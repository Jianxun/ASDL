from __future__ import annotations

from typing import Optional

from asdl.ast.location import Locatable
from asdl.diagnostics import Diagnostic, Severity, format_code

NO_SPAN_NOTE = "No source span available."

IMPORT_PATH_MISSING = format_code("AST", 10)
IMPORT_PATH_MALFORMED = format_code("AST", 11)


def import_path_missing(path: str, loc: Optional[Locatable] = None) -> Diagnostic:
    return _diagnostic(IMPORT_PATH_MISSING, f"Import path not found: {path}", loc)


def import_path_malformed(
    path: str, reason: Optional[str] = None, loc: Optional[Locatable] = None
) -> Diagnostic:
    message = f"Malformed import path '{path}'."
    if reason:
        message = f"{message} {reason}"
    return _diagnostic(IMPORT_PATH_MALFORMED, message, loc)


def _diagnostic(code: str, message: str, loc: Optional[Locatable]) -> Diagnostic:
    span = loc.to_source_span() if loc is not None else None
    notes = None if span is not None else [NO_SPAN_NOTE]
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        message=message,
        primary_span=span,
        notes=notes,
        source="imports",
    )


__all__ = [
    "IMPORT_PATH_MALFORMED",
    "IMPORT_PATH_MISSING",
    "import_path_malformed",
    "import_path_missing",
]
