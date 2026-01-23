"""Lower AST documents into PatternedGraph bundles."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Mapping, Optional, Set

from asdl.ast import AsdlDocument, ModuleDecl
from asdl.core.graph import ProgramGraph
from asdl.core.graph_builder import PatternedGraphBuilder
from asdl.diagnostics import Diagnostic
from asdl.imports import ImportGraph, NameEnv, ProgramDB

from .ast_to_patterned_graph_diagnostics import _register_span
from .ast_to_patterned_graph_expressions import (
    _collect_named_patterns,
    _register_expression,
)
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

    device_ids = _lower_devices(document, file_id=file_id, builder=builder)

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


def build_patterned_graph_from_import_graph(
    graph: ImportGraph,
) -> tuple[ProgramGraph, List[Diagnostic]]:
    """Lower an import graph into a PatternedGraph program.

    Args:
        graph: Resolved import graph with documents, name envs, and ProgramDB.

    Returns:
        Tuple of (ProgramGraph, diagnostics).
    """
    diagnostics: List[Diagnostic] = []
    builder = PatternedGraphBuilder()

    file_order = _import_graph_file_order(graph)
    module_ids_by_file: Dict[Path, Dict[str, str]] = {}
    for file_id in file_order:
        document = graph.documents.get(file_id)
        if document is None:
            module_ids_by_file[file_id] = {}
            continue
        module_ids: Dict[str, str] = {}
        for name, module in (document.modules or {}).items():
            module_graph = builder.add_module(name, str(file_id))
            module_ids[name] = module_graph.module_id
            _register_span(builder, module_graph.module_id, getattr(module, "_loc", None))
        module_ids_by_file[file_id] = module_ids

    device_ids_by_file: Dict[Path, Dict[str, str]] = {}
    for file_id in file_order:
        document = graph.documents.get(file_id)
        if document is None:
            device_ids_by_file[file_id] = {}
            continue
        device_ids_by_file[file_id] = _lower_devices(
            document,
            file_id=str(file_id),
            builder=builder,
        )

    for file_id in file_order:
        document = graph.documents.get(file_id)
        if document is None:
            continue
        module_ids = module_ids_by_file.get(file_id, {})
        device_ids = device_ids_by_file.get(file_id, {})
        name_env = graph.name_envs.get(file_id)
        for name, module in (document.modules or {}).items():
            module_id = module_ids.get(name)
            if module_id is None:
                continue
            _lower_module(
                name,
                module,
                module_id=module_id,
                module_ids=module_ids,
                device_ids=device_ids,
                module_ids_by_file=module_ids_by_file,
                device_ids_by_file=device_ids_by_file,
                name_env=name_env,
                program_db=graph.program_db,
                diagnostics=diagnostics,
                builder=builder,
            )

    return builder.build(), diagnostics


def _lower_devices(
    document: AsdlDocument,
    *,
    file_id: Optional[str],
    builder: PatternedGraphBuilder,
) -> Dict[str, str]:
    """Lower device declarations into the program graph.

    Args:
        document: Parsed AST document.
        file_id: Optional file identifier override.
        builder: PatternedGraph builder instance.

    Returns:
        Mapping of device names to stable IDs.
    """
    device_ids: Dict[str, str] = {}
    for name, device in (document.devices or {}).items():
        device_def = builder.add_device(
            name,
            _resolve_file_id(file_id, device),
            ports=device.ports,
            parameters=device.parameters,
            variables=device.variables,
        )
        device_ids[name] = device_def.device_id
        _register_span(builder, device_def.device_id, getattr(device, "_loc", None))
    return device_ids


def _resolve_file_id(file_id: Optional[str], decl: object) -> str:
    """Resolve a declaration file identifier with best-effort fallbacks.

    Args:
        file_id: Optional explicit file identifier.
        decl: Declaration payload for span fallback.

    Returns:
        File identifier string.
    """
    if file_id:
        return file_id
    decl_loc = getattr(decl, "_loc", None)
    if decl_loc is not None and decl_loc.file:
        return decl_loc.file
    return "<unknown>"


def _lower_module(
    name: str,
    module: ModuleDecl,
    *,
    module_id: str,
    module_ids: Mapping[str, str],
    device_ids: Mapping[str, str],
    module_ids_by_file: Optional[Mapping[Path, Mapping[str, str]]] = None,
    device_ids_by_file: Optional[Mapping[Path, Mapping[str, str]]] = None,
    name_env: Optional[NameEnv] = None,
    program_db: Optional[ProgramDB] = None,
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
        module_ids_by_file: Optional per-file module ID mapping for imports.
        device_ids_by_file: Optional per-file device ID mapping for imports.
        name_env: Optional name environment for import namespaces.
        program_db: Optional program database for qualified references.
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
        module_ids_by_file=module_ids_by_file,
        device_ids_by_file=device_ids_by_file,
        name_env=name_env,
        program_db=program_db,
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
            for port_name, net_token in defaults.bindings.items():
                binding_loc = defaults._bindings_loc.get(port_name)
                net_name, is_port = _split_net_token(net_token)
                net_expr_id = _register_expression(
                    net_name,
                    builder=builder,
                    expr_cache=expr_cache,
                    named_patterns=named_patterns,
                    loc=binding_loc,
                    diagnostics=diagnostics,
                    module_name=name,
                    context=f"instance_defaults binding '{port_name}'",
                    require_single_segment=True,
                )
                if net_expr_id is None:
                    continue
                if is_port and net_name not in port_order:
                    port_order.append(net_name)

    builder.set_port_order(module_id, port_order or None)


def _import_graph_file_order(graph: ImportGraph) -> List[Path]:
    """Return deterministic file ordering for an import graph.

    Args:
        graph: Import graph with resolved documents.

    Returns:
        Ordered list of file IDs (entry first, then imports in resolution order).
    """
    order: List[Path] = []
    seen: Set[Path] = set()

    def visit(file_id: Path) -> None:
        if file_id in seen:
            return
        seen.add(file_id)
        order.append(file_id)
        for resolved in graph.imports.get(file_id, {}).values():
            visit(resolved)

    visit(graph.entry_file)
    for file_id in graph.documents.keys():
        if file_id not in seen:
            order.append(file_id)
    return order


__all__ = ["build_patterned_graph", "build_patterned_graph_from_import_graph"]
