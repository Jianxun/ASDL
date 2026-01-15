from pathlib import Path

import pytest

pytest.importorskip("xdsl")

from asdl.ast import AsdlDocument, DeviceBackendDecl, DeviceDecl, ModuleDecl, parse_file
from asdl.diagnostics import Severity
from asdl.ir.converters.ast_to_graphir import convert_document
from asdl.ir.graphir import DeviceOp, EndpointOp, InstanceOp, ModuleOp, NetOp, ProgramOp
from asdl.ir.patterns import PATTERN_DUPLICATE_ATOM, decode_pattern_expression_table


def test_convert_document_single_file_fixture() -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "graphir_single_file.asdl"
    document, parse_diags = parse_file(str(fixture_path))

    assert parse_diags == []
    assert document is not None

    program, diagnostics = convert_document(document)

    assert diagnostics == []
    assert isinstance(program, ProgramOp)

    modules = [op for op in program.body.block.ops if isinstance(op, ModuleOp)]
    devices = [op for op in program.body.block.ops if isinstance(op, DeviceOp)]
    assert len(modules) == 2
    assert len(devices) == 1

    module = next(op for op in modules if op.name_attr.data == "top")
    child = next(op for op in modules if op.name_attr.data == "child")
    device = devices[0]

    assert module.file_id.data == str(fixture_path)
    assert child.file_id.data == str(fixture_path)
    assert program.entry is not None
    assert program.entry.value.data == module.module_id.value.data
    assert module.port_order == ["VIN"]

    nets = [op for op in module.body.block.ops if isinstance(op, NetOp)]
    instances = [op for op in module.body.block.ops if isinstance(op, InstanceOp)]
    assert {net.name_attr.data for net in nets} == {"VIN", "VSS"}

    m1 = next(inst for inst in instances if inst.name_attr.data == "M1")
    u1 = next(inst for inst in instances if inst.name_attr.data == "U1")

    assert m1.props is not None
    assert m1.props.data["w"].data == "1u"
    assert m1.module_ref.kind.data == "device"
    assert m1.module_ref.sym_id.value.data == device.device_id.value.data
    assert u1.module_ref.kind.data == "module"
    assert u1.module_ref.sym_id.value.data == child.module_id.value.data

    vin_net = next(net for net in nets if net.name_attr.data == "VIN")
    endpoints = [op for op in vin_net.body.block.ops if isinstance(op, EndpointOp)]
    endpoint_pairs = {(ep.inst_id.value.data, ep.port_path.data) for ep in endpoints}
    assert (m1.inst_id.value.data, "G") in endpoint_pairs
    assert (u1.inst_id.value.data, "IN") in endpoint_pairs


def test_convert_document_unresolved_reference_emits_error() -> None:
    document = AsdlDocument(
        top="top",
        modules={
            "top": ModuleDecl(
                instances={"U1": "missing"},
                nets={"OUT": ["U1.P"]},
            )
        },
        devices={
            "res": DeviceDecl(
                backends={"ngspice": DeviceBackendDecl(template="R{inst} {ports}")}
            )
        },
    )

    program, diagnostics = convert_document(document)

    assert program is None
    assert any(
        diag.code == "IR-011" and diag.severity is Severity.ERROR
        for diag in diagnostics
    )


def test_convert_document_invalid_instance_expr_emits_error() -> None:
    document = AsdlDocument(
        modules={
            "top": ModuleDecl(
                instances={"M1": "res bad"},
                nets={"OUT": ["M1.P"]},
            )
        },
        devices={
            "res": DeviceDecl(
                backends={"ngspice": DeviceBackendDecl(template="R{inst} {ports}")}
            )
        },
    )

    program, diagnostics = convert_document(document)

    assert program is None
    assert any(
        diag.code == "IR-001" and diag.severity is Severity.ERROR
        for diag in diagnostics
    )


def test_convert_document_invalid_endpoint_expr_emits_error() -> None:
    module = ModuleDecl.model_construct(
        instances={"M1": "res"},
        nets={"OUT": "M1.P"},
    )
    module._instances_loc = {}
    module._nets_loc = {}
    document = AsdlDocument.model_construct(
        modules={"top": module},
        devices={
            "res": DeviceDecl(
                backends={"ngspice": DeviceBackendDecl(template="R{inst} {ports}")}
            )
        },
    )

    program, diagnostics = convert_document(document)

    assert program is None
    assert any(
        diag.code == "IR-002" and diag.severity is Severity.ERROR
        for diag in diagnostics
    )


