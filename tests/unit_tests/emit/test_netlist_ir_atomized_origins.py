from asdl.core.atomized_graph import (
    AtomizedDeviceDef,
    AtomizedEndpoint,
    AtomizedInstance,
    AtomizedModuleGraph,
    AtomizedNet,
    AtomizedPatternOrigin,
    AtomizedProgramGraph,
)
from asdl.core.registries import RegistrySet
from asdl.emit.backend_config import BackendConfig, SystemDeviceTemplate
from asdl.emit.netlist import emit_netlist
from asdl.lowering import build_netlist_ir_design
from asdl.patterns.parser import parse_pattern_expr


def _backend_config(pattern_rendering: str = "{N}") -> BackendConfig:
    templates = {
        "__subckt_header__": SystemDeviceTemplate(template="{name}"),
        "__subckt_footer__": SystemDeviceTemplate(template=""),
        "__subckt_call__": SystemDeviceTemplate(template="{name} {ports} {ref}"),
        "__netlist_header__": SystemDeviceTemplate(template=""),
        "__netlist_footer__": SystemDeviceTemplate(template=""),
    }
    return BackendConfig(
        name="sim.ngspice",
        extension=".cir",
        comment_prefix="*",
        templates=templates,
        pattern_rendering=pattern_rendering,
    )


def test_emit_netlist_renders_numeric_pattern_atoms_from_atomized_origins() -> None:
    program = AtomizedProgramGraph()
    program.devices["d1"] = AtomizedDeviceDef(
        device_id="d1",
        name="cell",
        file_id="design.asdl",
        ports=["P"],
    )

    net_expr, net_errors = parse_pattern_expr("BUS<25:24>")
    pin_expr, pin_errors = parse_pattern_expr("pin<130:129>")
    sw_expr, sw_errors = parse_pattern_expr("sw_row<130:129>")
    assert net_errors == []
    assert pin_errors == []
    assert sw_errors == []
    assert net_expr is not None
    assert pin_expr is not None
    assert sw_expr is not None

    program.registries = RegistrySet(
        pattern_expressions={
            "expr_net": net_expr,
            "expr_pin": pin_expr,
            "expr_sw": sw_expr,
        },
        pattern_expr_kinds={
            "expr_net": "net",
            "expr_pin": "inst",
            "expr_sw": "inst",
        },
        device_backend_templates={
            "d1": {"sim.ngspice": "X{name} {ports}"},
        },
    )

    module = AtomizedModuleGraph(
        module_id="m1",
        name="top",
        file_id="design.asdl",
        ports=[],
    )
    module.instances = {
        "i1": AtomizedInstance(
            inst_id="i1",
            name="pin130",
            ref_kind="device",
            ref_id="d1",
            ref_raw="cell",
            pattern_origin=AtomizedPatternOrigin(
                expression_id="expr_pin",
                segment_index=0,
                atom_index=0,
                base_name="pin",
                pattern_parts=[130],
            ),
        ),
        "i2": AtomizedInstance(
            inst_id="i2",
            name="pin129",
            ref_kind="device",
            ref_id="d1",
            ref_raw="cell",
            pattern_origin=AtomizedPatternOrigin(
                expression_id="expr_pin",
                segment_index=0,
                atom_index=1,
                base_name="pin",
                pattern_parts=[129],
            ),
        ),
        "i3": AtomizedInstance(
            inst_id="i3",
            name="sw_row130",
            ref_kind="device",
            ref_id="d1",
            ref_raw="cell",
            pattern_origin=AtomizedPatternOrigin(
                expression_id="expr_sw",
                segment_index=0,
                atom_index=0,
                base_name="sw_row",
                pattern_parts=[130],
            ),
        ),
        "i4": AtomizedInstance(
            inst_id="i4",
            name="sw_row129",
            ref_kind="device",
            ref_id="d1",
            ref_raw="cell",
            pattern_origin=AtomizedPatternOrigin(
                expression_id="expr_sw",
                segment_index=0,
                atom_index=1,
                base_name="sw_row",
                pattern_parts=[129],
            ),
        ),
    }
    module.nets = {
        "n1": AtomizedNet(
            net_id="n1",
            name="BUS25",
            endpoint_ids=["e1", "e3"],
            pattern_origin=AtomizedPatternOrigin(
                expression_id="expr_net",
                segment_index=0,
                atom_index=0,
                base_name="BUS",
                pattern_parts=[25],
            ),
        ),
        "n2": AtomizedNet(
            net_id="n2",
            name="BUS24",
            endpoint_ids=["e2", "e4"],
            pattern_origin=AtomizedPatternOrigin(
                expression_id="expr_net",
                segment_index=0,
                atom_index=1,
                base_name="BUS",
                pattern_parts=[24],
            ),
        ),
    }
    module.endpoints = {
        "e1": AtomizedEndpoint(
            endpoint_id="e1", net_id="n1", inst_id="i1", port="P"
        ),
        "e2": AtomizedEndpoint(
            endpoint_id="e2", net_id="n2", inst_id="i2", port="P"
        ),
        "e3": AtomizedEndpoint(
            endpoint_id="e3", net_id="n1", inst_id="i3", port="P"
        ),
        "e4": AtomizedEndpoint(
            endpoint_id="e4", net_id="n2", inst_id="i4", port="P"
        ),
    }
    program.modules["m1"] = module

    design = build_netlist_ir_design(program)
    netlist, diagnostics = emit_netlist(
        design, backend_name="sim.ngspice", backend_config=_backend_config("[{N}]")
    )

    assert diagnostics == []
    assert netlist is not None
    for line in (
        "Xpin[130] BUS[25]",
        "Xpin[129] BUS[24]",
        "Xsw_row[130] BUS[25]",
        "Xsw_row[129] BUS[24]",
    ):
        assert line in netlist
