"""Dependency graph model and serialization helpers for ASDL docs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence

from asdl.ast import AsdlDocument
from asdl.diagnostics import Diagnostic, Severity, format_code
from asdl.imports import ImportGraph, NameEnv, ProgramDB, resolve_import_graph

DEPGRAPH_SCHEMA_VERSION = 1
DEPGRAPH_BUILD_ERROR = format_code("TOOL", 100)
NO_SPAN_NOTE = "No source span available."

UNRESOLVED_DEVICE_REFERENCE = "device_reference"
UNRESOLVED_INVALID_REFERENCE = "invalid_reference"
UNRESOLVED_UNKNOWN_NAMESPACE = "unknown_namespace"
UNRESOLVED_UNKNOWN_SYMBOL = "unknown_symbol"


@dataclass(frozen=True)
class DepGraphFile:
    """Represent a resolved ASDL file in the dependency graph.

    Attributes:
        file_id: Normalized absolute file identifier.
        entry: True if the file was listed as an entry file.
    """

    file_id: str
    entry: bool


@dataclass(frozen=True)
class DepGraphModule:
    """Represent a module definition in the dependency graph.

    Attributes:
        module_id: Stable module identifier (`name__hash8`).
        name: Module name for display.
        file_id: Source file identifier.
    """

    module_id: str
    name: str
    file_id: str


@dataclass(frozen=True)
class DepGraphInstance:
    """Represent a module instance declaration in the graph.

    Attributes:
        instance_id: Stable instance identifier (`{module_id}:{name}`).
        name: Instance name in the module.
        module_id: Owning module identifier.
        ref: Raw reference token from the instance expression.
    """

    instance_id: str
    name: str
    module_id: str
    ref: str


@dataclass(frozen=True)
class DepGraphEdge:
    """Represent a module-to-module dependency edge.

    Attributes:
        from_module_id: Module that contains the instance.
        to_module_id: Resolved module referenced by the instance.
        instance_id: Instance identifier that created the dependency.
    """

    from_module_id: str
    to_module_id: str
    instance_id: str


@dataclass(frozen=True)
class DepGraphUnresolved:
    """Represent an instance reference that did not resolve to a module.

    Attributes:
        instance_id: Instance identifier that could not resolve.
        module_id: Owning module identifier.
        ref: Raw reference token from the instance expression.
        reason: Resolution failure reason (see UNRESOLVED_* constants).
    """

    instance_id: str
    module_id: str
    ref: str
    reason: str


@dataclass(frozen=True)
class DependencyGraph:
    """Container for dependency graph data.

    Attributes:
        files: Resolved ASDL files.
        modules: Module definitions across the project.
        instances: Instance declarations across all modules.
        edges: Module-to-module dependency edges.
        unresolved: Instance references that did not resolve to modules.
    """

    files: Sequence[DepGraphFile]
    modules: Sequence[DepGraphModule]
    instances: Sequence[DepGraphInstance]
    edges: Sequence[DepGraphEdge]
    unresolved: Sequence[DepGraphUnresolved]


def build_dependency_graph(
    entry_files: Iterable[Path | str] | Path | str,
    *,
    lib_roots: Optional[Iterable[Path]] = None,
) -> tuple[Optional[DependencyGraph], list[Diagnostic]]:
    """Build a dependency graph from one or more entry ASDL files.

    Args:
        entry_files: Entry ASDL file(s) to seed import resolution.
        lib_roots: Optional library search roots for import resolution.

    Returns:
        Tuple of (DependencyGraph or None, diagnostics).
    """
    diagnostics: list[Diagnostic] = []
    entries = _normalize_entry_files(entry_files)
    if not entries:
        diagnostics.append(_diagnostic(DEPGRAPH_BUILD_ERROR, "No entry files provided."))
        return None, diagnostics

    import_graphs = []
    entry_file_ids: set[Path] = set()
    for entry in entries:
        graph, import_diags = resolve_import_graph(entry, lib_roots=lib_roots)
        diagnostics.extend(import_diags)
        if graph is None:
            continue
        import_graphs.append(graph)
        entry_file_ids.add(graph.entry_file)

    if _has_error_diagnostics(diagnostics):
        return None, diagnostics
    if not import_graphs:
        diagnostics.append(_diagnostic(DEPGRAPH_BUILD_ERROR, "No import graphs resolved."))
        return None, diagnostics

    documents, imports = _merge_import_graphs(import_graphs)
    program_db, program_diags = ProgramDB.build(documents)
    diagnostics.extend(program_diags)
    if _has_error_diagnostics(diagnostics):
        return None, diagnostics

    name_envs = {
        file_id: NameEnv(file_id=file_id, bindings=dict(imports.get(file_id, {})))
        for file_id in documents.keys()
    }

    files = _build_files(documents, entry_file_ids)
    modules, module_ids_by_file = _build_modules(documents)
    instances, edges, unresolved = _build_instances(
        documents,
        module_ids_by_file,
        name_envs,
        program_db,
    )

    graph = DependencyGraph(
        files=files,
        modules=modules,
        instances=instances,
        edges=edges,
        unresolved=unresolved,
    )
    return graph, diagnostics


def dependency_graph_to_jsonable(graph: DependencyGraph) -> dict:
    """Convert a DependencyGraph into a JSON-serializable payload.

    Args:
        graph: Dependency graph to serialize.

    Returns:
        JSON-ready mapping containing files, modules, instances, edges, and unresolved.
    """
    files = sorted(graph.files, key=lambda item: item.file_id)
    modules = sorted(graph.modules, key=lambda item: (item.file_id, item.name))
    instances = sorted(graph.instances, key=lambda item: (item.module_id, item.name))
    edges = sorted(graph.edges, key=lambda item: (item.from_module_id, item.instance_id))
    unresolved = sorted(
        graph.unresolved,
        key=lambda item: (item.module_id, item.instance_id),
    )
    return {
        "schema_version": DEPGRAPH_SCHEMA_VERSION,
        "files": [_file_to_dict(item) for item in files],
        "modules": [_module_to_dict(item) for item in modules],
        "instances": [_instance_to_dict(item) for item in instances],
        "edges": [_edge_to_dict(item) for item in edges],
        "unresolved": [_unresolved_to_dict(item) for item in unresolved],
    }


def dump_dependency_graph(graph: DependencyGraph, *, indent: int = 2) -> str:
    """Serialize a DependencyGraph to JSON text.

    Args:
        graph: Dependency graph to serialize.
        indent: Indentation level for JSON output.

    Returns:
        JSON string representing the dependency graph.
    """
    return json.dumps(dependency_graph_to_jsonable(graph), indent=indent, sort_keys=True)


def _normalize_entry_files(
    entry_files: Iterable[Path | str] | Path | str,
) -> list[Path]:
    """Normalize entry file inputs into a list.

    Args:
        entry_files: Entry file or iterable of entry files.

    Returns:
        List of entry file paths.
    """
    if isinstance(entry_files, (str, Path)):
        entries = [entry_files]
    else:
        entries = list(entry_files)
    return [Path(entry) for entry in entries]


def _merge_import_graphs(
    graphs: Iterable[ImportGraph],
) -> tuple[dict[Path, AsdlDocument], dict[Path, dict[str, Path]]]:
    """Merge import graph documents and imports into unified maps.

    Args:
        graphs: Iterable of ImportGraph instances.

    Returns:
        Tuple of (documents, imports) maps.
    """
    documents: dict[Path, AsdlDocument] = {}
    imports: dict[Path, dict[str, Path]] = {}
    for graph in graphs:
        for file_id, document in graph.documents.items():
            documents.setdefault(file_id, document)
        for file_id, import_map in graph.imports.items():
            imports.setdefault(file_id, dict(import_map))
    return documents, imports


def _build_files(
    documents: dict[Path, AsdlDocument],
    entry_file_ids: set[Path],
) -> list[DepGraphFile]:
    """Build DepGraphFile entries for each document.

    Args:
        documents: Mapping of file IDs to parsed ASDL documents.
        entry_file_ids: Set of entry file IDs.

    Returns:
        Sorted list of DepGraphFile entries.
    """
    files: list[DepGraphFile] = []
    for file_id in sorted(documents.keys(), key=lambda item: str(item)):
        files.append(
            DepGraphFile(
                file_id=str(file_id),
                entry=file_id in entry_file_ids,
            )
        )
    return files


def _build_modules(
    documents: dict[Path, AsdlDocument],
) -> tuple[list[DepGraphModule], dict[Path, dict[str, str]]]:
    """Build DepGraphModule entries and per-file module ID maps.

    Args:
        documents: Mapping of file IDs to parsed ASDL documents.

    Returns:
        Tuple of (module list, module ID map per file).
    """
    modules: list[DepGraphModule] = []
    module_ids_by_file: dict[Path, dict[str, str]] = {}
    for file_id in sorted(documents.keys(), key=lambda item: str(item)):
        document = documents[file_id]
        module_ids: dict[str, str] = {}
        for name, _module in sorted((document.modules or {}).items()):
            module_id = _module_identifier(name, str(file_id))
            module_ids[name] = module_id
            modules.append(
                DepGraphModule(
                    module_id=module_id,
                    name=name,
                    file_id=str(file_id),
                )
            )
        module_ids_by_file[file_id] = module_ids
    return modules, module_ids_by_file


def _build_instances(
    documents: dict[Path, AsdlDocument],
    module_ids_by_file: dict[Path, dict[str, str]],
    name_envs: dict[Path, NameEnv],
    program_db: ProgramDB,
) -> tuple[
    list[DepGraphInstance],
    list[DepGraphEdge],
    list[DepGraphUnresolved],
]:
    """Build instance, edge, and unresolved entries.

    Args:
        documents: Mapping of file IDs to parsed ASDL documents.
        module_ids_by_file: Mapping of file IDs to module ID maps.
        name_envs: Name environment per file for qualified lookups.
        program_db: Program database for symbol resolution.

    Returns:
        Tuple of (instances, edges, unresolved).
    """
    instances: list[DepGraphInstance] = []
    edges: list[DepGraphEdge] = []
    unresolved: list[DepGraphUnresolved] = []
    for file_id in sorted(documents.keys(), key=lambda item: str(item)):
        document = documents[file_id]
        module_ids = module_ids_by_file.get(file_id, {})
        name_env = name_envs.get(file_id)
        for module_name, module in sorted((document.modules or {}).items()):
            module_id = module_ids.get(module_name)
            if module_id is None:
                continue
            for inst_name, inst_expr in sorted((module.instances or {}).items()):
                ref, _params = _parse_instance_expr(inst_expr)
                instance_id = _instance_identifier(module_id, inst_name)
                instances.append(
                    DepGraphInstance(
                        instance_id=instance_id,
                        name=inst_name,
                        module_id=module_id,
                        ref=ref,
                    )
                )
                target_module_id, reason = _resolve_module_ref(
                    ref,
                    file_id,
                    name_env,
                    program_db,
                    module_ids_by_file,
                )
                if target_module_id is not None:
                    edges.append(
                        DepGraphEdge(
                            from_module_id=module_id,
                            to_module_id=target_module_id,
                            instance_id=instance_id,
                        )
                    )
                else:
                    unresolved.append(
                        DepGraphUnresolved(
                            instance_id=instance_id,
                            module_id=module_id,
                            ref=ref,
                            reason=reason,
                        )
                    )
    return instances, edges, unresolved


def _parse_instance_expr(expr: str) -> tuple[str, str]:
    """Split an instance expression into a reference and parameter string.

    Args:
        expr: Raw instance expression string.

    Returns:
        Tuple of (ref, params).
    """
    tokens = expr.split()
    if not tokens:
        return "", ""
    ref = tokens[0]
    params = " ".join(tokens[1:])
    return ref, params


def _resolve_module_ref(
    ref: str,
    file_id: Path,
    name_env: Optional[NameEnv],
    program_db: ProgramDB,
    module_ids_by_file: dict[Path, dict[str, str]],
) -> tuple[Optional[str], str]:
    """Resolve an instance reference to a module identifier if possible.

    Args:
        ref: Reference token from the instance expression.
        file_id: File identifier for the module containing the instance.
        name_env: Name environment for resolving import namespaces.
        program_db: Program database for symbol lookup.
        module_ids_by_file: Per-file mapping of module names to IDs.

    Returns:
        Tuple of (module_id or None, unresolved_reason).
    """
    if not ref:
        return None, UNRESOLVED_INVALID_REFERENCE
    if "." in ref:
        namespace, symbol = ref.split(".", 1)
        if not namespace or not symbol:
            return None, UNRESOLVED_INVALID_REFERENCE
        if name_env is None:
            return None, UNRESOLVED_UNKNOWN_NAMESPACE
        resolved_file = name_env.resolve(namespace)
        if resolved_file is None:
            return None, UNRESOLVED_UNKNOWN_NAMESPACE
        symbol_def = program_db.lookup(resolved_file, symbol)
        if symbol_def is None:
            return None, UNRESOLVED_UNKNOWN_SYMBOL
        if symbol_def.kind != "module":
            return None, UNRESOLVED_DEVICE_REFERENCE
        module_id = module_ids_by_file.get(resolved_file, {}).get(symbol)
        if module_id is None:
            return None, UNRESOLVED_UNKNOWN_SYMBOL
        return module_id, ""

    symbol_def = program_db.lookup(file_id, ref)
    if symbol_def is None:
        return None, UNRESOLVED_UNKNOWN_SYMBOL
    if symbol_def.kind != "module":
        return None, UNRESOLVED_DEVICE_REFERENCE
    module_id = module_ids_by_file.get(file_id, {}).get(ref)
    if module_id is None:
        return None, UNRESOLVED_UNKNOWN_SYMBOL
    return module_id, ""


def _hash_file_id(file_id: str) -> str:
    """Return the short SHA1 hash used for module identifiers.

    Args:
        file_id: Normalized file identifier string.

    Returns:
        The first 8 characters of the file_id SHA1 digest.
    """
    return hashlib.sha1(file_id.encode("utf-8")).hexdigest()[:8]


def _module_identifier(name: str, file_id: str) -> str:
    """Build a stable module identifier from a name and file_id.

    Args:
        name: Module name.
        file_id: Normalized file identifier string.

    Returns:
        Stable module identifier using the `name__hash8` format.
    """
    return f"{name}__{_hash_file_id(file_id)}"


def _instance_identifier(module_id: str, name: str) -> str:
    """Build a stable instance identifier.

    Args:
        module_id: Owning module identifier.
        name: Instance name.

    Returns:
        Instance identifier string.
    """
    return f"{module_id}:{name}"


def module_identifier(name: str, file_id: str) -> str:
    """Build a stable module identifier from a name and file_id.

    Args:
        name: Module name.
        file_id: Normalized file identifier string.

    Returns:
        Stable module identifier using the `name__hash8` format.
    """
    return _module_identifier(name, file_id)


def instance_identifier(module_id: str, name: str) -> str:
    """Build a stable instance identifier.

    Args:
        module_id: Owning module identifier.
        name: Instance name.

    Returns:
        Instance identifier string.
    """
    return _instance_identifier(module_id, name)


def _file_to_dict(item: DepGraphFile) -> dict:
    """Convert a DepGraphFile to a JSON-serializable mapping."""
    return {"file_id": item.file_id, "entry": item.entry}


def _module_to_dict(item: DepGraphModule) -> dict:
    """Convert a DepGraphModule to a JSON-serializable mapping."""
    return {
        "module_id": item.module_id,
        "name": item.name,
        "file_id": item.file_id,
    }


def _instance_to_dict(item: DepGraphInstance) -> dict:
    """Convert a DepGraphInstance to a JSON-serializable mapping."""
    return {
        "instance_id": item.instance_id,
        "name": item.name,
        "module_id": item.module_id,
        "ref": item.ref,
    }


def _edge_to_dict(item: DepGraphEdge) -> dict:
    """Convert a DepGraphEdge to a JSON-serializable mapping."""
    return {
        "from_module_id": item.from_module_id,
        "to_module_id": item.to_module_id,
        "instance_id": item.instance_id,
    }


def _unresolved_to_dict(item: DepGraphUnresolved) -> dict:
    """Convert a DepGraphUnresolved to a JSON-serializable mapping."""
    return {
        "instance_id": item.instance_id,
        "module_id": item.module_id,
        "ref": item.ref,
        "reason": item.reason,
    }


def _has_error_diagnostics(diagnostics: Iterable[Diagnostic]) -> bool:
    """Check whether diagnostics contain error or fatal severities."""
    return any(
        diagnostic.severity in (Severity.ERROR, Severity.FATAL)
        for diagnostic in diagnostics
    )


def _diagnostic(code: str, message: str) -> Diagnostic:
    """Create a dependency-graph diagnostic."""
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        message=message,
        primary_span=None,
        notes=[NO_SPAN_NOTE],
        source="depgraph",
    )


__all__ = [
    "DEPGRAPH_SCHEMA_VERSION",
    "DependencyGraph",
    "DepGraphEdge",
    "DepGraphFile",
    "DepGraphInstance",
    "DepGraphModule",
    "DepGraphUnresolved",
    "UNRESOLVED_DEVICE_REFERENCE",
    "UNRESOLVED_INVALID_REFERENCE",
    "UNRESOLVED_UNKNOWN_NAMESPACE",
    "UNRESOLVED_UNKNOWN_SYMBOL",
    "build_dependency_graph",
    "dependency_graph_to_jsonable",
    "dump_dependency_graph",
    "instance_identifier",
    "module_identifier",
]
