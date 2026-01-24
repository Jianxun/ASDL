from asdl.core.atomized_graph import (
    AtomizedDeviceDef,
    AtomizedEndpoint,
    AtomizedInstance,
    AtomizedModuleGraph,
    AtomizedNet,
    AtomizedProgramGraph,
)
from asdl.core.registries import RegistrySet
from asdl.emit.netlist_ir import NetlistDesign
from asdl.lowering import build_netlist_ir_design
from asdl.patterns_refactor.parser import parse_pattern_expr


def test_build_netlist_ir_design_happy_path() -> None:
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

    design = build_netlist_ir_design(program)

    assert isinstance(design, NetlistDesign)
    assert design.top == "top"
    assert design.entry_file_id == "design.asdl"

    netlist_module = design.modules[0]
    assert netlist_module.name == "top"
    assert netlist_module.ports == ["VIN", "VOUT"]
    assert [net.name for net in netlist_module.nets] == ["VIN", "VOUT", "VSS"]
    assert netlist_module.pattern_expression_table is not None
    assert netlist_module.pattern_expression_table["expr_net"].expression == "V<IN|OUT>"
    assert netlist_module.pattern_expression_table["expr_inst"].kind == "inst"

    vin_origin = netlist_module.nets[0].pattern_origin
    assert vin_origin is not None
    assert vin_origin.expression_id == "expr_net"
    assert vin_origin.segment_index == 0
    assert vin_origin.base_name == "V"
    assert vin_origin.pattern_parts == ["IN"]

    vout_origin = netlist_module.nets[1].pattern_origin
    assert vout_origin is not None
    assert vout_origin.expression_id == "expr_net"
    assert vout_origin.pattern_parts == ["OUT"]

    inst = netlist_module.instances[0]
    assert inst.name == "M1"
    assert inst.ref == "nfet"
    assert inst.ref_file_id == "design.asdl"
    assert inst.params == {"m": "2"}
    assert [(conn.port, conn.net) for conn in inst.conns] == [
        ("G", "VIN"),
        ("D", "VOUT"),
        ("S", "VSS"),
    ]

    inst_origin = inst.pattern_origin
    assert inst_origin is not None
    assert inst_origin.expression_id == "expr_inst"
    assert inst_origin.base_name == "M"
    assert inst_origin.pattern_parts == [1]

    device = design.devices[0]
    assert device.name == "nfet"
    assert device.ports == ["D", "G", "S"]
    assert device.params == {"W": "1"}
    assert device.backends[0].name == "sim.ngspice"
    assert device.backends[0].template == "M {ports} {model}"
