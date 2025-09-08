"""
Coordinator that orchestrates the ASDL import resolution flow.

Flow: parse main (provided), resolve paths, build dependency graph, validate,
and flatten using precedence policy and options.
"""

from pathlib import Path
from typing import List, Optional, Tuple

from ...data_structures import ASDLFile
from ...parser import ASDLParser
from ...diagnostics import Diagnostic
from ...timing import time_block
from ...logging_utils import get_logger
from .path_resolver import PathResolver
from .file_loader import FileLoader
from .dependency_graph import DependencyGraphBuilder
from .reference_validator import ReferenceValidator
from .flattener import Flattener
from .policies import PrecedencePolicy, FlattenOptions


class ImportCoordinator:
    """High-level API that mirrors the old ImportResolver interface."""

    def __init__(
        self,
        parser: Optional[ASDLParser] = None,
        path_resolver: Optional[PathResolver] = None,
        file_loader: Optional[FileLoader] = None,
        precedence: PrecedencePolicy = PrecedencePolicy.LOCAL_WINS,
        flatten_options: Optional[FlattenOptions] = None,
    ) -> None:
        self.parser = parser or ASDLParser()
        self.path_resolver = path_resolver or PathResolver()
        self.file_loader = file_loader or FileLoader(self.parser)
        self.graph_builder = DependencyGraphBuilder(self.path_resolver, self.file_loader)
        self.validator = ReferenceValidator()
        self.flattener = Flattener(precedence=precedence, options=flatten_options or FlattenOptions())

    def resolve_imports(self, main_file_path: Path, search_paths: Optional[List[Path]] = None) -> Tuple[Optional[ASDLFile], List[Diagnostic]]:
        log = get_logger("elaborator.imports")
        diagnostics: List[Diagnostic] = []

        # Normalize main file path to absolute for consistent identity across components
        main_file_path = main_file_path.resolve()

        # Parse main file
        log.debug(f"Parsing main file: {main_file_path}")
        main_file, parse_diags = self.parser.parse_file(str(main_file_path))
        diagnostics.extend(parse_diags)
        if main_file is None:
            return None, diagnostics

        # Build dependency graph
        with time_block(log, "Build dependency graph"):
            graph, alias_map, loaded_files, graph_diags = self.graph_builder.build(main_file, main_file_path, search_paths)
        diagnostics.extend(graph_diags)

        # Validate references/aliases
        with time_block(log, "Validate imports/aliases"):
            validation_diags = self.validator.validate(main_file, main_file_path, loaded_files, alias_map)
        diagnostics.extend(validation_diags)

        # Flatten
        with time_block(log, "Flatten modules"):
            flattened, flat_diags = self.flattener.flatten(main_file, loaded_files)
        diagnostics.extend(flat_diags)

        return flattened, diagnostics


