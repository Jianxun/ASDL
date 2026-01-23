from __future__ import annotations

from asdl.core import PatternedGraphBuilder
from asdl.lowering import build_atomized_graph
from asdl.patterns_refactor import NamedPattern, parse_pattern_expr


def _parse_expr(
    expression: str,
    *,
    named_patterns: dict[str, NamedPattern] | None = None,
):
    expr, errors = parse_pattern_expr(expression, named_patterns=named_patterns)
    assert errors == []
    assert expr is not None
    return expr


def _endpoint_map(module_graph):
    inst_names = {inst_id: inst.name for inst_id, inst in module_graph.instances.items()}
    net_by_name = {net.name: net for net in module_graph.nets.values()}
    mapped: dict[str, list[tuple[str, str]]] = {}
    for net_name, net in net_by_name.items():
        mapped[net_name] = [
            (
                inst_names[module_graph.endpoints[endpoint_id].inst_id],
                module_graph.endpoints[endpoint_id].port,
            )
            for endpoint_id in net.endpoint_ids
        ]
    return mapped


def test_patterned_graph_atomize_basic_expansion() -> None:
    builder = PatternedGraphBuilder()
    module = builder.add_module("top", "design.asdl")
    net_expr_id = builder.add_expression(_parse_expr("NET<0|1>"))
    inst_expr_id = builder.add_expression(_parse_expr("U<0|1>"))
    endpoint_expr_id = builder.add_expression(_parse_expr("U<0|1>.D"))

    net_id = builder.add_net(module.module_id, net_expr_id)
    builder.add_instance(
        module.module_id,
        inst_expr_id,
        ref_kind="device",
        ref_id="dev1",
        ref_raw="nmos",
    )
    builder.add_endpoint(module.module_id, net_id, endpoint_expr_id)

    graph = builder.build()
    atomized, diagnostics = build_atomized_graph(graph)

    assert diagnostics == []
    module_graph = next(iter(atomized.modules.values()))
    assert [net.name for net in module_graph.nets.values()] == ["NET0", "NET1"]
    assert [inst.name for inst in module_graph.instances.values()] == ["U0", "U1"]
    assert _endpoint_map(module_graph) == {
        "NET0": [("U0", "D")],
        "NET1": [("U1", "D")],
    }


def test_patterned_graph_atomize_broadcast_binding() -> None:
    named_patterns = {
        "cols": NamedPattern(expr="<0|1>", tag="c"),
        "rows": NamedPattern(expr="<0|1>", tag="r"),
    }
    builder = PatternedGraphBuilder()
    module = builder.add_module("top", "design.asdl")
    net_expr_id = builder.add_expression(
        _parse_expr("BUS<@cols>", named_patterns=named_patterns)
    )
    inst_expr_id = builder.add_expression(
        _parse_expr("U<@rows><@cols>", named_patterns=named_patterns)
    )
    endpoint_expr_id = builder.add_expression(
        _parse_expr("U<@rows><@cols>.D", named_patterns=named_patterns)
    )

    net_id = builder.add_net(module.module_id, net_expr_id)
    builder.add_instance(
        module.module_id,
        inst_expr_id,
        ref_kind="device",
        ref_id="dev1",
        ref_raw="nmos",
    )
    builder.add_endpoint(module.module_id, net_id, endpoint_expr_id)

    graph = builder.build()
    atomized, diagnostics = build_atomized_graph(graph)

    assert diagnostics == []
    module_graph = next(iter(atomized.modules.values()))
    assert [net.name for net in module_graph.nets.values()] == ["BUS0", "BUS1"]
    assert [inst.name for inst in module_graph.instances.values()] == [
        "U00",
        "U01",
        "U10",
        "U11",
    ]
    assert _endpoint_map(module_graph) == {
        "BUS0": [("U00", "D"), ("U10", "D")],
        "BUS1": [("U01", "D"), ("U11", "D")],
    }


def test_patterned_graph_atomize_binding_error_emits_diagnostic() -> None:
    builder = PatternedGraphBuilder()
    module = builder.add_module("top", "design.asdl")
    net_expr_id = builder.add_expression(_parse_expr("NET<0|1>"))
    inst_expr_id = builder.add_expression(_parse_expr("U<0|1|2>"))
    endpoint_expr_id = builder.add_expression(_parse_expr("U<0|1|2>.D"))

    net_id = builder.add_net(module.module_id, net_expr_id)
    builder.add_instance(
        module.module_id,
        inst_expr_id,
        ref_kind="device",
        ref_id="dev1",
        ref_raw="nmos",
    )
    builder.add_endpoint(module.module_id, net_id, endpoint_expr_id)

    graph = builder.build()
    atomized, diagnostics = build_atomized_graph(graph)

    assert any(diag.code == "IR-003" for diag in diagnostics)
    module_graph = next(iter(atomized.modules.values()))
    assert module_graph.endpoints == {}


