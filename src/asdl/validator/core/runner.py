"""
Validator runner that orchestrates rule execution.
"""

from typing import Iterable, List, Optional, Tuple

from .types import ValidationContext, ModuleRule, FileRule
from .registry import default_rules
from ...data_structures import ASDLFile
from ...diagnostics import Diagnostic


class ASDLValidator:
    def __init__(
        self,
        *,
        module_rules: Optional[Iterable[ModuleRule]] = None,
        file_rules: Optional[Iterable[FileRule]] = None,
    ) -> None:
        if module_rules is None or file_rules is None:
            default_module_rules, default_file_rules = default_rules()
            self._module_rules: Tuple[ModuleRule, ...] = tuple(module_rules or default_module_rules)
            self._file_rules: Tuple[FileRule, ...] = tuple(file_rules or default_file_rules)
        else:
            self._module_rules = tuple(module_rules)
            self._file_rules = tuple(file_rules)

    def validate_file(self, asdl_file: ASDLFile) -> List[Diagnostic]:
        ctx = ValidationContext(asdl_file)
        diagnostics: List[Diagnostic] = []

        for module_name, module in (asdl_file.modules or {}).items():
            for rule in self._module_rules:
                diagnostics.extend(rule.validate(ctx, module_name, module))

        for rule in self._file_rules:
            diagnostics.extend(rule.validate_file(ctx))

        return diagnostics


