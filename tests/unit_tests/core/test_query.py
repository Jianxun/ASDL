from __future__ import annotations

from dataclasses import dataclass

from asdl.core import (
    DesignQuery,
    EndpointBundle,
    GraphIndex,
    InstanceBundle,
    ModuleGraph,
    NetBundle,
    ProgramGraph,
    RegistrySet,
)


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


def _build_module() -> ModuleGraph:
    net_a = NetBundle(net_id="net_a", name_expr_id="expr_net_a", endpoint_ids=["ep_a1", "ep_a2"])
    net_b = NetBundle(net_id="net_b", name_expr_id="expr_net_b", endpoint_ids=["ep_b1"])
    inst_a = InstanceBundle(
        inst_id="inst_a",
        name_expr_id="expr_inst_a",
        ref_kind="device",
        ref_id="dev1",
        ref_raw="M1",
    )
    inst_b = InstanceBundle(
        inst_id="inst_b",
        name_expr_id="expr_inst_b",
        ref_kind="device",
        ref_id="dev2",
        ref_raw="M2",
    )
    endpoints = {
        "ep_a1": EndpointBundle(endpoint_id="ep_a1", net_id="net_a", port_expr_id="expr_ep_a1"),
        "ep_a2": EndpointBundle(endpoint_id="ep_a2", net_id="net_a", port_expr_id="expr_ep_a2"),
        "ep_b1": EndpointBundle(endpoint_id="ep_b1", net_id="net_b", port_expr_id="expr_ep_b1"),
    }
    return ModuleGraph(
        module_id="mod1",
        name="top",
        file_id="file.asdl",
        nets={"net_a": net_a, "net_b": net_b},
        instances={"inst_a": inst_a, "inst_b": inst_b},
        endpoints=endpoints,
    )


def _build_registries() -> RegistrySet:
    return RegistrySet(
        pattern_expressions={
            "expr_net_a": _expr("NET_A"),
            "expr_net_b": _expr("NET_B"),
            "expr_inst_a": _expr("U1"),
            "expr_inst_b": _expr("U2"),
        }
    )


def test_graph_index_name_lookup_is_deterministic() -> None:
    module = _build_module()
    registries = _build_registries()

    index = GraphIndex.from_module(module, registries)

    assert index.net_name_to_id == {"NET_A": "net_a", "NET_B": "net_b"}
    assert index.inst_name_to_id == {"U1": "inst_a", "U2": "inst_b"}


def test_design_query_adjacency_lists() -> None:
    module = _build_module()
    graph = ProgramGraph(modules={module.module_id: module}, registries=_build_registries())

    query = DesignQuery.from_program(graph)

    assert query.net_endpoints(module.module_id, "net_a") == ["ep_a1", "ep_a2"]
    assert query.net_endpoints_by_name(module.module_id, "NET_B") == ["ep_b1"]
    assert query.net_endpoints(module.module_id, "missing") == []


def test_graph_index_falls_back_to_expr_id() -> None:
    module = _build_module()

    index = GraphIndex.from_module(module)

    assert index.net_name_to_id == {"expr_net_a": "net_a", "expr_net_b": "net_b"}
    assert index.inst_name_to_id == {"expr_inst_a": "inst_a", "expr_inst_b": "inst_b"}
