"""Lower PatternedGraph programs into AtomizedGraph representations."""

from __future__ import annotations

from asdl.core.atomized_graph import (
    AtomizedDeviceDef,
    AtomizedModuleGraph,
    AtomizedProgramGraph,
)
from asdl.core.verify_atomized_graph import verify_atomized_graph_if_clean
from asdl.core.graph import ProgramGraph
from asdl.diagnostics import Diagnostic

from .patterned_graph_to_atomized_context import (
    INVALID_ENDPOINT_EXPR,
    PATTERN_EXPANSION_ERROR,
    ModuleAtomizationContext,
    _IdAllocator,
    _diagnostic,
)
from .patterned_graph_to_atomized_instances import (
    _collect_module_expressions,
    _expand_port_order,
    atomize_instances,
)
from .patterned_graph_to_atomized_nets import atomize_nets


def build_atomized_graph(
    graph: ProgramGraph,
) -> tuple[AtomizedProgramGraph, list[Diagnostic]]:
    """Lower a PatternedGraph program into an AtomizedGraph program.

    Args:
        graph: PatternedGraph program to atomize.

    Returns:
        Tuple of (atomized program graph, diagnostics).
    """
    diagnostics: list[Diagnostic] = []
    atomized = AtomizedProgramGraph()
    for device_id, device in graph.devices.items():
        atomized.devices[device_id] = AtomizedDeviceDef(
            device_id=device.device_id,
            name=device.name,
            file_id=device.file_id,
            ports=list(device.ports or []),
            parameters=device.parameters,
            variables=device.variables,
            attrs=device.attrs,
        )

    expr_registry = graph.registries.pattern_expressions
    if expr_registry is None:
        diagnostics.append(
            _diagnostic(
                PATTERN_EXPANSION_ERROR,
                "Pattern expression registry missing for atomization.",
                None,
            )
        )
        return atomized, diagnostics

    source_spans = graph.registries.source_spans

    for module_id, module in graph.modules.items():
        allocator = _IdAllocator()
        atomized_module = AtomizedModuleGraph(
            module_id=module_id,
            name=module.name,
            file_id=module.file_id,
            ports=[],
            patterned_module_id=module.module_id,
        )
        atomized.modules[module_id] = atomized_module

        module_exprs = _collect_module_expressions(module, expr_registry)
        ports, port_diags = _expand_port_order(
            module.ports,
            module_exprs,
            module_name=module.name,
        )
        diagnostics.extend(port_diags)
        atomized_module.ports = ports

        context = ModuleAtomizationContext(
            module=module,
            atomized_module=atomized_module,
            expr_registry=expr_registry,
            source_spans=source_spans,
            allocator=allocator,
            diagnostics=diagnostics,
        )
        atomize_instances(context)
        atomize_nets(context)

        for net_id, net in atomized_module.nets.items():
            if not net.endpoint_ids:
                diagnostics.append(
                    _diagnostic(
                        INVALID_ENDPOINT_EXPR,
                        (
                            f"Net '{net.name}' in module '{module.name}' has no "
                            "legal endpoints after atomization."
                        ),
                        context.net_spans.get(net_id),
                    )
                )

    return atomized, diagnostics


def build_atomized_graph_and_verify(
    graph: ProgramGraph,
) -> tuple[AtomizedProgramGraph, list[Diagnostic]]:
    """Lower and verify a PatternedGraph program into an AtomizedGraph program.

    Args:
        graph: PatternedGraph program to atomize.

    Returns:
        Tuple of (atomized program graph, diagnostics).
    """
    atomized, diagnostics = build_atomized_graph(graph)
    diagnostics = verify_atomized_graph_if_clean(atomized, diagnostics)
    return atomized, diagnostics


__all__ = ["build_atomized_graph", "build_atomized_graph_and_verify"]
