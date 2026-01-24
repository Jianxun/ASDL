import pytest

pytest.importorskip("xdsl")

from asdl.core.atomized_graph import (
    AtomizedDeviceDef,
    AtomizedEndpoint,
    AtomizedInstance,
    AtomizedModuleGraph,
    AtomizedNet,
    AtomizedProgramGraph,
)
from asdl.core.registries import RegistrySet
from asdl.diagnostics import format_code
from asdl.ir.ifir import BackendOp, DesignOp, DeviceOp, InstanceOp, ModuleOp, NetOp
from asdl.ir.patterns.origin import decode_pattern_origin
from asdl.lowering import build_ifir_design
from asdl.patterns_refactor.parser import parse_pattern_expr


def test_build_ifir_design_happy_path() -> None:
    program = AtomizedProgramGraph()
    program.devices["d1"] = AtomizedDeviceDef(
        device_id="d1",
        name="nfet",
        file_id="design.asdl",
        ports=["D", "G", "S"],
        parameters={"W": 1},
    )

    net_expr, net_errors = parse_pattern_expr("V<IN|OUT>")
    inst_expr, inst_errors = parse_pattern_expr("M<1:1>")
    assert net_errors == []
    assert inst_errors == []
    assert net_expr is not None
    assert inst_expr is not None
    program.registries = RegistrySet(
        pattern_expressions={
            "expr_net": net_expr,
            "expr_inst": inst_expr,
        },
        pattern_expr_kinds={
            "expr_net": "net",
            "expr_inst": "inst",
        },
        pattern_origins={
            "pn_vin": ("expr_net", 0, 0),
            "pn_vout": ("expr_net", 0, 1),
            "pi1": ("expr_inst", 0, 0),
        },
        device_backend_templates={
            "d1": {"sim.ngspice": "M {ports} {model}"},
        },
    )

    module = AtomizedModuleGraph(
        module_id="m1",
        name="top",
        file_id="design.asdl",
        ports=["VIN", "VOUT"],
    )
    module.instances = {
        "i1": AtomizedInstance(
            inst_id="i1",
            name="M1",
            ref_kind="device",
            ref_id="d1",
            ref_raw="nfet",
            param_values={"m": 2},
        )
    }
    module.nets = {
        "n1": AtomizedNet(
            net_id="n1",
            name="VIN",
            endpoint_ids=["e1"],
            patterned_net_id="pn_vin",
        ),
        "n2": AtomizedNet(
            net_id="n2",
            name="VOUT",
            endpoint_ids=["e2"],
            patterned_net_id="pn_vout",
        ),
        "n3": AtomizedNet(net_id="n3", name="VSS", endpoint_ids=["e3"]),
    }
    module.endpoints = {
        "e1": AtomizedEndpoint(
            endpoint_id="e1", net_id="n1", inst_id="i1", port="G"
        ),
        "e2": AtomizedEndpoint(
            endpoint_id="e2", net_id="n2", inst_id="i1", port="D"
        ),
        "e3": AtomizedEndpoint(
            endpoint_id="e3", net_id="n3", inst_id="i1", port="S"
        ),
    }
    module.instances["i1"].patterned_inst_id = "pi1"
    program.modules["m1"] = module

    design, diagnostics = build_ifir_design(program)

    assert diagnostics == []
    assert isinstance(design, DesignOp)
    assert design.top is not None
    assert design.top.data == "top"
    assert design.entry_file_id is not None
    assert design.entry_file_id.data == "design.asdl"

    ifir_module = next(
        op for op in design.body.block.ops if isinstance(op, ModuleOp)
    )
    assert ifir_module.sym_name.data == "top"
    assert [item.data for item in ifir_module.port_order.data] == ["VIN", "VOUT"]
    assert ifir_module.pattern_expression_table is not None
    assert "expr_net" in ifir_module.pattern_expression_table.data
    assert "expr_inst" in ifir_module.pattern_expression_table.data

    nets = [op for op in ifir_module.body.block.ops if isinstance(op, NetOp)]
    assert [net.name_attr.data for net in nets] == ["VIN", "VOUT", "VSS"]
    net_by_name = {net.name_attr.data: net for net in nets}
    vin_origin = decode_pattern_origin(net_by_name["VIN"].pattern_origin)
    assert vin_origin.expression_id == "expr_net"
    assert vin_origin.base_name == "V"
    assert vin_origin.pattern_parts == ["IN"]
    vout_origin = decode_pattern_origin(net_by_name["VOUT"].pattern_origin)
    assert vout_origin.expression_id == "expr_net"
    assert vout_origin.base_name == "V"
    assert vout_origin.pattern_parts == ["OUT"]

    inst = next(op for op in ifir_module.body.block.ops if isinstance(op, InstanceOp))
    conns = [(conn.port.data, conn.net.data) for conn in inst.conns.data]
    assert conns == [("G", "VIN"), ("D", "VOUT"), ("S", "VSS")]
    assert inst.params is not None
    assert inst.params.data["m"].data == "2"
    inst_origin = decode_pattern_origin(inst.pattern_origin)
    assert inst_origin.expression_id == "expr_inst"
    assert inst_origin.base_name == "M"
    assert inst_origin.pattern_parts == [1]

    ifir_device = next(
        op for op in design.body.block.ops if isinstance(op, DeviceOp)
    )
    assert ifir_device.sym_name.data == "nfet"
    assert [port.data for port in ifir_device.ports.data] == ["D", "G", "S"]
    assert ifir_device.params is not None
    assert ifir_device.params.data["W"].data == "1"
    backends = [
        op for op in ifir_device.body.block.ops if isinstance(op, BackendOp)
    ]
    assert len(backends) == 1
    assert backends[0].name_attr.data == "sim.ngspice"
    assert backends[0].template.data == "M {ports} {model}"


