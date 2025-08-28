"""
Registry for assembling the default set of validator rules.
"""

from typing import List, Tuple

from .types import ModuleRule, FileRule
from ..rules.port_mapping import PortMappingRule
from ..rules.parameter_overrides import ParameterOverridesModuleRule, ParameterOverridesFileRule
from ..rules.net_declarations import NetDeclarationsRule
from ..rules.module_parameters import ModuleParametersRule
from ..rules.unused import UnusedModulesRule


def default_rules() -> Tuple[List[ModuleRule], List[FileRule]]:
    module_rules: List[ModuleRule] = [
        PortMappingRule(),
        NetDeclarationsRule(),
        ModuleParametersRule(),
        ParameterOverridesModuleRule(),
    ]

    file_rules: List[FileRule] = [
        UnusedModulesRule(),
        ParameterOverridesFileRule(),
    ]

    return module_rules, file_rules


