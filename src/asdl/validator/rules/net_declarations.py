"""
Net declaration validation (V0401).
"""

from typing import List

from ..diagnostics import create_validator_diagnostic
from ..core.types import ValidationContext, ModuleRule
from ...diagnostics import Diagnostic


class NetDeclarationsRule(ModuleRule):
    def validate(self, ctx: ValidationContext, module_name: str, module) -> List[Diagnostic]:
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

        # TEMPORARILY SUPPRESSED - will refine later
        # if undeclared_nets:
        #     nets_list = ", ".join(f"'{net}'" for net in sorted(undeclared_nets))
        #     diagnostics.append(
        #         create_validator_diagnostic(
        #             "V0401",
        #             module_name=module_name,
        #             nets_list=nets_list,
        #         )
        #     )

        return diagnostics


