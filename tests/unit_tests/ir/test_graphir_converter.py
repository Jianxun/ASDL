from pathlib import Path

import pytest

pytest.importorskip("xdsl")

from asdl.ast import AsdlDocument, DeviceBackendDecl, DeviceDecl, ModuleDecl, parse_file
from asdl.diagnostics import Severity
from asdl.ir.converters.ast_to_graphir import convert_document
from asdl.ir.graphir import DeviceOp, EndpointOp, InstanceOp, ModuleOp, NetOp, ProgramOp


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
