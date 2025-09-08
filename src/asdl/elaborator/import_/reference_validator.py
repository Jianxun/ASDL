"""
Reference validation for the ASDL import system.

Validates qualified instance references (E0443/E0444) and leverages
the existing AliasResolver for model_alias validation.
Fixes alias-usage tracking scoping.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from ...data_structures import ASDLFile
from ...diagnostics import Diagnostic
from .alias_resolver import AliasResolver
from .diagnostics import ImportDiagnostics


class ReferenceValidator:
    """Validates instance model references and model_alias definitions."""

    def __init__(self, alias_resolver: Optional[AliasResolver] = None, diagnostics: Optional[ImportDiagnostics] = None) -> None:
        self.alias_resolver = alias_resolver or AliasResolver()
        self.diagnostics = diagnostics or ImportDiagnostics()

    def validate(
        self,
        main_file: ASDLFile,
        main_file_path: Path,
        loaded_files: Dict[Path, ASDLFile],
        alias_resolution_map: Dict[Path, Dict[str, Optional[Path]]],
        emit_unused_warnings: bool = False,
    ) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []

        # 1) Validate model_alias definitions using existing logic
        diagnostics.extend(self.alias_resolver.validate_model_aliases(main_file, loaded_files))

        # 2) Validate qualified references used by instances across main + imports
        files_to_scan: List[Tuple[Path, ASDLFile]] = [(main_file_path, main_file)]
        files_to_scan.extend(list(loaded_files.items()))

        used_import_aliases_by_file: Dict[Path, Set[str]] = {}
        used_model_aliases_by_file: Dict[Path, Set[str]] = {}

        for file_path, asdl_file in files_to_scan:
            if not asdl_file.modules:
                continue
            imports_for_file: Dict[str, str] = asdl_file.imports or {}
            available_imports = list(imports_for_file.keys())
            alias_map_for_file = alias_resolution_map.get(file_path, {})
            used_import_aliases: Set[str] = set()
            used_model_aliases: Set[str] = set()

            for module in asdl_file.modules.values():
                instances = getattr(module, "instances", None)
                if not instances:
                    continue
                for inst in instances.values():
                    model_ref = getattr(inst, "model", None)
                    # Track model_alias usage when unqualified and present
                    if (
                        isinstance(model_ref, str)
                        and "." not in model_ref
                        and asdl_file.model_alias
                        and model_ref in asdl_file.model_alias
                    ):
                        used_model_aliases.add(model_ref)
                        continue

                    if not isinstance(model_ref, str) or "." not in model_ref:
                        continue

                    # Qualified reference "alias.module"
                    alias, module_name = model_ref.split(".", 1)
                    if alias not in imports_for_file:
                        diagnostics.append(
                            self.diagnostics.create_import_alias_not_found_error(
                                alias, model_ref, available_imports
                            )
                        )
                        continue

                    used_import_aliases.add(alias)
                    # Resolve to imported file via alias map
                    resolved_path = alias_map_for_file.get(alias)
                    imported_file = loaded_files.get(resolved_path) if resolved_path else None
                    available_modules: List[str] = []
                    if imported_file and imported_file.modules:
                        available_modules = list(imported_file.modules.keys())
                    if imported_file is None or module_name not in (imported_file.modules or {}):
                        import_file_path = resolved_path if resolved_path else Path(imports_for_file[alias])
                        diagnostics.append(
                            self.diagnostics.create_module_not_found_error(
                                module_name, alias, import_file_path, available_modules
                            )
                        )

            used_import_aliases_by_file[file_path] = used_import_aliases
            used_model_aliases_by_file[file_path] = used_model_aliases

        # 3) Optional unused warnings (main file only)
        if emit_unused_warnings:
            main_used_imports = used_import_aliases_by_file.get(main_file_path, set())
            main_used_model_aliases = used_model_aliases_by_file.get(main_file_path, set())
            if main_file.imports:
                for imp_alias in main_file.imports.keys():
                    if imp_alias not in main_used_imports:
                        diagnostics.append(self.diagnostics.create_unused_import_warning(imp_alias))
            if main_file.model_alias:
                for local_alias in main_file.model_alias.keys():
                    if local_alias not in main_used_model_aliases:
                        diagnostics.append(self.diagnostics.create_unused_model_alias_warning(local_alias))

        return diagnostics


