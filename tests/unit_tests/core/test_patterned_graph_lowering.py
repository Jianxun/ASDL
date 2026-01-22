from __future__ import annotations

from asdl.ast import (
    AsdlDocument,
    DeviceBackendDecl,
    DeviceDecl,
    InstanceDefaultsDecl,
    ModuleDecl,
    PatternDecl,
)
from asdl.ast.location import Locatable
from asdl.core import GroupSlice, build_patterned_graph


def _loc(line: int, col: int, length: int = 1, file_name: str = "design.asdl") -> Locatable:
    return Locatable(
        file=file_name,
        start_line=line,
        start_col=col,
        end_line=line,
        end_col=col + length,
    )


def test_build_patterned_graph_with_groups_and_patterns() -> None:
    module = ModuleDecl.model_construct(
        instances={"U<@cols>": "nmos W=<0|1>"},
        nets={
            "$BUS<@cols>": [
                ["U<@cols>.D", "U<@cols>.G"],
                ["U<@cols>.S"],
            ]
        },
        patterns={"cols": PatternDecl(expr="<0|1>", tag="col")},
    )
    module._loc = _loc(1, 1)
    module._instances_loc["U<@cols>"] = _loc(2, 3)
    module._instance_expr_loc["U<@cols>"] = _loc(2, 10)
    module._nets_loc["$BUS<@cols>"] = _loc(3, 3)
    module._net_endpoint_locs["$BUS<@cols>"] = [_loc(4, 5), _loc(5, 5)]

    device = DeviceDecl(
        ports=None,
        parameters=None,
        variables=None,
        backends={"sim.ngspice": DeviceBackendDecl(template="M")},
    )
    document = AsdlDocument.model_construct(
        modules={"top": module},
        devices={"nmos": device},
        top="top",
    )

    graph, diagnostics = build_patterned_graph(document, file_id="design.asdl")

    assert diagnostics == []
    module_graph = next(iter(graph.modules.values()))
    assert module_graph.port_order == ["BUS<@cols>"]

    net_id = next(iter(module_graph.nets))
    net_bundle = module_graph.nets[net_id]
    assert net_bundle.endpoint_ids == list(module_graph.endpoints.keys())

    hints = graph.registries.schematic_hints
    assert hints is not None
    assert hints.net_groups[net_id] == [
        GroupSlice(start=0, count=2, label=None),
        GroupSlice(start=2, count=1, label=None),
    ]

    exprs = graph.registries.pattern_expressions
    assert exprs is not None
    expr_by_raw = {expr.raw: expr for expr in exprs.values()}
    assert expr_by_raw["BUS<@cols>"].axis_order == ["col"]

    inst_id = next(iter(module_graph.instances))
    inst_bundle = module_graph.instances[inst_id]
    assert inst_bundle.param_expr_ids is not None
    param_expr_id = inst_bundle.param_expr_ids["W"]
    assert exprs[param_expr_id].raw == "<0|1>"

    origins = graph.registries.pattern_origins
    assert origins is not None
    assert origins[net_id] == (net_bundle.name_expr_id, 0, 0)

    param_origins = graph.registries.param_pattern_origins
    assert param_origins is not None
    assert param_origins[(inst_id, "W")] == (param_expr_id, 0)

    spans = graph.registries.source_spans
    assert spans is not None
    assert spans[net_id].file == "design.asdl"


def test_build_patterned_graph_port_order_appends_default_ports() -> None:
    module = ModuleDecl.model_construct(
        instances={"U1": "nmos"},
        nets={
            "$A": ["U1.D"],
            "$B": ["U1.G"],
        },
        instance_defaults={
            "nmos": InstanceDefaultsDecl.model_construct(
                bindings={
                    "G": "$CTRL",
                    "S": "VSS",
                    "B": "$A",
                    "D": "$VDD",
                }
            )
        },
    )
    device = DeviceDecl(
        ports=None,
        parameters=None,
        variables=None,
        backends={"sim.ngspice": DeviceBackendDecl(template="M")},
    )
    document = AsdlDocument.model_construct(
        modules={"top": module},
        devices={"nmos": device},
        top="top",
    )

    graph, diagnostics = build_patterned_graph(document, file_id="design.asdl")

    assert diagnostics == []
    module_graph = next(iter(graph.modules.values()))
    assert module_graph.port_order == ["A", "B", "CTRL", "VDD"]


def test_build_patterned_graph_invalid_instance_expr_emits_ir001() -> None:
    document = AsdlDocument(
        modules={
            "top": ModuleDecl(
                instances={"M1": "res bad"},
                nets={"OUT": ["M1.P"]},
            )
        },
        devices={
            "res": DeviceDecl(
                ports=None,
                parameters=None,
                variables=None,
                backends={"sim.ngspice": DeviceBackendDecl(template="R")},
            )
        },
    )

    _, diagnostics = build_patterned_graph(document, file_id="design.asdl")

    assert any(diag.code == "IR-001" for diag in diagnostics)


def test_build_patterned_graph_invalid_endpoint_expr_emits_ir002() -> None:
    document = AsdlDocument(
        modules={
            "top": ModuleDecl(
                instances={"M1": "res"},
                nets={"OUT": ["M1"]},
            )
        },
        devices={
            "res": DeviceDecl(
                ports=None,
                parameters=None,
                variables=None,
                backends={"sim.ngspice": DeviceBackendDecl(template="R")},
            )
        },
    )

    _, diagnostics = build_patterned_graph(document, file_id="design.asdl")

    assert any(diag.code == "IR-002" for diag in diagnostics)


def test_build_patterned_graph_pattern_parse_failure_emits_ir003() -> None:
    document = AsdlDocument(
        modules={
            "top": ModuleDecl(
                instances={"M1": "res"},
                nets={"$BUS<>": ["M1.P"]},
            )
        },
        devices={
            "res": DeviceDecl(
                ports=None,
                parameters=None,
                variables=None,
                backends={"sim.ngspice": DeviceBackendDecl(template="R")},
            )
        },
    )

    _, diagnostics = build_patterned_graph(document, file_id="design.asdl")

    assert any(diag.code == "IR-003" for diag in diagnostics)
