import pytest

pytest.importorskip("xdsl")

from xdsl.dialects.builtin import DictionaryAttr, StringAttr

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
    assert port_order == ["OUTP", "OUTN", "VSS"]

    nets = [op for op in ifir_module.body.block.ops if isinstance(op, NetOp)]
    assert [net.name_attr.data for net in nets] == ["OUTP", "OUTN", "VSS"]

    instances = [
        op for op in ifir_module.body.block.ops if isinstance(op, InstanceOp)
    ]
    assert [inst.name_attr.data for inst in instances] == ["M1", "M2"]

    conns = {
        inst.name_attr.data: [(conn.port.data, conn.net.data) for conn in inst.conns.data]
        for inst in instances
    }
    assert conns["M1"] == [("D", "OUTP"), ("S", "VSS")]
    assert conns["M2"] == [("D", "OUTN"), ("S", "VSS")]


def test_elaborate_patterns_expands_instance_params() -> None:
    instance = InstanceOp(
        name="M<1|2>",
        ref="nfet",
        conns=[ConnAttr(StringAttr("D"), StringAttr("OUT"))],
        params=DictionaryAttr(
            {
                "m": StringAttr("<1|2>"),
                "w": StringAttr("<4>"),
            }
        ),
    )
    module = ModuleOp(
        name="top",
        port_order=["OUT"],
        region=[NetOp(name="OUT"), instance],
    )
    design = DesignOp(region=[module], top="top")

    elaborated, diagnostics = run_pattern_elaboration(design)

    assert diagnostics == []
    assert elaborated is not None

    ifir_module = next(
        op for op in elaborated.body.block.ops if isinstance(op, ModuleOp)
    )
    instances = [
        op for op in ifir_module.body.block.ops if isinstance(op, InstanceOp)
    ]
    params = {
        inst.name_attr.data: {
            key: value.data for key, value in (inst.params.data if inst.params else {}).items()
        }
        for inst in instances
    }
    assert params["M1"] == {"m": "1", "w": "4"}
    assert params["M2"] == {"m": "2", "w": "4"}


def test_elaborate_patterns_rejects_mismatched_param_lengths() -> None:
    instance = InstanceOp(
        name="M<1|2>",
        ref="nfet",
        conns=[ConnAttr(StringAttr("D"), StringAttr("OUT"))],
        params=DictionaryAttr(
            {
                "m": StringAttr("<1|2|3>"),
            }
        ),
    )
    module = ModuleOp(
        name="top",
        port_order=["OUT"],
        region=[NetOp(name="OUT"), instance],
    )
    design = DesignOp(region=[module], top="top")

    elaborated, diagnostics = run_pattern_elaboration(design)

    assert elaborated is None
    assert any(
        "parameter 'm' expands to 3 values but instance expands to 2" in diag.message
        for diag in diagnostics
    )
