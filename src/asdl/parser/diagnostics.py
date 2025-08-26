"""
Parser diagnostics (XCCSS format) and helpers.

Code format: XCCSS where
  - X: Component prefix 'P' (Parser)
  - CC: Category (01 Syntax, 02 Schema, 03 Semantic, 04 Reference, 05 Type, 06 Style, 07 Extension, 08 Performance)
  - SS: Specific code within category

This module provides a centralized place to define Parser diagnostic
titles and detail templates, plus a helper to create Diagnostics with
severity derived from the XCCSS category. Existing parser code can
migrate to use `create_parser_diagnostic` incrementally.
"""

from typing import Dict, Tuple, Optional

from ..diagnostics import Diagnostic, DiagnosticSeverity


# Diagnostic definitions for the Parser component
PARSER_DIAGNOSTICS: Dict[str, Tuple[str, str]] = {
    # Syntax (P01xx)
    "P100": ("Invalid YAML Syntax", "The file could not be parsed because of a syntax error: {problem}"),
    "P101": ("Invalid Root Type", "The root of an ASDL file must be a dictionary (a set of key-value pairs)."),

    # Schema (P02xx)
    "P102": ("Missing Required Section", "'{section}' is a mandatory section and must be present at the top level of the ASDL file."),
    "P103": ("Invalid Section Type", "The '{section}' section must be a dictionary (mapping), but found {found_type}."),
    "P104": ("Missing Required Field", "{context} is missing the required '{field}' field."),
    "P105": ("Port Parsing Error", "An error occurred while parsing port '{port_name}': {error}"),

    # Semantic (P03xx)
    "P107": ("Module Type Conflict", "Module '{module}' cannot have both 'spice_template' and 'instances'."),
    "P108": ("Incomplete Module Definition", "Module '{module}' must have either 'spice_template' or 'instances'."),

    # Extension (P07xx)
    "P200": ("Unknown Top-Level Section", "The top-level section '{section}' is not a recognized ASDL section."),
    "P201": ("Unknown Field", "{context} contains unknown field '{field_name}' which is not a recognized field."),

    # Style (P06xx) — dual syntax warnings
    "P301": ("Dual Parameter Syntax", "{context} contains both 'parameters' and 'params' fields. Using 'parameters' and ignoring 'params'."),
    "P302": ("Dual Variables Syntax", "{context} contains both 'variables' and 'vars' fields. Using 'variables' and ignoring 'vars'."),

    # Type (P05xx) — imports simplified path validation
    "P0501": ("Invalid Import Path Type", "Import '{alias}' path must be a string, got {found_type}."),
    "P0502": ("Invalid Import File Extension", "Import '{alias}' must reference a .asdl file, got '{path}'."),

    # Type (P05xx) — model_alias format
    "P0503": ("Invalid Model Alias Format", "Model alias '{alias}' must follow 'library.module' format; {details}"),
}


def _severity_for_code(code: str) -> DiagnosticSeverity:
    """Derive severity from the category digits per XCCSS design decisions."""
    if len(code) != 5 or code[0] != "P" or not code[1:].isdigit():
        return DiagnosticSeverity.ERROR
    category = int(code[1:3])
    if 1 <= category <= 5:
        return DiagnosticSeverity.ERROR
    if 6 <= category <= 7:
        return DiagnosticSeverity.WARNING
    if category == 8:
        return DiagnosticSeverity.INFO
    return DiagnosticSeverity.ERROR


def create_parser_diagnostic(
    code: str,
    *,
    location=None,
    suggestion: Optional[str] = None,
    **template_params,
) -> Diagnostic:
    """Create a Diagnostic for the Parser using XCCSS definitions.

    Args:
        code: XCCSS diagnostic code (e.g., 'P0304')
        location: Optional location info implementing Locatable
        suggestion: Optional suggestion text
        **template_params: Named parameters to fill into the message template
    """
    if code not in PARSER_DIAGNOSTICS:
        title = "Unknown Parser Diagnostic"
        details_template = "Diagnostic code {code} is not defined."
    else:
        title, details_template = PARSER_DIAGNOSTICS[code]

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


