import pytest

from asdl.diagnostics.core import (
    Diagnostic,
    Severity,
    SourcePos,
    SourceSpan,
    sort_diagnostics,
)


def test_sort_diagnostics_orders_by_file_span_severity_code_message() -> None:
    span_a1 = SourceSpan(file="a.yaml", start=SourcePos(1, 1), end=SourcePos(1, 2))
    span_a2 = SourceSpan(file="a.yaml", start=SourcePos(2, 1), end=SourcePos(2, 2))
    span_b1 = SourceSpan(file="b.yaml", start=SourcePos(1, 1), end=SourcePos(1, 2))

    diagnostics = [
        Diagnostic(code="AST-002", severity=Severity.WARNING, message="late", primary_span=span_a2),
        Diagnostic(code="AST-003", severity=Severity.INFO, message="info", primary_span=span_a1),
        Diagnostic(code="AST-001", severity=Severity.ERROR, message="err", primary_span=span_b1),
        Diagnostic(code="AST-999", severity=Severity.INFO, message="no-span", primary_span=None),
        Diagnostic(code="AST-000", severity=Severity.FATAL, message="fatal", primary_span=span_a1),
    ]

    ordered = sort_diagnostics(diagnostics)
    ordered_codes = [diagnostic.code for diagnostic in ordered]

    assert ordered_codes == [
        "AST-000",
        "AST-003",
        "AST-002",
        "AST-001",
        "AST-999",
    ]


def test_source_span_requires_positions() -> None:
    with pytest.raises(ValueError):
        SourceSpan(file="a.yaml", start=None, end=None)  # type: ignore[arg-type]
