"""
Generator diagnostics (XCCSS format) and helpers.

Code format: XCCSS where
  - X: Component prefix 'G' (Generator)
  - CC: Category (01 Syntax, 02 Schema, 03 Semantic, 04 Reference, 05 Type, 06 Style, 07 Extension, 08 Performance)
  - SS: Specific code within category
"""

from typing import Dict, Tuple, Optional

from ..diagnostics import Diagnostic, DiagnosticSeverity


# Diagnostic definitions for the Generator component
GENERATOR_DIAGNOSTICS: Dict[str, Tuple[str, str]] = {
    # Semantic errors (G03xx)
    "G0301": (
        "Cannot Generate SPICE",
        "Cannot generate SPICE for incomplete module '{module}'.",
    ),
    "G0302": (
        "Missing PDK Reference",
        "Primitive module '{module}' missing PDK reference for SPICE generation.",
    ),
    "G0305": (
        "Unresolved Template Placeholder",
        "Generated SPICE contains unresolved placeholders: {placeholders}. These indicate missing parameter or variable definitions that would cause SPICE simulation to fail.",
    ),
    "G0401": (
        "Unknown Model Reference",
        "Instance references unknown model '{model}'.",
    ),

    # Type errors (G05xx)
    "G0501": (
        "Unsupported Output Format",
        "Output format '{format}' is not supported by the generator.",
    ),
    "G0502": (
        "Template Processing Error",
        "Error processing SPICE template: {error}.",
    ),
}


def _severity_for_code(code: str) -> DiagnosticSeverity:
    """Derive severity from the category digits per XCCSS design decisions."""
    if len(code) != 5 or code[0] != "G" or not code[1:].isdigit():
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


def create_generator_diagnostic(
    code: str,
    *,
    location=None,
    suggestion: Optional[str] = None,
    **template_params,
) -> Diagnostic:
    """Create a Diagnostic for the Generator using XCCSS definitions.

    Args:
        code: XCCSS diagnostic code (e.g., 'G0305')
        location: Optional location info implementing Locatable
        suggestion: Optional suggestion text
        **template_params: Named parameters to fill into the message template
    """
    if code not in GENERATOR_DIAGNOSTICS:
        title = "Unknown Generator Diagnostic"
        details_template = "Diagnostic code {code} is not defined."
    else:
        title, details_template = GENERATOR_DIAGNOSTICS[code]

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


