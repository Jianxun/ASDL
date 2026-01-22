from __future__ import annotations

from dataclasses import dataclass

from asdl.core import PatternedGraphBuilder
from asdl.core.registries import GroupSlice


@dataclass(frozen=True)
class DummyPatternSegment:
    tokens: list[object]
    span: object | None


@dataclass(frozen=True)
class DummyAxisSpec:
    axis_id: str
    kind: str
    labels: list[str | int]
    size: int
    order: int


@dataclass(frozen=True)
class DummyPatternExpr:
    raw: str
    segments: list[DummyPatternSegment]
    axes: list[DummyAxisSpec]
    axis_order: list[str]
    span: object | None


def _expr(raw: str) -> DummyPatternExpr:
    return DummyPatternExpr(
        raw=raw,
        segments=[DummyPatternSegment(tokens=[raw], span=None)],
        axes=[],
        axis_order=[],
        span=None,
    )


def test_builder_empty_registries_are_none() -> None:
    builder = PatternedGraphBuilder()
    builder.add_module("top", "file.asdl")

    graph = builder.build()

    assert graph.registries.pattern_expressions is None
    assert graph.registries.pattern_origins is None
    assert graph.registries.param_pattern_origins is None
    assert graph.registries.source_spans is None
    assert graph.registries.schematic_hints is None
    assert graph.registries.annotations is None


def test_builder_builds_graph_with_registries() -> None:
    builder = PatternedGraphBuilder()
    module = builder.add_module("top", "file.asdl")

    expr = _expr("NET")
    expr_id = builder.add_expression(expr)
    net_id = builder.add_net(module.module_id, expr_id)
    inst_id = builder.add_instance(
        module.module_id,
        expr_id,
        ref_kind="device",
        ref_id="dev1",
        ref_raw="M1",
        param_expr_ids={"w": expr_id},
    )
    endpoint_id = builder.add_endpoint(module.module_id, net_id, expr_id)
    builder.register_pattern_origin(net_id, expr_id, 0, 0)
    builder.register_param_origin(inst_id, "w", expr_id, 0)
    builder.register_net_groups(net_id, [GroupSlice(start=0, count=1, label=None)])
    builder.set_port_order(module.module_id, ["NET"])

    graph = builder.build()
    module_graph = graph.modules[module.module_id]

    assert module_graph.port_order == ["NET"]
    assert module_graph.nets[net_id].endpoint_ids == [endpoint_id]
    assert graph.registries.pattern_expressions == {expr_id: expr}
    assert graph.registries.pattern_origins == {net_id: (expr_id, 0, 0)}
    assert graph.registries.param_pattern_origins == {(inst_id, "w"): (expr_id, 0)}
    assert graph.registries.schematic_hints is not None
    assert graph.registries.schematic_hints.net_groups[net_id][0].count == 1
