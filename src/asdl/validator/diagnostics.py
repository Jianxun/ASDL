"""
Validator diagnostics (XCCSS format) and helpers.

Code format: XCCSS where
  - X: Component prefix 'V' (Validator)
  - CC: Category (01 Syntax, 02 Schema, 03 Semantic, 04 Reference, 05 Type, 06 Style, 07 Extension, 08 Performance)
  - SS: Specific code within category
"""

from typing import Dict, Tuple, Optional

from ..diagnostics import Diagnostic, DiagnosticSeverity


# Diagnostic definitions for the Validator component
VALIDATOR_DIAGNOSTICS: Dict[str, Tuple[str, str]] = {
    # Semantic (V03xx) — port mapping and overrides
    "V0301": (
        "Invalid Port Mapping",
        "Instance '{instance_id}' maps to ports {mapped_ports}, but module '{module_name}' defines no ports.",
    ),
    "V0302": (
        "Invalid Port Mapping",
        "Instance '{instance_id}' maps to invalid ports: {invalid_ports}. Module '{module_name}' only defines ports: {valid_ports}.",
    ),
    "V0303": (
        "Invalid Parameter Override",
        "Instance '{instance_id}' attempts to override parameters {override_params} on hierarchical module '{module_name}'. Parameter overrides are only allowed for primitive modules (those with spice_template).",
    ),
    "V0304": (
        "Invalid Variable Override",
        "Instance '{instance_id}' attempts to override variable '{var_name}' on module '{module_name}'. Variables cannot be overridden in instances.",
    ),
    # Note: V0305 details vary depending on available parameters; allow free-form details injection
    "V0305": (
        "Invalid Parameter Override",
        "{details}",
    ),

    # Reference (V04xx) — undeclared nets
    "V0401": (
        "Undeclared Nets",
        "In module '{module_name}', undeclared nets used in instance mappings: {nets_list}. These nets are not declared as ports or internal nets.",
    ),

    # Schema (V02xx) — invalid declarations on hierarchical modules
    "V0201": (
        "Invalid Module Parameter Declaration",
        "Hierarchical module '{module_name}' declares parameters {param_names}. Hierarchical modules should only use 'variables' for internal implementation details. Use 'variables' instead of 'parameters' or convert to primitive module with spice_template.",
    ),

    # Style/quality warnings (V06xx) — unused modules
    "V0601": (
        "Unused Modules",
        "Unused modules detected: {modules_list}. These modules are defined but never instantiated.",
    ),
}

# Per-code severity overrides when category default doesn't match intended level
_VALIDATOR_SEVERITY_OVERRIDES: Dict[str, DiagnosticSeverity] = {
    # Undeclared nets should be a WARNING in our validator policy
    "V0401": DiagnosticSeverity.WARNING,
}


def _severity_for_code(code: str) -> DiagnosticSeverity:
    """Derive severity from the category digits per XCCSS design decisions."""
    if code in _VALIDATOR_SEVERITY_OVERRIDES:
        return _VALIDATOR_SEVERITY_OVERRIDES[code]
    if len(code) != 5 or code[0] != "V" or not code[1:].isdigit():
        # Fallback to ERROR for malformed codes
        return DiagnosticSeverity.ERROR

    category = int(code[1:3])
    if 1 <= category <= 5:
        return DiagnosticSeverity.ERROR
    if 6 <= category <= 7:
        return DiagnosticSeverity.WARNING
    if category == 8:
        return DiagnosticSeverity.INFO
    return DiagnosticSeverity.ERROR


def create_validator_diagnostic(
    code: str,
    *,
    location=None,
    suggestion: Optional[str] = None,
    **template_params,
) -> Diagnostic:
    """Create a Diagnostic for the Validator using XCCSS definitions.

    Args:
        code: XCCSS diagnostic code (e.g., 'V0301')
        location: Optional location info implementing Locatable
        suggestion: Optional suggestion text
        **template_params: Named parameters to fill into the message template
    """
    if code not in VALIDATOR_DIAGNOSTICS:
        title = "Unknown Validator Diagnostic"
        details_template = "Diagnostic code {code} is not defined."
    else:
        title, details_template = VALIDATOR_DIAGNOSTICS[code]

    try:
        details = details_template.format(**template_params)
    except Exception:
        # Guard against formatting errors; include raw params for debugging
        details = f"{details_template} [params={template_params}]"

    return Diagnostic(
        code=code,
        title=title,
        details=details,
        severity=_severity_for_code(code),
        location=location,
        suggestion=suggestion,
    )




