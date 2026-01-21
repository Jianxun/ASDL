from __future__ import annotations

from dataclasses import dataclass

from asdl.core import (
    EndpointBundle,
    InstanceBundle,
    ModuleGraph,
    NetBundle,
    ProgramGraph,
    RegistrySet,
    SchematicHints,
)


@dataclass(frozen=True)
class DummyPatternExpr:
    raw: str


def _build_module() -> ModuleGraph:
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
    return ModuleGraph(
        module_id="mod1",
        name="top",
        file_id="file.asdl",
        nets={net_id: net},
        instances={inst_id: inst},
        endpoints={endpoint_id: endpoint},
    )


def test_patterned_graph_construction() -> None:
    module = _build_module()
    graph = ProgramGraph(modules={module.module_id: module})

    assert graph.modules[module.module_id] is module
    assert module.instances["inst1"].ref_raw == "M1"


def test_endpoint_ownership() -> None:
    module = _build_module()
    net = module.nets["net1"]
    endpoint = module.endpoints["ep1"]

    assert endpoint.net_id == net.net_id
    assert endpoint.endpoint_id in net.endpoint_ids


def test_registry_optionality() -> None:
    graph = ProgramGraph(modules={})

    assert graph.registries.pattern_expressions is None
    assert graph.registries.source_spans is None
    assert graph.registries.schematic_hints is None
    assert graph.registries.annotations is None

    hints = SchematicHints(net_groups={"net1": []})
    registries = RegistrySet(
        pattern_expressions={"expr1": DummyPatternExpr("N<1>")},
        schematic_hints=hints,
        annotations={"net1": {"role": "signal"}},
    )
    graph = ProgramGraph(modules={}, registries=registries)

    assert graph.registries.pattern_expressions == {"expr1": DummyPatternExpr("N<1>")}
    assert graph.registries.schematic_hints is hints
    assert graph.registries.annotations == {"net1": {"role": "signal"}}
