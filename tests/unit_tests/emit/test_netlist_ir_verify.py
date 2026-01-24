from __future__ import annotations

from asdl.emit.netlist_ir import (
    NetlistConn,
    NetlistDesign,
    NetlistInstance,
    NetlistModule,
    NetlistNet,
    PatternExpressionEntry,
    PatternOrigin,
)
from asdl.emit.verify_netlist_ir import (
    DUPLICATE_INSTANCE_NAME,
    DUPLICATE_NET_NAME,
    INVALID_LITERAL_NAME,
    INVALID_PATTERN_ORIGIN,
    INVALID_PORT_LIST,
    UNKNOWN_CONN_TARGET,
    verify_netlist_ir,
)


def _design(module: NetlistModule) -> NetlistDesign:
    return NetlistDesign(modules=[module])


def test_verify_netlist_ir_reports_invalid_literal_names() -> None:
    module = NetlistModule(
        name="top",
        file_id="design.asdl",
        nets=[NetlistNet(name="N<A>")],
    )

    diagnostics = verify_netlist_ir(_design(module))

    assert any(diag.code == INVALID_LITERAL_NAME for diag in diagnostics)


def test_verify_netlist_ir_reports_duplicate_net_names() -> None:
    module = NetlistModule(
        name="top",
        file_id="design.asdl",
        nets=[NetlistNet(name="N0"), NetlistNet(name="N0")],
    )

    diagnostics = verify_netlist_ir(_design(module))

    assert any(diag.code == DUPLICATE_NET_NAME for diag in diagnostics)


def test_verify_netlist_ir_reports_duplicate_instance_names() -> None:
    instance = NetlistInstance(
        name="U0",
        ref="cell",
        ref_file_id="design.asdl",
    )
    module = NetlistModule(
        name="top",
        file_id="design.asdl",
        instances=[instance, instance],
    )

    diagnostics = verify_netlist_ir(_design(module))

    assert any(diag.code == DUPLICATE_INSTANCE_NAME for diag in diagnostics)


def test_verify_netlist_ir_reports_unknown_conn_target() -> None:
    instance = NetlistInstance(
        name="U0",
        ref="cell",
        ref_file_id="design.asdl",
        conns=[NetlistConn(port="P", net="MISSING")],
    )
    module = NetlistModule(
        name="top",
        file_id="design.asdl",
        nets=[NetlistNet(name="N0")],
        instances=[instance],
    )

    diagnostics = verify_netlist_ir(_design(module))

    assert any(diag.code == UNKNOWN_CONN_TARGET for diag in diagnostics)


def test_verify_netlist_ir_reports_invalid_port_list() -> None:
    module = NetlistModule(
        name="top",
        file_id="design.asdl",
        ports=["N0", "MISSING"],
        nets=[NetlistNet(name="N0")],
    )

    diagnostics = verify_netlist_ir(_design(module))

    assert any(diag.code == INVALID_PORT_LIST for diag in diagnostics)


def test_verify_netlist_ir_reports_pattern_origin_table_mismatch() -> None:
    module = NetlistModule(
        name="top",
        file_id="design.asdl",
        nets=[
            NetlistNet(
                name="N0",
                pattern_origin=PatternOrigin(
                    expression_id="expr1",
                    segment_index=0,
                    base_name="N",
                    pattern_parts=["0"],
                ),
            )
        ],
        pattern_expression_table={
            "expr1": PatternExpressionEntry(expression="N<0>", kind="inst")
        },
    )

    diagnostics = verify_netlist_ir(_design(module))

    assert any(diag.code == INVALID_PATTERN_ORIGIN for diag in diagnostics)
