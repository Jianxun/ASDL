import pytest

pytest.importorskip("xdsl")

from xdsl.dialects.builtin import StringAttr

from asdl.ir.ifir import ConnAttr, DesignOp, InstanceOp, ModuleOp, NetOp
from asdl.ir.pattern_atomization import run_pattern_atomization


def test_atomize_patterns_base_less_forwarding() -> None:
    instance_base = InstanceOp(
        name="U",
        ref="amp",
        conns=[
            ConnAttr(StringAttr("<P|N>"), StringAttr("<INP|INN>")),
            ConnAttr(StringAttr("D"), StringAttr("OUT")),
        ],
    )
    instance_pattern = InstanceOp(
        name="<P|N>",
        ref="sw",
        conns=[ConnAttr(StringAttr("D"), StringAttr("OUT"))],
    )
    module = ModuleOp(
        name="top",
        port_order=["<INP|INN>", "OUT"],
        region=[
            NetOp(name="<INP|INN>"),
            NetOp(name="OUT"),
            instance_base,
            instance_pattern,
        ],
    )
    design = DesignOp(region=[module], top="top")

    atomized, diagnostics = run_pattern_atomization(design)

    assert diagnostics == []
    assert atomized is not None

    ifir_module = next(
        op for op in atomized.body.block.ops if isinstance(op, ModuleOp)
    )
    port_order = [attr.data for attr in ifir_module.port_order.data]
    assert port_order == ["<INP>", "<INN>", "OUT"]

    nets = [op for op in ifir_module.body.block.ops if isinstance(op, NetOp)]
    assert [net.name_attr.data for net in nets] == ["<INP>", "<INN>", "OUT"]
    origins = {net.name_attr.data: net.pattern_origin.data for net in nets if net.pattern_origin}
    assert origins == {"<INP>": "<INP|INN>", "<INN>": "<INP|INN>"}

    instances = [
        op for op in ifir_module.body.block.ops if isinstance(op, InstanceOp)
    ]
    assert [inst.name_attr.data for inst in instances] == ["U", "<P>", "<N>"]
    inst_origins = {
        inst.name_attr.data: inst.pattern_origin.data
        for inst in instances
        if inst.pattern_origin
    }
    assert inst_origins == {"<P>": "<P|N>", "<N>": "<P|N>"}

    conns = {
        inst.name_attr.data: [(conn.port.data, conn.net.data) for conn in inst.conns.data]
        for inst in instances
    }
    assert conns["U"] == [("<P>", "<INP>"), ("<N>", "<INN>"), ("D", "OUT")]
    assert conns["<P>"] == [("D", "OUT")]
    assert conns["<N>"] == [("D", "OUT")]


def test_atomize_patterns_reports_literal_collisions() -> None:
    module = ModuleOp(
        name="top",
        port_order=["OUT<P>", "OUTP"],
        region=[
            NetOp(name="OUT<P>"),
            NetOp(name="OUTP"),
            InstanceOp(
                name="M<1>",
                ref="nfet",
                conns=[ConnAttr(StringAttr("D"), StringAttr("OUT<P>"))],
            ),
            InstanceOp(
                name="M1",
                ref="nfet",
                conns=[ConnAttr(StringAttr("D"), StringAttr("OUTP"))],
            ),
        ],
    )
    design = DesignOp(region=[module], top="top")

    atomized, diagnostics = run_pattern_atomization(design)

    assert atomized is None
    assert any("Net literal name collision" in diag.message for diag in diagnostics)
    assert any("Instance literal name collision" in diag.message for diag in diagnostics)
