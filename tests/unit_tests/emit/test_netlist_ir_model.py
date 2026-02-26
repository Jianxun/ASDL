from asdl.emit.netlist_ir import (
    NetlistBackend,
    NetlistConn,
    NetlistDesign,
    NetlistDevice,
    NetlistInstance,
    NetlistModule,
    NetlistNet,
    PatternExpressionEntry,
    PatternOrigin,
)


def test_netlist_ir_construction_preserves_ordering() -> None:
    """Test NetlistIR construction preserves list ordering and metadata."""
    pattern_table = {
        "expr1": PatternExpressionEntry(expression="N<A,B>", kind="net"),
        "expr2": PatternExpressionEntry(expression="X<1:2>", kind="inst"),
    }

    net_a = NetlistNet(
        name="N_A",
        pattern_origin=PatternOrigin(
            expression_id="expr1",
            segment_index=0,
            base_name="N",
            pattern_parts=["_A"],
        ),
    )
    net_b = NetlistNet(name="N_B")

    conn_a = NetlistConn(port="in", net="N_A")
    conn_b = NetlistConn(port="out", net="N_B")

    inst = NetlistInstance(
        name="X1",
        ref="my_cell",
        ref_file_id="design.asdl",
        params={"gain": "2"},
        conns=[conn_a, conn_b],
        pattern_origin=PatternOrigin(
            expression_id="expr2",
            segment_index=0,
            base_name="X",
            pattern_parts=[1],
        ),
    )

    backend = NetlistBackend(
        name="sim.ngspice",
        template="X{name} {ports} {ref}",
        params={"m": "1"},
        variables=None,
        props={"comment": "test"},
    )

    device = NetlistDevice(
        name="my_cell",
        file_id="design.asdl",
        ports=["in", "out"],
        params=None,
        variables=None,
        backends=[backend],
    )

    module = NetlistModule(
        name="top",
        file_id="design.asdl",
        ports=["in", "out"],
        parameters={"mode": "ac", "m": "2"},
        nets=[net_a, net_b],
        instances=[inst],
        pattern_expression_table=pattern_table,
    )

    design = NetlistDesign(
        modules=[module],
        devices=[device],
        top="top",
        entry_file_id="design.asdl",
    )

    assert design.modules[0].ports == ["in", "out"]
    assert [net.name for net in design.modules[0].nets] == ["N_A", "N_B"]
    assert [inst.name for inst in design.modules[0].instances] == ["X1"]
    assert [conn.port for conn in design.modules[0].instances[0].conns] == [
        "in",
        "out",
    ]
    assert design.modules[0].parameters == {"mode": "ac", "m": "2"}
    assert [backend.name for backend in design.devices[0].backends] == [
        "sim.ngspice"
    ]
    assert design.modules[0].pattern_expression_table["expr1"].expression == "N<A,B>"
