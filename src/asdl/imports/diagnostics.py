from __future__ import annotations

from typing import Iterable, Optional

from asdl.diagnostics import Diagnostic, Severity, SourceSpan, format_code

NO_SPAN_NOTE = "No source span available."
SOURCE = "import"

IMPORT_NOT_FOUND = format_code("AST", 10)
IMPORT_MALFORMED_PATH = format_code("AST", 11)
IMPORT_CYCLE = format_code("AST", 12)
DUPLICATE_NAMESPACE = format_code("AST", 13)
DUPLICATE_SYMBOL = format_code("AST", 14)
IMPORT_AMBIGUOUS = format_code("AST", 15)


def import_not_found(
    path: str, *, span: Optional[SourceSpan] = None, notes: Optional[Iterable[str]] = None
) -> Diagnostic:
    return _diagnostic(
        IMPORT_NOT_FOUND,
        f"Import path not found: {path}",
        span=span,
        notes=notes,
    )


def import_malformed_path(
    path: str, *, span: Optional[SourceSpan] = None, notes: Optional[Iterable[str]] = None
) -> Diagnostic:
    return _diagnostic(
        IMPORT_MALFORMED_PATH,
        f"Malformed import path: {path}",
        span=span,
        notes=notes,
    )


def import_cycle(chain: Iterable[str], *, span: Optional[SourceSpan] = None) -> Diagnostic:
    cycle = " -> ".join(chain)
    return _diagnostic(
        IMPORT_CYCLE,
        f"Import cycle detected: {cycle}",
        span=span,
    )


def duplicate_namespace(namespace: str, *, span: Optional[SourceSpan] = None) -> Diagnostic:
    return _diagnostic(
        DUPLICATE_NAMESPACE,
        f"Duplicate import namespace: {namespace}",
        span=span,
    )


def duplicate_symbol(name: str, *, span: Optional[SourceSpan] = None) -> Diagnostic:
    return _diagnostic(
        DUPLICATE_SYMBOL,
        f"Duplicate symbol in file: {name}",
        span=span,
    )


def ambiguous_import_path(
    path: str,
    matches: Iterable[str],
    *,
    span: Optional[SourceSpan] = None,
) -> Diagnostic:
    notes = [f"Match: {match}" for match in matches]
    return _diagnostic(
        IMPORT_AMBIGUOUS,
        f"Ambiguous import path: {path}",
        span=span,
        notes=notes,
    )


def _diagnostic(
    code: str,
    message: str,
    *,
    span: Optional[SourceSpan] = None,
    notes: Optional[Iterable[str]] = None,
) -> Diagnostic:
    note_list = list(notes) if notes else []
    if span is None:
        note_list.append(NO_SPAN_NOTE)
    if not note_list:
        note_list = None
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        message=message,
        primary_span=span,
        notes=note_list,
        source=SOURCE,
    )


__all__ = [
    "IMPORT_NOT_FOUND",
    "IMPORT_MALFORMED_PATH",
    "IMPORT_CYCLE",
    "DUPLICATE_NAMESPACE",
    "DUPLICATE_SYMBOL",
    "IMPORT_AMBIGUOUS",
    "import_not_found",
    "import_malformed_path",
    "import_cycle",
    "duplicate_namespace",
    "duplicate_symbol",
    "ambiguous_import_path",
]
