import pytest

pytest.importorskip("xdsl")

from xdsl.dialects.builtin import StringAttr

from asdl.ir.ifir import ConnAttr, DesignOp, InstanceOp, ModuleOp, NetOp
from asdl.ir.pattern_elaboration import run_pattern_elaboration


def test_elaborate_patterns_expands_names_and_conns() -> None:
    instance = InstanceOp(
        name="M<1|2>",
        ref="nfet",
        conns=[
            ConnAttr(StringAttr("D"), StringAttr("OUT<P|N>")),
            ConnAttr(StringAttr("S"), StringAttr("VSS")),
        ],
    )
    module = ModuleOp(
        name="top",
        port_order=["OUT<P|N>", "VSS"],
        region=[
            NetOp(name="OUT<P|N>"),
            NetOp(name="VSS"),
            instance,
        ],
    )
    design = DesignOp(region=[module], top="top")

    elaborated, diagnostics = run_pattern_elaboration(design)

    assert diagnostics == []
    assert elaborated is not None

    ifir_module = next(
        op for op in elaborated.body.block.ops if isinstance(op, ModuleOp)
    )
    port_order = [attr.data for attr in ifir_module.port_order.data]
    assert port_order == ["OUT_P", "OUT_N", "VSS"]

    nets = [op for op in ifir_module.body.block.ops if isinstance(op, NetOp)]
    assert [net.name_attr.data for net in nets] == ["OUT_P", "OUT_N", "VSS"]

    instances = [
        op for op in ifir_module.body.block.ops if isinstance(op, InstanceOp)
    ]
    assert [inst.name_attr.data for inst in instances] == ["M_1", "M_2"]

    conns = {
        inst.name_attr.data: [(conn.port.data, conn.net.data) for conn in inst.conns.data]
        for inst in instances
    }
    assert conns["M_1"] == [("D", "OUT_P"), ("S", "VSS")]
    assert conns["M_2"] == [("D", "OUT_N"), ("S", "VSS")]
