from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from asdl.ast.location import Locatable
from asdl.diagnostics import Diagnostic, Severity, format_code

NO_SPAN_NOTE = "No source span available."

IMPORT_PATH_MISSING = format_code("AST", 10)
IMPORT_PATH_MALFORMED = format_code("AST", 11)
IMPORT_PATH_AMBIGUOUS = format_code("AST", 15)


def import_path_missing(path: str, loc: Optional[Locatable] = None) -> Diagnostic:
    return _diagnostic(IMPORT_PATH_MISSING, f"Import path not found: {path}", loc)


def import_path_malformed(
    path: str, reason: Optional[str] = None, loc: Optional[Locatable] = None
) -> Diagnostic:
    message = f"Malformed import path '{path}'."
    if reason:
        message = f"{message} {reason}"
    return _diagnostic(IMPORT_PATH_MALFORMED, message, loc)


def import_path_ambiguous(
    path: str, matches: Iterable[Path], loc: Optional[Locatable] = None
) -> Diagnostic:
    ordered = [str(match) for match in matches]
    notes = ["Matches (root order):", *ordered]
    return _diagnostic(
        IMPORT_PATH_AMBIGUOUS,
        f"Ambiguous import path '{path}'.",
        loc,
        notes=notes,
    )


def _diagnostic(
    code: str,
    message: str,
    loc: Optional[Locatable],
    *,
    notes: Optional[list[str]] = None,
) -> Diagnostic:
    span = loc.to_source_span() if loc is not None else None
    note_list = list(notes) if notes else []
    if span is None:
        note_list = [NO_SPAN_NOTE, *note_list]
    notes_payload = note_list or None
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        message=message,
        primary_span=span,
        notes=notes_payload,
        source="imports",
    )


__all__ = [
    "IMPORT_PATH_AMBIGUOUS",
    "IMPORT_PATH_MALFORMED",
    "IMPORT_PATH_MISSING",
    "import_path_ambiguous",
    "import_path_malformed",
    "import_path_missing",
]
