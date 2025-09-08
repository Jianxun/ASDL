"""
Dependency graph construction for the ASDL import system.

Builds an ImportGraph, alias resolution map, and loads dependencies using
the FileLoader while avoiding duplicate circular checks outside the loader.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

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

            # Check for circular dependency before using cache
            if resolved_path in loading_stack + [current_path]:
                cycle_stack = loading_stack + [current_path, resolved_path]
                diagnostics.append(self.diagnostics.create_circular_import_error(cycle_stack))
                # Do not proceed to load in cycle
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


