"""
Compatibility wrapper around the new ImportCoordinator.

Maintains the old ImportResolver API while delegating to the coordinator.
"""

from pathlib import Path
from typing import List, Optional, Tuple

from ...data_structures import ASDLFile
from ...diagnostics import Diagnostic
from ...parser import ASDLParser
from .coordinator import ImportCoordinator


class ImportResolver:
    """Backwards-compatible facade that delegates to ImportCoordinator."""

    def __init__(self, parser: Optional[ASDLParser] = None):
        self._coordinator = ImportCoordinator(parser=parser)

    def resolve_imports(
        self, main_file_path: Path, search_paths: Optional[List[Path]] = None
    ) -> Tuple[Optional[ASDLFile], List[Diagnostic]]:
        return self._coordinator.resolve_imports(main_file_path, search_paths)

    def get_loaded_file_info(self):
        # Coordinator proxies to FileLoader internally; expose cache stats through coordinator's loader
        return self._coordinator.file_loader.get_cache_stats()

    def clear_cache(self) -> None:
        self._coordinator.file_loader.clear_cache()