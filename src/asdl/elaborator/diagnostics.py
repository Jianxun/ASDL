"""
Elaborator diagnostics (XCCSS-style) and helpers.

This module centralizes Elaborator diagnostic definitions and provides a
factory to create Diagnostics with severities derived from category digits.

Codes follow XCCSS where:
  - X: Component prefix 'E' (Elaborator)
  - CC: Category (01 Syntax, 02 Schema, 03 Semantic, 04 Reference, 05 Type, 06 Style, 07 Extension, 08 Performance)
  - SS: Specific code within category

Note: Existing short-form E10x pattern-expansion codes are still emitted
elsewhere and will be migrated later.
"""

from typing import Dict, Tuple, Optional

from ..diagnostics import Diagnostic, DiagnosticSeverity


# Diagnostic definitions for the Elaborator component
ELABORATOR_DIAGNOSTICS: Dict[str, Tuple[str, str]] = {
    # Syntax (E01xx) — pattern syntax issues
    "E0101": (
        "Empty Literal Pattern",
        "Pattern in '{name}' is empty.",
    ),
    "E0102": (
        "Single-Item Pattern",
        "Pattern in '{name}' contains only a single item.",
    ),
    "E0103": (
        "Empty Pattern Item",
        "Pattern in '{name}' contains only empty items.",
    ),
    "E0104": (
        "Invalid Bus Range",
        "Bus range '{name}' has identical MSB and LSB.",
    ),
    "E0105": (
        "Mixed Pattern Types",
        "'{name}' contains both a literal ('<>') and bus ('[]') pattern.",
    ),

    # Semantic (E03xx) — pattern semantics
    "E0301": (
        "Pattern Count Mismatch",
        "Pattern item counts must match: {expected} vs {found}.",
    ),
    "E0302": (
        "Unmatched Net Pattern",
        "Net pattern '{net_name}' requires matching port pattern or instance pattern.",
    ),

    # Reference (E04xx)
    "E0402": (
        "Undefined Variable",
        "Parameter '{param_name}' in instance '{instance_name}' references undefined variable '{var_name}'. Available: {available}",
    ),

    # Type (E05xx) — environment variable handling
    "E0501": (
        "Environment Variable Not Found",
        "Environment variable ${var_name} not found in parameter '{param_name}' on {owner_kind} '{owner_name}'.",
    ),
    "E0502": (
        "Invalid Environment Variable Format",
        "Invalid environment variable format in parameter '{param_name}' on {owner_kind} '{owner_name}': expected ${VAR} format.",
    ),
}


def _severity_for_code(code: str) -> DiagnosticSeverity:
    """Derive severity from the category digits per XCCSS design decisions."""
    try:
        if len(code) == 5 and code[0] == "E" and code[1:].isdigit():
            category = int(code[1:3])
            if 1 <= category <= 5:
                return DiagnosticSeverity.ERROR
            if 6 <= category <= 7:
                return DiagnosticSeverity.WARNING
            if category == 8:
                return DiagnosticSeverity.INFO
    except Exception:
        pass
    # Default to ERROR for unknown/malformed codes and legacy short-form
    return DiagnosticSeverity.ERROR


def create_elaborator_diagnostic(
    code: str,
    *,
    location=None,
    suggestion: Optional[str] = None,
    **template_params,
) -> Diagnostic:
    """Create a Diagnostic for the Elaborator using XCCSS definitions.

    Args:
        code: XCCSS diagnostic code (e.g., 'E0501')
        location: Optional location info implementing Locatable
        suggestion: Optional suggestion text
        **template_params: Named parameters to fill into the message template
    """
    # Backward-compatibility mapping from legacy short-form codes
    LEGACY_MAP = {
        "E100": "E0101",
        "E101": "E0102",
        "E104": "E0104",
        "E105": "E0301",
        "E106": "E0302",
        "E107": "E0103",
        "E108": "E0402",
        "E103": "E0105",
    }
    if code in LEGACY_MAP:
        code = LEGACY_MAP[code]

    if code not in ELABORATOR_DIAGNOSTICS:
        title = "Unknown Elaborator Diagnostic"
        details_template = "Diagnostic code {code} is not defined."
    else:
        title, details_template = ELABORATOR_DIAGNOSTICS[code]

    try:
        details = details_template.format(**template_params)
    except Exception:
        details = f"{details_template} [params={template_params}]"

    return Diagnostic(
        code=code,
        title=title,
        details=details,
        severity=_severity_for_code(code),
        location=location,
        suggestion=suggestion,
    )


