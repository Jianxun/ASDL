"""Lower AST documents into PatternedGraph bundles."""

from __future__ import annotations

from typing import Dict, Iterable, List, Mapping, Optional

from asdl.ast import AsdlDocument, ModuleDecl
from asdl.core.graph import ProgramGraph
from asdl.core.graph_builder import PatternedGraphBuilder
from asdl.diagnostics import Diagnostic

from .ast_to_patterned_graph_diagnostics import _register_span
from .ast_to_patterned_graph_expressions import _collect_named_patterns
from .ast_to_patterned_graph_instances import _lower_instances
from .ast_to_patterned_graph_nets import _lower_nets, _split_net_token


def build_patterned_graph(
    document: AsdlDocument,
    *,
    file_id: Optional[str] = None,
) -> tuple[ProgramGraph, List[Diagnostic]]:
    """Lower a parsed AST document into a PatternedGraph program.

    Args:
        document: Parsed AST document.
        file_id: Optional file identifier to attach to module graphs.

    Returns:
        Tuple of (ProgramGraph, diagnostics).
    """
    diagnostics: List[Diagnostic] = []
    builder = PatternedGraphBuilder()

    module_graphs: Dict[str, str] = {}
    for name, module in (document.modules or {}).items():
        module_graph = builder.add_module(name, _resolve_file_id(file_id, module))
        module_graphs[name] = module_graph.module_id
        _register_span(builder, module_graph.module_id, getattr(module, "_loc", None))

    device_ids = _allocate_ids((document.devices or {}).keys(), "d")

    for name, module in (document.modules or {}).items():
        module_id = module_graphs[name]
        _lower_module(
            name,
            module,
            module_id=module_id,
            module_ids=module_graphs,
            device_ids=device_ids,
            diagnostics=diagnostics,
            builder=builder,
        )

    return builder.build(), diagnostics


def _allocate_ids(names: Iterable[str], prefix: str) -> Dict[str, str]:
    """Allocate deterministic identifiers for named symbols.

    Args:
        names: Ordered sequence of names.
        prefix: Prefix for the identifiers.

    Returns:
        Mapping of name to allocated identifier.
    """
    return {name: f"{prefix}{index}" for index, name in enumerate(names, start=1)}


def _resolve_file_id(file_id: Optional[str], module: ModuleDecl) -> str:
    """Resolve a module file identifier with best-effort fallbacks.

    Args:
        file_id: Optional explicit file identifier.
        module: Module declaration for span fallback.

    Returns:
        File identifier string.
    """
    if file_id:
        return file_id
    module_loc = getattr(module, "_loc", None)
    if module_loc is not None and module_loc.file:
        return module_loc.file
    return "<unknown>"


def _lower_module(
    name: str,
    module: ModuleDecl,
    *,
    module_id: str,
    module_ids: Mapping[str, str],
    device_ids: Mapping[str, str],
    diagnostics: List[Diagnostic],
    builder: PatternedGraphBuilder,
) -> None:
    """Lower a module declaration into a ModuleGraph.

    Args:
        name: Module name.
        module: Module declaration.
        module_id: Stable module identifier.
        module_ids: Mapping of module names to IDs.
        device_ids: Mapping of device names to IDs.
        diagnostics: Diagnostics list to append to.
        builder: PatternedGraph builder instance.
    """
    expr_cache: Dict[str, str] = {}
    named_patterns = _collect_named_patterns(module)

    instance_refs = _lower_instances(
        name,
        module,
        module_id=module_id,
        module_ids=module_ids,
        device_ids=device_ids,
        expr_cache=expr_cache,
        named_patterns=named_patterns,
        diagnostics=diagnostics,
        builder=builder,
    )

    port_order = _lower_nets(
        name,
        module,
        module_id=module_id,
        expr_cache=expr_cache,
        named_patterns=named_patterns,
        diagnostics=diagnostics,
        builder=builder,
    )

    if module.instance_defaults and instance_refs:
        for ref, defaults in module.instance_defaults.items():
            if ref not in instance_refs:
                continue
            for net_token in defaults.bindings.values():
                net_name, is_port = _split_net_token(net_token)
                if is_port and net_name not in port_order:
                    port_order.append(net_name)

    builder.set_port_order(module_id, port_order or None)


__all__ = ["build_patterned_graph"]
