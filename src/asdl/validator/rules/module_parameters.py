"""
Module parameter field rules (V0201).
"""

from typing import List

from ..diagnostics import create_validator_diagnostic
from ..core.types import ValidationContext, ModuleRule
from ...diagnostics import Diagnostic


class ModuleParametersRule(ModuleRule):
    def validate(self, ctx: ValidationContext, module_name: str, module) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []

        is_hierarchical = bool(module.instances)
        has_parameters = bool(module.parameters)

        if is_hierarchical and has_parameters:
            param_names = list(module.parameters.keys())
            diagnostics.append(
                create_validator_diagnostic(
                    "V0201",
                    module_name=module_name,
                    param_names=param_names,
                    location=module,
                )
            )

        return diagnostics