def test_pattern_origin_uses_segment_atom_index() -> None:
    program = AtomizedProgramGraph()
    net_expr, net_errors = parse_pattern_expr("X<1:1>;X<1>")
    assert net_errors == []
    assert net_expr is not None
    program.registries = RegistrySet(
        pattern_expressions={
            "expr_net": net_expr,
        },
        pattern_expr_kinds={
            "expr_net": "net",
        },
        pattern_origins={
            "pn0": ("expr_net", 0, 0),
            "pn1": ("expr_net", 1, 0),
        },
    )

    module = AtomizedModuleGraph(
        module_id="m1",
        name="top",
        file_id="design.asdl",
    )
    module.nets = {
        "n1": AtomizedNet(
            net_id="n1",
            name="X1",
            endpoint_ids=[],
            patterned_net_id="pn0",
        ),
        "n2": AtomizedNet(
            net_id="n2",
            name="X1",
            endpoint_ids=[],
            patterned_net_id="pn1",
        ),
    }
    program.modules["m1"] = module

    design, diagnostics = build_ifir_design(program)

    assert diagnostics == []
    assert isinstance(design, DesignOp)
    ifir_module = next(
        op for op in design.body.block.ops if isinstance(op, ModuleOp)
    )
    nets = [op for op in ifir_module.body.block.ops if isinstance(op, NetOp)]
    assert [net.name_attr.data for net in nets] == ["X1", "X1"]

    first_origin = decode_pattern_origin(nets[0].pattern_origin)
    assert first_origin.segment_index == 0
    assert first_origin.base_name == "X"
    assert first_origin.pattern_parts == [1]

    second_origin = decode_pattern_origin(nets[1].pattern_origin)
    assert second_origin.segment_index == 1
    assert second_origin.base_name == "X"
    assert second_origin.pattern_parts == ["1"]


def test_build_ifir_design_missing_endpoint_sets_error() -> None:
    program = AtomizedProgramGraph()
    program.devices["d1"] = AtomizedDeviceDef(
        device_id="d1",
        name="nfet",
        file_id="design.asdl",
        ports=["D", "G", "S"],
    )

    module = AtomizedModuleGraph(
        module_id="m1",
        name="top",
        file_id="design.asdl",
    )
    module.instances = {
        "i1": AtomizedInstance(
            inst_id="i1",
            name="M1",
            ref_kind="device",
            ref_id="d1",
            ref_raw="nfet",
        )
    }
    module.nets = {
        "n1": AtomizedNet(net_id="n1", name="VIN", endpoint_ids=["e-missing"])
    }
    module.endpoints = {}
    program.modules["m1"] = module

    design, diagnostics = build_ifir_design(program)

    assert design is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == format_code("IR", 41)
    assert "missing endpoint" in diagnostics[0].message
