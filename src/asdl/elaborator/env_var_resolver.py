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

    def resolve_in_template(
        self,
        *,
        template: str,
        owner_name: str,
        owner_kind: str,  # "module" | "instance"
        locatable: Optional[Locatable] = None,
    ) -> Tuple[str, List]:
        """
        Resolve environment variables in a SPICE template string.

        Rules mirror resolve_in_parameters:
        - Only resolves exact tokens of the form `${VAR}` (full-string match is not required; tokens can appear within the template string).
        - If a `${VAR}` is found but the environment variable is missing, emit E0501 and leave the token unchanged.
        - If `$` appears in an invalid `${...}` format, emit E0502 and leave as-is.
        """
        diagnostics: List = []
        if not isinstance(template, str) or "$" not in template:
            return template, diagnostics

        # Replace all occurrences of ${VAR} while collecting diagnostics for missing vars
        def _replace(match: re.Match) -> str:
            var_name = match.group(1)
            env_value = os.environ.get(var_name)
            if env_value is None:
                diagnostics.append(
                    create_elaborator_diagnostic(
                        "E0501",
                        location=locatable,
                        var_name=var_name,
                        param_name="spice_template",
                        owner_name=owner_name,
                        owner_kind=owner_kind,
                    )
                )
                return match.group(0)
            return env_value

        # First pass: valid pattern replacements for any occurrence of ${VAR}
        any_valid_token = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
        new_template = any_valid_token.sub(_replace, template)

        # Second pass: if any remaining '$' patterns that look like `${...}` but invalid, flag E0502
        # Detect `${...}` with invalid identifier
        invalid_token_pattern = re.compile(r"\$\{([^}]*)\}")
        for invalid in invalid_token_pattern.findall(new_template):
            if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", invalid or ""):
                diagnostics.append(
                    create_elaborator_diagnostic(
                        "E0502",
                        location=locatable,
                        param_name="spice_template",
                        owner_name=owner_name,
                        owner_kind=owner_kind,
                    )
                )

        return new_template, diagnostics


