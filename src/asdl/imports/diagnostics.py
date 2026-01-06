from __future__ import annotations

from asdl.ast.location import Locatable
from asdl.diagnostics import Diagnostic, Severity, format_code

NO_SPAN_NOTE = "No source span available."

IMPORT_PATH_NOT_FOUND = format_code("AST", 10)
MALFORMED_IMPORT_PATH = format_code("AST", 11)
IMPORT_CYCLE = format_code("AST", 12)
DUPLICATE_NAMESPACE = format_code("AST", 13)
DUPLICATE_SYMBOL = format_code("AST", 14)


def _diagnostic(
    code: str,
    message: str,
    severity: Severity,
    loc: Locatable | None = None,
) -> Diagnostic:
    span = loc.to_source_span() if loc is not None else None
    notes = None if span is not None else [NO_SPAN_NOTE]
    return Diagnostic(
        code=code,
        severity=severity,
        message=message,
        primary_span=span,
        notes=notes,
        source="imports",
    )


__all__ = [
    "IMPORT_PATH_NOT_FOUND",
    "MALFORMED_IMPORT_PATH",
    "IMPORT_CYCLE",
    "DUPLICATE_NAMESPACE",
    "DUPLICATE_SYMBOL",
    "_diagnostic",
]
