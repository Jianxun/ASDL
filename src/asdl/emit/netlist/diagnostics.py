from __future__ import annotations

from typing import Iterable

try:
    from xdsl.dialects.builtin import FileLineColLoc, LocationAttr
except ModuleNotFoundError:
    FileLineColLoc = None

    class LocationAttr:
        """Fallback xdsl LocationAttr when xdsl is unavailable."""

        pass

from asdl.diagnostics import Diagnostic, Severity, SourcePos, SourceSpan, format_code
from asdl.diagnostics.collector import DiagnosticCollector

NO_SPAN_NOTE = "No source span available."

MISSING_TOP = format_code("EMIT", 1)
UNKNOWN_INSTANCE_PARAM = format_code("EMIT", 2)
UNKNOWN_REFERENCE = format_code("EMIT", 3)
MISSING_BACKEND = format_code("EMIT", 4)
MISSING_CONN = format_code("EMIT", 5)
UNKNOWN_CONN_PORT = format_code("EMIT", 6)
MISSING_PLACEHOLDER = format_code("EMIT", 7)
MALFORMED_TEMPLATE = format_code("EMIT", 8)
NETLIST_DESIGN_MISSING = format_code("EMIT", 9)
NETLIST_VERIFY_CRASH = format_code("EMIT", 10)
UNRESOLVED_ENV_VAR = format_code("EMIT", 11)
INSTANCE_VARIABLE_OVERRIDE = format_code("EMIT", 12)
VARIABLE_KEY_COLLISION = format_code("EMIT", 13)
EMISSION_NAME_COLLISION = format_code("EMIT", 14)
PROVENANCE_METADATA_WARNING = format_code("EMIT", 15)


def _emit_diagnostic(
    diagnostics: DiagnosticCollector | list[Diagnostic],
    diagnostic: Diagnostic,
) -> None:
    if isinstance(diagnostics, DiagnosticCollector):
        diagnostics.emit(diagnostic)
        return
    diagnostics.append(diagnostic)


def _diagnostic(
    code: str,
    message: str,
    severity: Severity,
    loc: LocationAttr | None = None,
    notes: list[str] | None = None,
    help: str | None = None,
) -> Diagnostic:
    span = _location_attr_to_span(loc)
    resolved_notes = notes
    if span is None:
        if resolved_notes is None:
            resolved_notes = [NO_SPAN_NOTE]
        elif NO_SPAN_NOTE not in resolved_notes:
            resolved_notes = [*resolved_notes, NO_SPAN_NOTE]
    return Diagnostic(
        code=code,
        severity=severity,
        message=message,
        primary_span=span,
        notes=resolved_notes,
        help=help,
        source="emit",
    )


def _location_attr_to_span(loc: LocationAttr | None) -> SourceSpan | None:
    """Convert an xdsl LocationAttr into a diagnostics SourceSpan when possible.

    Args:
        loc: Optional xdsl location attribute.

    Returns:
        SourceSpan if the location is a FileLineColLoc; otherwise None.
    """
    if loc is None:
        return None
    if FileLineColLoc is not None and isinstance(loc, FileLineColLoc):
        return SourceSpan(
            file=loc.filename.data,
            start=SourcePos(loc.line.data, loc.column.data),
            end=SourcePos(loc.line.data, loc.column.data),
        )
    return None


def _has_error_diagnostics(diagnostics: Iterable[Diagnostic]) -> bool:
    return any(
        diagnostic.severity in (Severity.ERROR, Severity.FATAL)
        for diagnostic in diagnostics
    )
