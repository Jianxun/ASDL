from __future__ import annotations

from asdl.core import PatternedGraphBuilder
from asdl.diagnostics import SourcePos, SourceSpan
from asdl.lowering import build_atomized_graph
from asdl.patterns import NamedPattern, parse_pattern_expr


def _parse_expr(
    expression: str,
    *,
    named_patterns: dict[str, NamedPattern] | None = None,
    span: SourceSpan | None = None,
):
    expr, errors = parse_pattern_expr(
        expression,
        named_patterns=named_patterns,
        span=span,
    )
    assert errors == []
    assert expr is not None
    return expr


def _span(file: str, line: int, col: int) -> SourceSpan:
    return SourceSpan(
        file=file,
        start=SourcePos(line, col),
        end=SourcePos(line, col + 1),
    )


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


def test_patterned_graph_atomize_attaches_pattern_origins() -> None:
    builder = PatternedGraphBuilder()
    module = builder.add_module("top", "design.asdl")
    net_expr_id = builder.add_expression(_parse_expr("NET<0:1>"))
    inst_expr_id = builder.add_expression(_parse_expr("U<0:1>"))
    endpoint_expr_id = builder.add_expression(_parse_expr("U<0:1>.D"))

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
    nets_by_name = {net.name: net for net in module_graph.nets.values()}
    insts_by_name = {inst.name: inst for inst in module_graph.instances.values()}
    endpoints_by_inst = {
        module_graph.instances[endpoint.inst_id].name: endpoint
        for endpoint in module_graph.endpoints.values()
    }

    net0_origin = nets_by_name["NET0"].pattern_origin
    assert net0_origin is not None
    assert net0_origin.expression_id == net_expr_id
    assert net0_origin.segment_index == 0
    assert net0_origin.atom_index == 0
    assert net0_origin.base_name == "NET"
    assert net0_origin.pattern_parts == [0]

    inst1_origin = insts_by_name["U1"].pattern_origin
    assert inst1_origin is not None
    assert inst1_origin.expression_id == inst_expr_id
    assert inst1_origin.segment_index == 0
    assert inst1_origin.atom_index == 1
    assert inst1_origin.base_name == "U"
    assert inst1_origin.pattern_parts == [1]

    endpoint0_origin = endpoints_by_inst["U0"].pattern_origin
    assert endpoint0_origin is not None
    assert endpoint0_origin.expression_id == endpoint_expr_id
    assert endpoint0_origin.segment_index == 0
    assert endpoint0_origin.atom_index == 0
    assert endpoint0_origin.base_name == "U.D"
    assert endpoint0_origin.pattern_parts == [0]


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
    builder.set_ports(module.module_id, ["P<0|1>"])

    graph = builder.build()
    atomized, diagnostics = build_atomized_graph(graph)

    assert diagnostics == []
    module_graph = next(iter(atomized.modules.values()))
    assert module_graph.ports == ["P0", "P1"]


def test_patterned_graph_atomize_propagates_devices() -> None:
    builder = PatternedGraphBuilder()
    builder.add_expression(_parse_expr("P0"))
    device = builder.add_device(
        "nmos",
        "design.asdl",
        ports=["D", "G", "S"],
        parameters={"w": 1},
        variables={"l": 2},
        attrs={"kind": "mos"},
    )
    builder.add_module("top", "design.asdl")

    graph = builder.build()
    atomized, diagnostics = build_atomized_graph(graph)

    assert diagnostics == []
    assert device.device_id in atomized.devices
    atomized_device = atomized.devices[device.device_id]
    assert atomized_device.name == "nmos"
    assert atomized_device.ports == ["D", "G", "S"]
    assert atomized_device.parameters == {"w": 1}
    assert atomized_device.variables == {"l": 2}
    assert atomized_device.attrs == {"kind": "mos"}


def test_patterned_graph_atomize_propagates_module_variables() -> None:
    builder = PatternedGraphBuilder()
    builder.add_expression(_parse_expr("IN"))
    module = builder.add_module("top", "design.asdl", variables={"corner": "tt", "temp": 27})
    builder.set_ports(module.module_id, ["IN", "OUT"])

    graph = builder.build()
    atomized, diagnostics = build_atomized_graph(graph)

    assert diagnostics == []
    atomized_module = atomized.modules[module.module_id]
    assert atomized_module.variables == {"corner": "tt", "temp": 27}


def test_patterned_graph_atomize_propagates_module_parameters() -> None:
    builder = PatternedGraphBuilder()
    builder.add_expression(_parse_expr("IN"))
    module = builder.add_module(
        "top",
        "design.asdl",
        parameters={"mode": "ac", "m": 2},
    )
    builder.set_ports(module.module_id, ["IN"])

    graph = builder.build()
    atomized, diagnostics = build_atomized_graph(graph)

    assert diagnostics == []
    atomized_module = atomized.modules[module.module_id]
    assert atomized_module.parameters == {"mode": "ac", "m": 2}


def test_patterned_graph_atomize_substitutes_module_variables_in_params() -> None:
    builder = PatternedGraphBuilder()
    module = builder.add_module(
        "top",
        "design.asdl",
        variables={"suffix": "<0|1>", "w_expr": "W{suffix}"},
    )
    inst_expr_id = builder.add_expression(_parse_expr("U<0|1>"))
    param_expr_id = builder.add_expression(_parse_expr("{w_expr}"))

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

    assert diagnostics == []
    module_graph = atomized.modules[module.module_id]
    instances = list(module_graph.instances.values())
    assert [inst.name for inst in instances] == ["U0", "U1"]
    assert [inst.param_values for inst in instances] == [{"W": "W0"}, {"W": "W1"}]


def test_patterned_graph_atomize_reports_undefined_module_variable() -> None:
    builder = PatternedGraphBuilder()
    module = builder.add_module("top", "design.asdl")
    inst_expr_id = builder.add_expression(_parse_expr("U0"))
    missing_span = _span("design.asdl", 12, 8)
    param_expr_id = builder.add_expression(_parse_expr("W{missing}", span=missing_span))

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

    undefined_diags = [diag for diag in diagnostics if diag.code == "IR-012"]
    assert len(undefined_diags) == 1
    assert "missing" in undefined_diags[0].message
    assert undefined_diags[0].primary_span == missing_span
    module_graph = atomized.modules[module.module_id]
    assert list(module_graph.instances.values())[0].param_values is None


def test_patterned_graph_atomize_reports_recursive_module_variable() -> None:
    builder = PatternedGraphBuilder()
    module_span = _span("design.asdl", 3, 1)
    module = builder.add_module(
        "top",
        "design.asdl",
        variables={"a": "{b}", "b": "{a}"},
    )
    builder.register_source_span(module.module_id, module_span)
    inst_expr_id = builder.add_expression(_parse_expr("U0"))
    param_expr_id = builder.add_expression(_parse_expr("{a}"))

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

    recursive_diags = [diag for diag in diagnostics if diag.code == "IR-013"]
    assert len(recursive_diags) == 1
    assert recursive_diags[0].primary_span == module_span
    module_graph = atomized.modules[module.module_id]
    assert list(module_graph.instances.values())[0].param_values is None


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
