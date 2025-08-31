from typing import Dict, Any, Tuple, List, Optional
import os
import re

from ..data_structures import Locatable
from .diagnostics import create_elaborator_diagnostic


class EnvVarResolver:
    """
    Resolve environment variable references in parameter dictionaries.

    Rules:
    - Only resolves strings that exactly match the pattern `${VAR}` where VAR matches
      `[A-Za-z_][A-Za-z0-9_]*`.
    - Any other usage containing `$` or `${...}` is considered invalid format and emits
      E0502 (value left unchanged).
    - If `${VAR}` is valid but VAR is not set in the environment, emit E0501 (value left unchanged).
    - Non-string values are left unchanged.
    """

    _VALID_PATTERN = re.compile(r"^\$\{([A-Za-z_][A-Za-z0-9_]*)\}$")

    def resolve_in_parameters(
        self,
        *,
        parameters: Dict[str, Any],
        owner_name: str,
        owner_kind: str,  # "module" | "instance"
        locatable: Optional[Locatable] = None,
    ) -> Tuple[Dict[str, Any], List]:
        diagnostics = []
        if not parameters:
            return parameters, diagnostics

        resolved: Dict[str, Any] = {}
        for param_name, value in parameters.items():
            if isinstance(value, str):
                match = self._VALID_PATTERN.match(value)
                if match:
                    var_name = match.group(1)
                    env_value = os.environ.get(var_name)
                    if env_value is None:
                        diagnostics.append(
                            create_elaborator_diagnostic(
                                "E0501",
                                location=locatable,
                                var_name=var_name,
                                param_name=param_name,
                                owner_name=owner_name,
                                owner_kind=owner_kind,
                            )
                        )
                        resolved[param_name] = value
                    else:
                        resolved[param_name] = env_value
                elif "$" in value:
                    diagnostics.append(
                        create_elaborator_diagnostic(
                            "E0502",
                            location=locatable,
                            param_name=param_name,
                            owner_name=owner_name,
                            owner_kind=owner_kind,
                        )
                    )
                    resolved[param_name] = value
                else:
                    resolved[param_name] = value
            else:
                resolved[param_name] = value

        return resolved, diagnostics


