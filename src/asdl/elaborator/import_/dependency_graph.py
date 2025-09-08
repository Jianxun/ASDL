"""
Dependency graph construction for the ASDL import system.

Builds an ImportGraph, alias resolution map, and loads dependencies using
the FileLoader while avoiding duplicate circular checks outside the loader.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
import json
import os

from ...data_structures import ASDLFile
from ...diagnostics import Diagnostic
from ...logging_utils import get_logger
from .file_loader import FileLoader
from .path_resolver import PathResolver
from .diagnostics import ImportDiagnostics
from .types import ImportGraph, GraphNode, AliasResolutionMap


class DependencyGraphBuilder:
    """Constructs the import dependency graph and loads dependencies."""

    def __init__(
        self,
        path_resolver: Optional[PathResolver] = None,
        file_loader: Optional[FileLoader] = None,
        diagnostics: Optional[ImportDiagnostics] = None,
    ) -> None:
        self.path_resolver = path_resolver or PathResolver()
        self.file_loader = file_loader or FileLoader()
        self.diagnostics = diagnostics or ImportDiagnostics()

    def build(
        self,
        main_file: ASDLFile,
        main_file_path: Path,
        search_paths: Optional[List[Path]] = None,
    ) -> Tuple[ImportGraph, AliasResolutionMap, Dict[Path, ASDLFile], List[Diagnostic]]:
        """
        Build the dependency graph starting from the main file.
        Returns graph, alias_resolution_map, loaded_files (abs paths), and diagnostics.
        """
        log = get_logger("elaborator.imports")
        diagnostics: List[Diagnostic] = []
        graph = ImportGraph()
        alias_map: AliasResolutionMap = {}
        loaded_files: Dict[Path, ASDLFile] = {}

        # Normalize main file path to absolute for consistent identity
        main_file_path = main_file_path.resolve()

        if search_paths is None:
            search_paths = self.path_resolver.get_search_paths()
        log.debug(f"Search paths: {[str(p) for p in search_paths]}")

        # Seed root node
        graph.nodes[main_file_path] = GraphNode(
            file_path=main_file_path,
            asdl_file=main_file,
            imports=main_file.imports or {},
        )
        graph.edges[main_file_path] = set()
        alias_map[main_file_path] = {}

        # DFS load
        self._dfs_load(
            current_file=main_file,
            current_path=main_file_path,
            search_paths=list(search_paths),
            graph=graph,
            alias_map=alias_map,
            loaded_files=loaded_files,
            diagnostics=diagnostics,
            loading_stack=[],
        )

        return graph, alias_map, loaded_files, diagnostics

    def _dfs_load(
        self,
        current_file: ASDLFile,
        current_path: Path,
        search_paths: List[Path],
        graph: ImportGraph,
        alias_map: AliasResolutionMap,
        loaded_files: Dict[Path, ASDLFile],
        diagnostics: List[Diagnostic],
        loading_stack: List[Path],
    ) -> None:
        if not current_file.imports:
            return

        log = get_logger("elaborator.imports")
        alias_map.setdefault(current_path, {})

        for import_alias, import_path in current_file.imports.items():
            # Effective roots: [dir(current_file)] + configured search_paths
            importer_root = current_path.parent
            effective_roots: List[Path] = [importer_root] + list(search_paths)

            # Probe all candidates across effective roots
            candidates: List[Path] = []
            seen: Set[Path] = set()
            for root in effective_roots:
                candidate_path = (root / import_path).resolve()
                if candidate_path.exists() and candidate_path.is_file():
                    if candidate_path not in seen:
                        candidates.append(candidate_path)
                        seen.add(candidate_path)

            if len(candidates) > 1:
                diagnostics.append(
                    self.diagnostics.create_ambiguous_import_error(import_alias, import_path, candidates)
                )
                # Record unresolved due to ambiguity
                alias_map[current_path][import_alias] = None
                continue

            resolved_path = candidates[0] if candidates else None
            alias_map[current_path][import_alias] = resolved_path
            try:
                log.trace(f"Resolve alias '{import_alias}': '{import_path}' -> {resolved_path}")
            except AttributeError:
                log.debug(f"Resolve alias '{import_alias}': '{import_path}' -> {resolved_path}")

            if resolved_path is None:
                # File not found with explicit probe list
                # Build probe list using effective roots
                probe_paths = [(root / import_path).resolve() for root in effective_roots]
                diag = self.diagnostics.create_file_not_found_error(import_alias, import_path, probe_paths)
                diagnostics.append(diag)
                continue

            # Add edge in graph
            graph.edges.setdefault(current_path, set()).add(resolved_path)

            if resolved_path in loaded_files:
                continue

            # Load via FileLoader; it will emit E0442 on cycles
            loaded_file, load_diags = self.file_loader.load_file_with_dependency_check(
                resolved_path, loading_stack + [current_path]
            )
            diagnostics.extend(load_diags)

            if loaded_file is None:
                continue

            loaded_files[resolved_path] = loaded_file
            # Register node in graph
            graph.nodes[resolved_path] = GraphNode(
                file_path=resolved_path,
                asdl_file=loaded_file,
                imports=loaded_file.imports or {},
            )
            graph.edges.setdefault(resolved_path, set())
            alias_map.setdefault(resolved_path, {})

            # Recurse
            self._dfs_load(
                current_file=loaded_file,
                current_path=resolved_path,
                search_paths=search_paths,
                graph=graph,
                alias_map=alias_map,
                loaded_files=loaded_files,
                diagnostics=diagnostics,
                loading_stack=loading_stack + [current_path],
            )




# --- Serialization helpers ----------------------------------------------------

def _format_path_for_export(path: Path, base_dir: Optional[Path]) -> str:
    """Format a path as relative to base_dir when provided, else as absolute.

    Args:
        path: Absolute path to format
        base_dir: Optional base directory to relativize paths against

    Returns:
        String path suitable for human-readable artifacts
    """
    if base_dir is None:
        return str(path)
    try:
        # Normalize to resolved absolute paths to avoid symlink prefix issues
        abs_path = path.resolve()
        abs_base = base_dir.resolve()
        return os.path.relpath(str(abs_path), str(abs_base))
    except Exception:
        return str(path)


def export_import_graph(
    graph: ImportGraph,
    alias_map: AliasResolutionMap,
    base_dir: Optional[Path] = None,
    include_absolute: bool = False,
) -> Dict:
    """Serialize the import dependency graph and alias map to a dict.

    Args:
        graph: ImportGraph built by DependencyGraphBuilder
        alias_map: AliasResolutionMap keyed by absolute paths
        base_dir: If provided, emit relative paths w.r.t. this directory
        include_absolute: When True, include absolute paths alongside relative

    Returns:
        A JSON-serializable dict with nodes, edges, and alias_map
    """
    payload_nodes: List[Dict] = []
    for abs_path, node in graph.nodes.items():
        entry = {
            "path": _format_path_for_export(abs_path, base_dir),
            "num_modules": len(node.asdl_file.modules or {}),
        }
        if include_absolute:
            entry["abs_path"] = str(abs_path)
        payload_nodes.append(entry)

    payload_edges: List[Dict] = []
    for src_abs, dest_set in graph.edges.items():
        for dest_abs in dest_set:
            edge = {
                "from": _format_path_for_export(src_abs, base_dir),
                "to": _format_path_for_export(dest_abs, base_dir),
            }
            if include_absolute:
                edge["from_abs"] = str(src_abs)
                edge["to_abs"] = str(dest_abs)
            payload_edges.append(edge)

    payload_alias: Dict[str, Dict[str, Optional[str]]] = {}
    for file_abs, alias_map_for_file in alias_map.items():
        file_key = _format_path_for_export(file_abs, base_dir)
        payload_alias[file_key] = {}
        for alias, target_abs in alias_map_for_file.items():
            payload_alias[file_key][alias] = (
                _format_path_for_export(target_abs, base_dir) if target_abs else None
            )

    result = {
        "version": 1,
        "base_dir": str(base_dir.resolve()) if base_dir else None,
        "nodes": payload_nodes,
        "edges": payload_edges,
        "alias_map": payload_alias,
    }
    return result


def export_import_graph_json(
    graph: ImportGraph,
    alias_map: AliasResolutionMap,
    base_dir: Optional[Path] = None,
    include_absolute: bool = False,
    indent: int = 2,
) -> str:
    """Serialize the import dependency graph to a JSON string."""
    data = export_import_graph(graph, alias_map, base_dir=base_dir, include_absolute=include_absolute)
    return json.dumps(data, indent=indent)
