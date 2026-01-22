"""Diagnostic helpers for AST -> PatternedGraph lowering."""

from __future__ import annotations

from typing import Optional

from asdl.ast.location import Locatable
from asdl.core.graph_builder import PatternedGraphBuilder
from asdl.diagnostics import Diagnostic, Severity, SourceSpan, format_code

INVALID_INSTANCE_EXPR = format_code("IR", 1)
INVALID_ENDPOINT_EXPR = format_code("IR", 2)
PATTERN_PARSE_ERROR = format_code("IR", 3)
QUALIFIED_REFERENCE_ERROR = format_code("IR", 10)
UNQUALIFIED_REFERENCE_ERROR = format_code("IR", 11)

NO_SPAN_NOTE = "No source span available."


def _register_span(
    builder: PatternedGraphBuilder,
    entity_id: str,
    loc: Optional[Locatable],
) -> None:
    """Register a source span for an entity when available.

    Args:
        builder: PatternedGraph builder instance.
        entity_id: Graph entity identifier.
        loc: Optional location payload.
    """
    if loc is None:
        return
    span = loc.to_source_span()
    if span is not None:
        builder.register_source_span(entity_id, span)


def _diagnostic(
    code: str,
    message: str,
    loc: Optional[Locatable],
    *,
    severity: Severity = Severity.ERROR,
) -> Diagnostic:
    """Create a diagnostic with optional location metadata.

    Args:
        code: Diagnostic code.
        message: Diagnostic message.
        loc: Optional location payload.
        severity: Diagnostic severity.

    Returns:
        Diagnostic instance.
    """
    span: Optional[SourceSpan] = None
    if loc is not None:
        span = loc.to_source_span()
    notes = None
    if span is None:
        notes = [NO_SPAN_NOTE]
    return Diagnostic(
        code=code,
        severity=severity,
        message=message,
        primary_span=span,
        notes=notes,
        source="core",
    )
