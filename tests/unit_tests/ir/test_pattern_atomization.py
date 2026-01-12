import pytest

pytest.importorskip("xdsl")

from xdsl.dialects.builtin import DictionaryAttr, StringAttr

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
    assert port_order == ["INP", "INN", "OUT"]

    nets = [op for op in ifir_module.body.block.ops if isinstance(op, NetOp)]
    assert [net.name_attr.data for net in nets] == ["INP", "INN", "OUT"]
    origins = {net.name_attr.data: net.pattern_origin.data for net in nets if net.pattern_origin}
    assert origins == {"INP": "<INP|INN>", "INN": "<INP|INN>"}

    instances = [
        op for op in ifir_module.body.block.ops if isinstance(op, InstanceOp)
    ]
    assert [inst.name_attr.data for inst in instances] == ["U", "P", "N"]
    inst_origins = {
        inst.name_attr.data: inst.pattern_origin.data
        for inst in instances
        if inst.pattern_origin
    }
    assert inst_origins == {"P": "<P|N>", "N": "<P|N>"}

    conns = {
        inst.name_attr.data: [(conn.port.data, conn.net.data) for conn in inst.conns.data]
        for inst in instances
    }
    assert conns["U"] == [("P", "INP"), ("N", "INN"), ("D", "OUT")]
    assert conns["P"] == [("D", "OUT")]
    assert conns["N"] == [("D", "OUT")]


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


def test_atomize_patterns_allows_subset_endpoint_bindings() -> None:
    module = ModuleOp(
        name="top",
        port_order=["OUT"],
        region=[
            NetOp(name="OUT"),
            InstanceOp(
                name="<P>",
                ref="sw",
                conns=[ConnAttr(StringAttr("D"), StringAttr("OUT"))],
            ),
            InstanceOp(
                name="<N>",
                ref="sw",
                conns=[],
            ),
        ],
    )
    design = DesignOp(region=[module], top="top")

    atomized, diagnostics = run_pattern_atomization(design)

    assert diagnostics == []
    assert atomized is not None

    ifir_module = next(
        op for op in atomized.body.block.ops if isinstance(op, ModuleOp)
    )
    instances = [
        op for op in ifir_module.body.block.ops if isinstance(op, InstanceOp)
    ]
    conns = {
        inst.name_attr.data: [(conn.port.data, conn.net.data) for conn in inst.conns.data]
        for inst in instances
    }
    assert conns["P"] == [("D", "OUT")]
    assert conns["N"] == []
    origins = {
        inst.name_attr.data: inst.pattern_origin.data
        for inst in instances
        if inst.pattern_origin
    }
    assert origins == {"P": "<P>", "N": "<N>"}


def test_atomize_patterns_expands_instance_params() -> None:
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

    atomized, diagnostics = run_pattern_atomization(design)

    assert diagnostics == []
    assert atomized is not None

    ifir_module = next(
        op for op in atomized.body.block.ops if isinstance(op, ModuleOp)
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
    assert params["M1"] == {"m": "<1>", "w": "<4>"}
    assert params["M2"] == {"m": "<2>", "w": "<4>"}
    origins = {
        inst.name_attr.data: inst.pattern_origin.data
        for inst in instances
        if inst.pattern_origin
    }
    assert origins == {"M1": "M<1|2>", "M2": "M<1|2>"}


def test_atomize_patterns_rejects_mismatched_param_lengths() -> None:
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

    atomized, diagnostics = run_pattern_atomization(design)

    assert atomized is None
    assert any(
        "parameter 'm' atomizes to 3 values but instance atomizes to 2" in diag.message
        for diag in diagnostics
    )


def test_atomize_patterns_is_idempotent() -> None:
    module = ModuleOp(
        name="top",
        port_order=["OUT<P|N>"],
        region=[
            NetOp(name="OUT<P|N>"),
            InstanceOp(
                name="M<1|2>",
                ref="sw",
                conns=[ConnAttr(StringAttr("D"), StringAttr("OUT<P|N>"))],
            ),
        ],
    )
    design = DesignOp(region=[module], top="top")

    atomized_first, diagnostics_first = run_pattern_atomization(design)
    assert diagnostics_first == []
    assert atomized_first is not None

    atomized_second, diagnostics_second = run_pattern_atomization(atomized_first)
    assert diagnostics_second == []
    assert atomized_second is not None

    def _snapshot(design_op: DesignOp) -> tuple[list[str], list[tuple[str, str | None]], list]:
        ifir_module = next(
            op for op in design_op.body.block.ops if isinstance(op, ModuleOp)
        )
        port_order = [attr.data for attr in ifir_module.port_order.data]
        nets = [
            (
                net.name_attr.data,
                net.pattern_origin.data if net.pattern_origin else None,
            )
            for net in ifir_module.body.block.ops
            if isinstance(net, NetOp)
        ]
        instances = [
            (
                inst.name_attr.data,
                inst.pattern_origin.data if inst.pattern_origin else None,
                [(conn.port.data, conn.net.data) for conn in inst.conns.data],
            )
            for inst in ifir_module.body.block.ops
            if isinstance(inst, InstanceOp)
        ]
        return port_order, nets, instances

    assert _snapshot(atomized_first) == _snapshot(atomized_second)
