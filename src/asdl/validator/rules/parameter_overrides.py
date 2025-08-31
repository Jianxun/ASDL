"""
Parameter override rules (V0303, V0304, V0305) and file-wide aggregation.
"""

from typing import List

from ..diagnostics import create_validator_diagnostic
from ..core.types import ValidationContext, ModuleRule, FileRule
from ...diagnostics import Diagnostic


class ParameterOverridesModuleRule(ModuleRule):
    def validate(self, ctx: ValidationContext, module_name: str, module) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []

        if not module.instances:
            return diagnostics

        for instance_id, instance in module.instances.items():
            # Resolve target module if the instance references a module in-file
            target_module = ctx.asdl_file.modules.get(instance.model)
            if not target_module:
                # Device models (primitive external) are allowed; no validation here
                continue

            if not instance.parameters:
                continue

            is_primitive = bool(target_module.spice_template)
            is_hierarchical = bool(target_module.instances)

            if is_hierarchical:
                override_params = list(instance.parameters.keys())
                diagnostics.append(
                    create_validator_diagnostic(
                        "V0303",
                        instance_id=instance_id,
                        override_params=override_params,
                        module_name=instance.model,
                        location=instance,
                    )
                )
                # Skip further checks for hierarchical
                continue

            module_parameters = set(target_module.parameters.keys()) if target_module.parameters else set()
            module_variables = set(target_module.variables.keys()) if target_module.variables else set()

            # Variable overrides never allowed
            attempted_variable_overrides = set(instance.parameters.keys()) & module_variables
            for var_name in sorted(attempted_variable_overrides):
                diagnostics.append(
                    create_validator_diagnostic(
                        "V0304",
                        instance_id=instance_id,
                        var_name=var_name,
                        module_name=instance.model,
                        location=instance,
                    )
                )

            # Only existing module parameters can be overridden
            attempted_parameter_overrides = set(instance.parameters.keys()) - module_variables
            non_existent_parameters = attempted_parameter_overrides - module_parameters
            for param_name in sorted(non_existent_parameters):
                if module_parameters:
                    available_params = ", ".join(f"'{param}'" for param in sorted(module_parameters))
                    details = (f"Instance '{instance_id}' attempts to override non-existent parameter '{param_name}' "
                               f"on module '{instance.model}'. Available parameters: {available_params}.")
                else:
                    details = (f"Instance '{instance_id}' attempts to override parameter '{param_name}' "
                               f"on module '{instance.model}', but module defines no parameters.")

                diagnostics.append(
                    create_validator_diagnostic(
                        "V0305",
                        details=details,
                        location=instance,
                    )
                )

        return diagnostics


class ParameterOverridesFileRule(FileRule):
    def validate_file(self, ctx: ValidationContext) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []
        # File-wide aggregation is already handled by module rule iterating all instances.
        # Kept for parity with previous API and future cross-module checks.
        for module_name, module in ctx.asdl_file.modules.items():
            if not module.instances:
                continue
            diagnostics.extend(ParameterOverridesModuleRule().validate(ctx, module_name, module))
        return diagnostics


