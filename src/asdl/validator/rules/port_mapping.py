"""
Port mapping validation rules (V0301, V0302).
"""

from typing import List

from ..diagnostics import create_validator_diagnostic
from ..core.types import ValidationContext, ModuleRule
from ...diagnostics import Diagnostic


class PortMappingRule(ModuleRule):
    def validate(self, ctx: ValidationContext, module_name: str, module) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []

        if not module.instances:
            return diagnostics

        for instance_id, instance in module.instances.items():
            # If target model is a module in this file, validate against its ports
            if instance.model in ctx.asdl_file.modules:
                target_module = ctx.asdl_file.modules[instance.model]

                # Module has no ports, but instance has mappings
                if not target_module.ports:
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
                    continue

                valid_ports = set(target_module.ports.keys())
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