def test_patterned_graph_atomize_duplicate_instance_atoms() -> None:
    builder = PatternedGraphBuilder()
    module = builder.add_module("top", "design.asdl")
    net_expr_id = builder.add_expression(_parse_expr("NET0"))
    inst_expr_id = builder.add_expression(_parse_expr("U<0>;U<0>"))
    endpoint_expr_id = builder.add_expression(_parse_expr("U0.D"))

    net_id = builder.add_net(module.module_id, net_expr_id)
    builder.add_instance(
        module.module_id,
        inst_expr_id,
        ref_kind="device",
        ref_id="dev1",
        ref_raw="nmos",
    )
    builder.add_endpoint(module.module_id, net_id, endpoint_expr_id)

    graph = builder.build()
    atomized, diagnostics = build_atomized_graph(graph)

    assert any("duplicate" in diag.message.lower() for diag in diagnostics)
    assert any("non-unique" in diag.message.lower() for diag in diagnostics)
    module_graph = next(iter(atomized.modules.values()))
    assert [inst.name for inst in module_graph.instances.values()] == ["U0"]
    assert _endpoint_map(module_graph) == {"NET0": []}


def test_patterned_graph_atomize_duplicate_net_atoms() -> None:
    builder = PatternedGraphBuilder()
    module = builder.add_module("top", "design.asdl")
    net_expr_id = builder.add_expression(_parse_expr("NET<0>;NET<0>"))
    inst_expr_id = builder.add_expression(_parse_expr("U0"))
    endpoint_expr_id = builder.add_expression(_parse_expr("U0.D;U0.D"))

    net_id = builder.add_net(module.module_id, net_expr_id)
    builder.add_instance(
        module.module_id,
        inst_expr_id,
        ref_kind="device",
        ref_id="dev1",
        ref_raw="nmos",
    )
    builder.add_endpoint(module.module_id, net_id, endpoint_expr_id)

    graph = builder.build()
    atomized, diagnostics = build_atomized_graph(graph)

    assert any("duplicate" in diag.message.lower() for diag in diagnostics)
    module_graph = next(iter(atomized.modules.values()))
    assert [net.name for net in module_graph.nets.values()] == ["NET0"]


def test_patterned_graph_atomize_param_length_mismatch_omits_params() -> None:
    builder = PatternedGraphBuilder()
    module = builder.add_module("top", "design.asdl")
    inst_expr_id = builder.add_expression(_parse_expr("U<0|1>"))
    param_expr_id = builder.add_expression(_parse_expr("P<0|1|2>"))

    builder.add_instance(
        module.module_id,
        inst_expr_id,
        ref_kind="device",
        ref_id="dev1",
        ref_raw="nmos",
        param_expr_ids={"W": param_expr_id},
    )

    graph = builder.build()
    atomized, diagnostics = build_atomized_graph(graph)

    assert any(diag.code == "IR-003" for diag in diagnostics)
    module_graph = next(iter(atomized.modules.values()))
    assert all(inst.param_values is None for inst in module_graph.instances.values())


def test_patterned_graph_atomize_port_order_expands_registered_expr() -> None:
    builder = PatternedGraphBuilder()
    module = builder.add_module("top", "design.asdl")
    builder.add_expression(_parse_expr("P<0|1>"))
    builder.set_port_order(module.module_id, ["P<0|1>"])

    graph = builder.build()
    atomized, diagnostics = build_atomized_graph(graph)

    assert diagnostics == []
    module_graph = next(iter(atomized.modules.values()))
    assert module_graph.port_order == ["P0", "P1"]


def test_patterned_graph_atomize_endpoint_uniqueness() -> None:
    builder = PatternedGraphBuilder()
    module = builder.add_module("top", "design.asdl")
    net0_expr_id = builder.add_expression(_parse_expr("N0"))
    net1_expr_id = builder.add_expression(_parse_expr("N1"))
    inst_expr_id = builder.add_expression(_parse_expr("U0"))
    endpoint_expr_id = builder.add_expression(_parse_expr("U0.D"))

    net0_id = builder.add_net(module.module_id, net0_expr_id)
    net1_id = builder.add_net(module.module_id, net1_expr_id)
    builder.add_instance(
        module.module_id,
        inst_expr_id,
        ref_kind="device",
        ref_id="dev1",
        ref_raw="nmos",
    )
    builder.add_endpoint(module.module_id, net0_id, endpoint_expr_id)
    builder.add_endpoint(module.module_id, net1_id, endpoint_expr_id)

    graph = builder.build()
    atomized, diagnostics = build_atomized_graph(graph)

    assert any(diag.code == "IR-002" for diag in diagnostics)
    module_graph = next(iter(atomized.modules.values()))
    assert _endpoint_map(module_graph) == {"N0": [("U0", "D")], "N1": []}
