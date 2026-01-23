"""Lower PatternedGraph programs into AtomizedGraph representations."""

from __future__ import annotations

from asdl.core.atomized_graph import AtomizedModuleGraph, AtomizedProgramGraph
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
    expr_registry = graph.registries.pattern_expressions
    if expr_registry is None:
        diagnostics.append(
            _diagnostic(
                PATTERN_EXPANSION_ERROR,
                "Pattern expression registry missing for atomization.",
                None,
            )
        )
        return AtomizedProgramGraph(), diagnostics

    source_spans = graph.registries.source_spans
    atomized = AtomizedProgramGraph()

    for module_id, module in graph.modules.items():
        allocator = _IdAllocator()
        atomized_module = AtomizedModuleGraph(
            module_id=module_id,
            name=module.name,
            file_id=module.file_id,
            port_order=None,
            patterned_module_id=module.module_id,
        )
        atomized.modules[module_id] = atomized_module

        module_exprs = _collect_module_expressions(module, expr_registry)
        port_order, port_diags = _expand_port_order(
            module.port_order,
            module_exprs,
            module_name=module.name,
        )
        diagnostics.extend(port_diags)
        atomized_module.port_order = port_order or None

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


__all__ = ["build_atomized_graph"]
