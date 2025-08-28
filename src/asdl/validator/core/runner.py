"""
Validator runner that orchestrates rule execution.
"""

from typing import Iterable, List, Optional, Tuple

from .types import ValidationContext, ModuleRule, FileRule
from .registry import default_rules
from ..diagnostics import create_validator_diagnostic
from ...data_structures import ASDLFile, Module, Instance
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

    # ---------------------------------------------------------------------
    # Backward-compatibility shim methods (preserve prior public API)
    # ---------------------------------------------------------------------

    def validate_port_mappings(self, instance_id: str, instance: Instance, module: Module) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []

        if not module.ports:
            if instance.mappings:
                mapped_ports = list(instance.mappings.keys())
                diagnostics.append(
                    create_validator_diagnostic(
                        "V0301",
                        instance_id=instance_id,
                        mapped_ports=mapped_ports,
                        module_name=instance.model,
                    )
                )
            return diagnostics

        valid_ports = set(module.ports.keys())
        mapped_ports = set(instance.mappings.keys()) if instance.mappings else set()
        invalid_ports = mapped_ports - valid_ports
        if invalid_ports:
            diagnostics.append(
                create_validator_diagnostic(
                    "V0302",
                    instance_id=instance_id,
                    invalid_ports=sorted(invalid_ports),
                    valid_ports=sorted(valid_ports),
                    module_name=instance.model,
                )
            )

        return diagnostics

    def validate_net_declarations(self, module: Module, module_name: str) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []

        if not module.instances:
            return diagnostics

        declared_nets = set()
        if module.ports:
            declared_nets.update(module.ports.keys())
        if module.internal_nets:
            declared_nets.update(module.internal_nets)

        undeclared_nets = set()
        for instance_id, instance in module.instances.items():
            if not instance.mappings:
                continue
            for port_name, net_name in instance.mappings.items():
                if net_name not in declared_nets:
                    undeclared_nets.add(net_name)

        if undeclared_nets:
            nets_list = ", ".join(f"'{net}'" for net in sorted(undeclared_nets))
            diagnostics.append(
                create_validator_diagnostic(
                    "V0401",
                    module_name=module_name,
                    nets_list=nets_list,
                )
            )

        return diagnostics

    def validate_parameter_overrides(self, instance_id: str, instance: Instance, module: Module) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []

        if not instance.parameters:
            return diagnostics

        is_hierarchical = bool(module.instances)
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
            return diagnostics

        module_parameters = set(module.parameters.keys()) if module.parameters else set()
        module_variables = set(module.variables.keys()) if module.variables else set()

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

        attempted_parameter_overrides = set(instance.parameters.keys()) - module_variables
        non_existent_parameters = attempted_parameter_overrides - module_parameters
        for param_name in sorted(non_existent_parameters):
            if module_parameters:
                available_params = ", ".join(f"'{param}'" for param in sorted(module_parameters))
                details = (
                    f"Instance '{instance_id}' attempts to override non-existent parameter '{param_name}' "
                    f"on module '{instance.model}'. Available parameters: {available_params}."
                )
            else:
                details = (
                    f"Instance '{instance_id}' attempts to override parameter '{param_name}' "
                    f"on module '{instance.model}', but module defines no parameters."
                )

            diagnostics.append(
                create_validator_diagnostic(
                    "V0305",
                    details=details,
                    location=instance,
                )
            )

        return diagnostics

    def validate_file_parameter_overrides(self, asdl_file: ASDLFile) -> List[Diagnostic]:
        ctx = ValidationContext(asdl_file)
        diagnostics: List[Diagnostic] = []
        for module_name, module in (asdl_file.modules or {}).items():
            if not module.instances:
                continue
            for instance_id, instance in (module.instances or {}).items():
                target_module = None
                if instance.model in (asdl_file.modules or {}):
                    target_module = asdl_file.modules[instance.model]
                if target_module:
                    diagnostics.extend(self.validate_parameter_overrides(instance_id, instance, target_module))
        return diagnostics

    def validate_unused_components(self, asdl_file: ASDLFile) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []

        used_modules = set()
        for module_name, module in (asdl_file.modules or {}).items():
            if module.instances:
                for instance in module.instances.values():
                    if instance.model in (asdl_file.modules or {}):
                        used_modules.add(instance.model)

        defined_modules = set((asdl_file.modules or {}).keys())
        unused_modules = defined_modules - used_modules

        if asdl_file.file_info.top_module:
            unused_modules.discard(asdl_file.file_info.top_module)

        if unused_modules:
            modules_list = ", ".join(f"'{module}'" for module in sorted(unused_modules))
            diagnostics.append(
                create_validator_diagnostic(
                    "V0601",
                    modules_list=modules_list,
                )
            )

        return diagnostics


