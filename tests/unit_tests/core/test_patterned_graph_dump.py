from __future__ import annotations

import json

from asdl.core import (
    EndpointBundle,
    GroupSlice,
    InstanceBundle,
    ModuleGraph,
    NetBundle,
    ProgramGraph,
    RegistrySet,
    SchematicHints,
    dump_patterned_graph,
    patterned_graph_to_jsonable,
)
from asdl.diagnostics import SourcePos, SourceSpan
from asdl.patterns_refactor.parser import (
    AxisSpec,
    PatternExpr,
    PatternGroup,
    PatternLiteral,
    PatternSegment,
)


def _span(file_id: str, start: int, end: int) -> SourceSpan:
    return SourceSpan(
        file=file_id,
        start=SourcePos(line=1, col=start),
        end=SourcePos(line=1, col=end),
        byte_start=start - 1,
        byte_end=end - 1,
    )


def _build_graph() -> ProgramGraph:
    net_id = "net1"
    inst_id = "inst1"
    endpoint_id = "ep1"

    net = NetBundle(
        net_id=net_id,
        name_expr_id="expr_net",
        endpoint_ids=[endpoint_id],
    )
    inst = InstanceBundle(
        inst_id=inst_id,
        name_expr_id="expr_inst",
        ref_kind="device",
        ref_id="dev1",
        ref_raw="M1",
        param_expr_ids={"w": "expr_param"},
    )
    endpoint = EndpointBundle(
        endpoint_id=endpoint_id,
        net_id=net_id,
        port_expr_id="expr_ep",
    )
    module = ModuleGraph(
        module_id="mod1",
        name="top",
        file_id="design.asdl",
        port_order=["$vdd"],
        nets={net_id: net},
        instances={inst_id: inst},
        endpoints={endpoint_id: endpoint},
    )

    expr = PatternExpr(
        raw="N<1|2>",
        segments=[
            PatternSegment(
                tokens=[
                    PatternLiteral(text="N", span=_span("design.asdl", 1, 2)),
                    PatternGroup(
                        kind="enum",
                        labels=[1, 2],
                        axis_id="n",
                        span=_span("design.asdl", 2, 6),
                    ),
                ],
                span=_span("design.asdl", 1, 6),
            )
        ],
        axes=[
            AxisSpec(
                axis_id="n",
                kind="enum",
                labels=[1, 2],
                size=2,
                order=0,
            )
        ],
        axis_order=["n"],
        span=_span("design.asdl", 1, 6),
    )

    registries = RegistrySet(
        pattern_expressions={"expr1": expr},
        pattern_origins={net_id: ("expr1", 0, 1)},
        param_pattern_origins={(inst_id, "w"): ("expr1", 0)},
        source_spans={net_id: _span("design.asdl", 1, 6)},
        schematic_hints=SchematicHints(
            net_groups={net_id: [GroupSlice(start=0, count=1, label="bus")]},
            hub_group_index=0,
        ),
        annotations={net_id: {"role": "signal"}},
    )

    return ProgramGraph(modules={module.module_id: module}, registries=registries)


def test_patterned_graph_jsonable_shape() -> None:
    graph = _build_graph()

    payload = patterned_graph_to_jsonable(graph)

    assert payload["modules"][0]["module_id"] == "mod1"
    assert payload["modules"][0]["nets"][0]["net_id"] == "net1"
    assert payload["modules"][0]["instances"][0]["ref_kind"] == "device"
    assert payload["registries"]["pattern_expressions"]["expr1"]["raw"] == "N<1|2>"
    assert payload["registries"]["pattern_origins"]["net1"]["expr_id"] == "expr1"
    assert payload["registries"]["param_pattern_origins"][0]["param_name"] == "w"
    assert payload["registries"]["source_spans"]["net1"]["file"] == "design.asdl"
    assert (
        payload["registries"]["schematic_hints"]["net_groups"]["net1"][0]["label"]
        == "bus"
    )
    assert payload["registries"]["annotations"]["net1"]["role"] == "signal"


def test_dump_patterned_graph_is_deterministic() -> None:
    graph = _build_graph()

    payload = patterned_graph_to_jsonable(graph)
    expected = json.dumps(payload, indent=2, sort_keys=True)

    assert dump_patterned_graph(graph) == expected
