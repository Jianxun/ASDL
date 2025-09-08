"""
Module flattening for the ASDL import system.

Rewrites instance model references and merges modules from imported files
according to precedence policy. Emits a warning diagnostic on conflicts
when local-wins is active. Deterministic sorting is intentionally skipped
per current scope.
"""

from dataclasses import replace
from pathlib import Path
from typing import Dict, List, Tuple

from ...data_structures import ASDLFile
from ...diagnostics import Diagnostic, DiagnosticSeverity
from .policies import PrecedencePolicy, FlattenOptions


class Flattener:
    """Flattens modules into a single ASDLFile according to policy/options."""

    def __init__(self, precedence: PrecedencePolicy = PrecedencePolicy.LOCAL_WINS, options: FlattenOptions = FlattenOptions()):
        self.precedence = precedence
        self.options = options

    def flatten(self, main_file: ASDLFile, loaded_files: Dict[Path, ASDLFile]) -> Tuple[ASDLFile, List[Diagnostic]]:
        diagnostics: List[Diagnostic] = []

        def _rewrite_module_instance_models(module, file_model_alias):
            if module.instances is None:
                return module
            new_instances = {}
            for inst_id, inst in module.instances.items():
                model_name = inst.model
                # 1) Strip qualified import alias (e.g., op.mod -> mod)
                if isinstance(model_name, str) and '.' in model_name:
                    model_name = model_name.split('.', 1)[1]
                # 2) Apply file-local model_alias mapping
                if file_model_alias and model_name in file_model_alias:
                    qualified_ref = file_model_alias[model_name]
                    if '.' in qualified_ref:
                        model_name = qualified_ref.split('.', 1)[1]
                    else:
                        model_name = qualified_ref
                new_instances[inst_id] = replace(inst, model=model_name)
            return replace(module, instances=new_instances)

        # Start with main file modules (apply rewriting)
        all_modules = {}
        if main_file.modules:
            for name, module in main_file.modules.items():
                all_modules[name] = _rewrite_module_instance_models(module, main_file.model_alias)

        # Merge imported modules
        for imported_file in loaded_files.values():
            if not imported_file.modules:
                continue
            for module_name, module in imported_file.modules.items():
                rewritten = _rewrite_module_instance_models(module, imported_file.model_alias)
                if module_name in all_modules:
                    if self.precedence == PrecedencePolicy.LOCAL_WINS:
                        # Emit a warning about shadowing and keep local
                        diagnostics.append(Diagnostic(
                            code="E0601",
                            title="Imported Module Shadowed by Local",
                            details=f"Module '{module_name}' from import is shadowed by local module with the same name.",
                            severity=DiagnosticSeverity.WARNING,
                            suggestion="Rename the imported or local module to avoid ambiguity if unintended."
                        ))
                        continue
                    # IMPORT_WINS: override local
                all_modules[module_name] = rewritten

        # Build flattened file and optionally drop metadata
        flattened = replace(
            main_file,
            modules=all_modules,
            imports=None if self.options.drop_metadata else main_file.imports,
            model_alias=None if self.options.drop_metadata else main_file.model_alias,
        )
        return flattened, diagnostics


