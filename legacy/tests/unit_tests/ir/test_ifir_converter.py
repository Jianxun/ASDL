import pytest

from xdsl.dialects.builtin import DictionaryAttr, StringAttr

pytest.importorskip("xdsl")

from asdl.ir import convert_graphir_to_ifir
from asdl.ir.graphir import DeviceOp as GraphDeviceOp
from asdl.ir.graphir import EndpointOp as GraphEndpointOp
from asdl.ir.graphir import InstanceOp as GraphInstanceOp
from asdl.ir.graphir import ModuleOp as GraphModuleOp
from asdl.ir.graphir import NetOp as GraphNetOp
from asdl.ir.graphir import ProgramOp as GraphProgramOp
from asdl.ir.ifir import BackendOp as IfirBackendOp
from asdl.ir.ifir import DesignOp as IfirDesignOp
from asdl.ir.ifir import DeviceOp as IfirDeviceOp
from asdl.ir.ifir import InstanceOp as IfirInstanceOp
from asdl.ir.ifir import ModuleOp as IfirModuleOp
from asdl.ir.ifir import NetOp as IfirNetOp
from asdl.ir.patterns import encode_pattern_expression_table, register_pattern_expression


def test_convert_graphir_program_to_ifir() -> None:
    instance = GraphInstanceOp(
        inst_id="i1",
        name="M1",
        module_ref=("device", "d1"),
        module_ref_raw="nfet",
    )
    net_vin = GraphNetOp(
        net_id="n1",
        name="VIN",
        region=[GraphEndpointOp(endpoint_id="e1", inst_id="i1", port_path="G")],
    )
    net_vss = GraphNetOp(
        net_id="n2",
        name="VSS",
        region=[GraphEndpointOp(endpoint_id="e2", inst_id="i1", port_path="S")],
    )
    module = GraphModuleOp(
        module_id="m1",
        name="top",
        file_id="entry.asdl",
        port_order=["VIN"],
        region=[net_vin, net_vss, instance],
    )
    device = GraphDeviceOp(
        device_id="d1",
        name="nfet",
        file_id="entry.asdl",
        ports=["D", "G", "S"],
        region=[IfirBackendOp(name="ngspice", template="M{inst} {D} {G} {S} {model}")],
    )
    program = GraphProgramOp(region=[module, device], entry="m1")

    ifir_design, diagnostics = convert_graphir_to_ifir(program)
    assert diagnostics == []
    assert isinstance(ifir_design, IfirDesignOp)
    assert ifir_design.top is not None
    assert ifir_design.top.data == "top"

    ifir_module = next(
        op for op in ifir_design.body.block.ops if isinstance(op, IfirModuleOp)
    )
    assert [item.data for item in ifir_module.port_order.data] == ["VIN"]
    nets = [op for op in ifir_module.body.block.ops if isinstance(op, IfirNetOp)]
    assert [net.name_attr.data for net in nets] == ["VIN", "VSS"]

    inst = next(
        op for op in ifir_module.body.block.ops if isinstance(op, IfirInstanceOp)
    )
    conns = [(conn.port.data, conn.net.data) for conn in inst.conns.data]
    assert conns == [("G", "VIN"), ("S", "VSS")]

    ifir_device = next(
        op for op in ifir_design.body.block.ops if isinstance(op, IfirDeviceOp)
    )
    backend = next(op for op in ifir_device.body.block.ops if isinstance(op, IfirBackendOp))
    assert ifir_device.sym_name.data == "nfet"
    assert backend.template.data == "M{inst} {D} {G} {S} {model}"


def test_convert_graphir_propagates_file_ids() -> None:
    instance = GraphInstanceOp(
        inst_id="i1",
        name="M1",
        module_ref=("device", "d1"),
        module_ref_raw="nfet",
    )
    module = GraphModuleOp(
        module_id="m1",
        name="top",
        file_id="entry.asdl",
        port_order=[],
        region=[
            GraphNetOp(net_id="n1", name="VIN", region=[]),
            instance,
        ],
    )
    device = GraphDeviceOp(
        device_id="d1",
        name="nfet",
        file_id="dep.asdl",
        ports=[],
        region=[],
    )
    program = GraphProgramOp(region=[module, device], entry="m1")

    ifir_design, diagnostics = convert_graphir_to_ifir(program)
    assert diagnostics == []
    assert ifir_design is not None
    assert ifir_design.entry_file_id is not None
    assert ifir_design.entry_file_id.data == "entry.asdl"

    ifir_module = next(
        op for op in ifir_design.body.block.ops if isinstance(op, IfirModuleOp)
    )
    assert ifir_module.file_id is not None
    assert ifir_module.file_id.data == "entry.asdl"

    ifir_device = next(
        op for op in ifir_design.body.block.ops if isinstance(op, IfirDeviceOp)
    )
    assert ifir_device.file_id is not None
    assert ifir_device.file_id.data == "dep.asdl"

    inst = next(
        op for op in ifir_module.body.block.ops if isinstance(op, IfirInstanceOp)
    )
    assert inst.ref_file_id is not None
    assert inst.ref_file_id.data == "dep.asdl"


