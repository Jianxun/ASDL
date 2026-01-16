from __future__ import annotations

from typing import Iterable

from xdsl.dialects.builtin import LocationAttr

from asdl.diagnostics import Diagnostic, Severity, format_code
from asdl.diagnostics.collector import DiagnosticCollector
from asdl.ir.location import location_attr_to_span

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


def _emit_diagnostic(
    diagnostics: DiagnosticCollector | list[Diagnostic],
    diagnostic: Diagnostic,
) -> None:
    if isinstance(diagnostics, DiagnosticCollector):
        diagnostics.emit(diagnostic)
        return
    diagnostics.append(diagnostic)


def _diagnostic(
    code: str, message: str, severity: Severity, loc: LocationAttr | None = None
) -> Diagnostic:
    span = location_attr_to_span(loc)
    notes = None if span is not None else [NO_SPAN_NOTE]
    return Diagnostic(
        code=code,
        severity=severity,
        message=message,
        primary_span=span,
        notes=notes,
        source="emit",
    )


def _has_error_diagnostics(diagnostics: Iterable[Diagnostic]) -> bool:
    return any(
        diagnostic.severity in (Severity.ERROR, Severity.FATAL)
        for diagnostic in diagnostics
    )