def test_convert_document_expands_patterns_with_param_origins() -> None:
    document = AsdlDocument(
        modules={
            "top": ModuleDecl(
                instances={"U<P|N>": "res r=R<P|N>"},
                nets={"OUT<P|N>": ["U<P|N>.P"]},
            )
        },
        devices={
            "res": DeviceDecl(
                backends={"ngspice": DeviceBackendDecl(template="R{inst} {ports}")}
            )
        },
    )

    program, diagnostics = convert_document(document)

    assert diagnostics == []
    assert isinstance(program, ProgramOp)

    module = next(op for op in program.body.block.ops if isinstance(op, ModuleOp))
    table_attr = module.attrs.data.get("pattern_expression_table")
    table = decode_pattern_expression_table(table_attr)
    expr_kinds = {(entry.expression, entry.kind) for entry in table.values()}
    assert ("OUT<P|N>", "net") in expr_kinds
    assert ("U<P|N>", "inst") in expr_kinds
    assert ("U<P|N>.P", "endpoint") in expr_kinds
    assert ("R<P|N>", "param") in expr_kinds

    nets = {
        net.name_attr.data: net
        for net in module.body.block.ops
        if isinstance(net, NetOp)
    }
    instances = {
        inst.name_attr.data: inst
        for inst in module.body.block.ops
        if isinstance(inst, InstanceOp)
    }
    assert set(nets.keys()) == {"OUTP", "OUTN"}
    assert set(instances.keys()) == {"UP", "UN"}

    outp_endpoint = next(
        op for op in nets["OUTP"].body.block.ops if isinstance(op, EndpointOp)
    )
    outn_endpoint = next(
        op for op in nets["OUTN"].body.block.ops if isinstance(op, EndpointOp)
    )
    assert outp_endpoint.inst_id.value.data == instances["UP"].inst_id.value.data
    assert outn_endpoint.inst_id.value.data == instances["UN"].inst_id.value.data
    assert outp_endpoint.pattern_origin is not None
    assert outn_endpoint.pattern_origin is not None

    expr_ids = {entry.expression: expr_id for expr_id, entry in table.items()}
    up = instances["UP"]
    un = instances["UN"]
    assert up.props is not None
    assert un.props is not None
    assert up.props.data["r"].data == "RP"
    assert un.props.data["r"].data == "RN"
    assert up.param_pattern_origin is not None
    assert un.param_pattern_origin is not None
    assert (
        up.param_pattern_origin.data["r"].expression_id.data
        == expr_ids["R<P|N>"]
    )
    assert (
        un.param_pattern_origin.data["r"].expression_id.data
        == expr_ids["R<P|N>"]
    )


def test_convert_document_allows_subset_endpoint_bindings() -> None:
    document = AsdlDocument(
        modules={
            "top": ModuleDecl(
                instances={"MN_IN_<1|2|3>": "nfet"},
                nets={"OUT<1|2>": ["MN_IN_<1|2>.D"]},
            )
        },
        devices={
            "nfet": DeviceDecl(
                ports=["D"],
                backends={"ngspice": DeviceBackendDecl(template="M{inst} {ports}")},
            )
        },
    )

    program, diagnostics = convert_document(document)

    assert diagnostics == []
    assert isinstance(program, ProgramOp)
    module = next(op for op in program.body.block.ops if isinstance(op, ModuleOp))
    nets = {
        net.name_attr.data: net
        for net in module.body.block.ops
        if isinstance(net, NetOp)
    }
    instances = {
        inst.name_attr.data: inst
        for inst in module.body.block.ops
        if isinstance(inst, InstanceOp)
    }

    out1_endpoint = next(
        op for op in nets["OUT1"].body.block.ops if isinstance(op, EndpointOp)
    )
    out2_endpoint = next(
        op for op in nets["OUT2"].body.block.ops if isinstance(op, EndpointOp)
    )
    assert out1_endpoint.inst_id.value.data == instances["MN_IN_1"].inst_id.value.data
    assert out2_endpoint.inst_id.value.data == instances["MN_IN_2"].inst_id.value.data


def test_convert_document_reports_pattern_length_mismatch() -> None:
    document = AsdlDocument(
        modules={
            "top": ModuleDecl(
                instances={"M<1|2>": "nfet"},
                nets={"OUT<1|2>": ["M<1|2|3>.D"]},
            )
        },
        devices={
            "nfet": DeviceDecl(
                ports=["D"],
                backends={"ngspice": DeviceBackendDecl(template="M{inst} {ports}")},
            )
        },
    )

    program, diagnostics = convert_document(document)

    assert program is None
    assert any(diag.code == "IR-003" for diag in diagnostics)


def test_convert_document_reports_pattern_collisions() -> None:
    document = AsdlDocument(
        modules={
            "top": ModuleDecl(instances={"M<P|P>": "nfet"}, nets={})
        },
        devices={
            "nfet": DeviceDecl(
                ports=["D"],
                backends={"ngspice": DeviceBackendDecl(template="M{inst} {ports}")},
            )
        },
    )

    program, diagnostics = convert_document(document)

    assert program is None
    assert any(diag.code == PATTERN_DUPLICATE_ATOM for diag in diagnostics)
