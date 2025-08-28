"""
Unused modules rule (V0601).
"""

from typing import List

from ..diagnostics import create_validator_diagnostic
from ..core.types import ValidationContext, FileRule
from ...diagnostics import Diagnostic


class UnusedModulesRule(FileRule):
    def validate_file(self, ctx: ValidationContext) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []

        used_modules = set()
        for module_name, module in ctx.asdl_file.modules.items():
            if module.instances:
                for instance in module.instances.values():
                    if instance.model in ctx.asdl_file.modules:
                        used_modules.add(instance.model)

        defined_modules = set(ctx.asdl_file.modules.keys())
        unused_modules = defined_modules - used_modules

        if ctx.asdl_file.file_info.top_module:
            unused_modules.discard(ctx.asdl_file.file_info.top_module)

        if unused_modules:
            modules_list = ", ".join(f"'{module}'" for module in sorted(unused_modules))
            diagnostics.append(
                create_validator_diagnostic(
                    "V0601",
                    modules_list=modules_list,
                )
            )

        return diagnostics