def test_convert_graphir_pattern_origin_uses_expression_table() -> None:
    table = {}
    net_expr_id = register_pattern_expression(
        table,
        expression="OUT<P|N>",
        kind="net",
    )
    inst_expr_id = register_pattern_expression(
        table,
        expression="U<P|N>",
        kind="inst",
    )
    pattern_table_attr = encode_pattern_expression_table(table)

    instance_p = GraphInstanceOp(
        inst_id="i1",
        name="UP",
        module_ref=("device", "d1"),
        module_ref_raw="res",
        pattern_origin=(inst_expr_id, 0, "U", ["P"]),
    )
    instance_n = GraphInstanceOp(
        inst_id="i2",
        name="UN",
        module_ref=("device", "d1"),
        module_ref_raw="res",
        pattern_origin=(inst_expr_id, 0, "U", ["N"]),
    )
    net_out_p = GraphNetOp(
        net_id="n1",
        name="OUTP",
        pattern_origin=(net_expr_id, 0, "OUT", ["P"]),
        region=[
            GraphEndpointOp(endpoint_id="e1", inst_id="i1", port_path="P"),
        ],
    )
    net_out_n = GraphNetOp(
        net_id="n2",
        name="OUTN",
        pattern_origin=(net_expr_id, 0, "OUT", ["N"]),
        region=[
            GraphEndpointOp(endpoint_id="e2", inst_id="i2", port_path="P"),
        ],
    )
    module = GraphModuleOp(
        module_id="m1",
        name="top",
        file_id="entry.asdl",
        port_order=["OUTP", "OUTN"],
        pattern_expression_table=pattern_table_attr,
        region=[net_out_p, net_out_n, instance_p, instance_n],
    )
    device = GraphDeviceOp(
        device_id="d1",
        name="res",
        file_id="entry.asdl",
        ports=["P"],
        region=[],
    )
    program = GraphProgramOp(region=[module, device], entry="m1")

    ifir_design, diagnostics = convert_graphir_to_ifir(program)

    assert diagnostics == []
    assert ifir_design is not None

    ifir_module = next(
        op for op in ifir_design.body.block.ops if isinstance(op, IfirModuleOp)
    )
    nets = [op for op in ifir_module.body.block.ops if isinstance(op, IfirNetOp)]
    instances = [
        op for op in ifir_module.body.block.ops if isinstance(op, IfirInstanceOp)
    ]

    assert ifir_module.pattern_expression_table is not None
    assert ifir_module.pattern_expression_table.data == pattern_table_attr.data

    net_origins = {
        net.name_attr.data: net.pattern_origin
        for net in nets
        if net.pattern_origin is not None
    }
    inst_origins = {
        inst.name_attr.data: inst.pattern_origin
        for inst in instances
        if inst.pattern_origin is not None
    }

    assert {origin.expression_id.data for origin in net_origins.values()} == {net_expr_id}
    assert {origin.expression_id.data for origin in inst_origins.values()} == {inst_expr_id}
    assert [part.data for part in net_origins["OUTP"].pattern_parts.data] == ["P"]
    assert [part.data for part in net_origins["OUTN"].pattern_parts.data] == ["N"]
    assert [part.data for part in inst_origins["UP"].pattern_parts.data] == ["P"]
    assert [part.data for part in inst_origins["UN"].pattern_parts.data] == ["N"]


def test_convert_graphir_device_variables_to_ifir() -> None:
    device_variables = DictionaryAttr({"FLAG": StringAttr("true")})
    backend_variables = DictionaryAttr({"MODE": StringAttr("fast")})

    device = GraphDeviceOp(
        device_id="d1",
        name="nfet",
        file_id="entry.asdl",
        ports=["D", "G", "S"],
        variables=device_variables,
        region=[
            IfirBackendOp(
                name="ngspice",
                template="M{inst} {D} {G} {S} {model}",
                variables=backend_variables,
            )
        ],
    )
    program = GraphProgramOp(region=[device], entry=None)

    ifir_design, diagnostics = convert_graphir_to_ifir(program)

    assert diagnostics == []
    assert isinstance(ifir_design, IfirDesignOp)

    ifir_device = next(
        op for op in ifir_design.body.block.ops if isinstance(op, IfirDeviceOp)
    )
    assert ifir_device.variables is not None
    assert ifir_device.variables.data["FLAG"].data == "true"

    backend = next(
        op for op in ifir_device.body.block.ops if isinstance(op, IfirBackendOp)
    )
    assert backend.variables is not None
    assert backend.variables.data["MODE"].data == "fast"
