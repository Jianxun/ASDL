import json

from asdl.diagnostics.core import Diagnostic, FixIt, Label, Severity, SourcePos, SourceSpan
from asdl.diagnostics.renderers import diagnostics_to_jsonable, render_json, render_text


def test_render_text_includes_optional_sections() -> None:
    span = SourceSpan(file="design.yaml", start=SourcePos(3, 1), end=SourcePos(3, 9))
    diagnostic = Diagnostic(
        code="PARSE-001",
        severity=Severity.ERROR,
        message="Unknown key: top_modee",
        primary_span=span,
        labels=[Label(span=span, message="bad key")],
        notes=["Did you mean `top_mode`?"],
        help="Check the spelling.",
        fixits=[FixIt(span=span, replacement="top_mode", message="Fix key spelling")],
        source="parser",
    )

    rendered = render_text([diagnostic])
    expected = "\n".join(
        [
            "design.yaml:3:1: error PARSE-001: Unknown key: top_modee",
            "  bad key (3:1-3:9)",
            "  note: Did you mean `top_mode`?",
            "  help: Check the spelling.",
            "  fix-it: Fix key spelling (3:1-3:9) => top_mode",
        ]
    )

    assert rendered == expected


def test_render_json_uses_stable_shape() -> None:
    diagnostic = Diagnostic(
        code="AST-001",
        severity=Severity.WARNING,
        message="Example warning",
        primary_span=None,
    )

    payload = diagnostics_to_jsonable([diagnostic])
    assert payload == [
        {
            "code": "AST-001",
            "severity": "warning",
            "message": "Example warning",
            "primary_span": None,
            "labels": [],
            "notes": [],
            "help": None,
            "fixits": [],
            "source": None,
        }
    ]

    rendered = render_json([diagnostic])
    assert json.loads(rendered) == payload
