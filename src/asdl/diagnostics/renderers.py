from __future__ import annotations

import json
from typing import Iterable, List, Optional

from .core import Diagnostic, FixIt, Label, Note, SourcePos, SourceSpan, sort_diagnostics


def _span_coords(span: SourceSpan) -> str:
    return f"{span.start.line}:{span.start.col}-{span.end.line}:{span.end.col}"


def _format_label(label: Label) -> str:
    coords = _span_coords(label.span)
    if label.message:
        return f"  {label.message} ({coords})"
    return f"  ({coords})"


def _format_fixit(fixit: FixIt) -> str:
    coords = _span_coords(fixit.span)
    replacement = fixit.replacement.replace("\n", "\\n")
    message = f"{fixit.message} " if fixit.message else ""
    return f"  fix-it: {message}({coords}) => {replacement}"


def render_text(diagnostics: Iterable[Diagnostic]) -> str:
    lines: List[str] = []
    for diagnostic in sort_diagnostics(diagnostics):
        lines.extend(_render_text_diagnostic(diagnostic))
    return "\n".join(lines)


def _render_text_diagnostic(diagnostic: Diagnostic) -> List[str]:
    span = diagnostic.primary_span
    severity = diagnostic.severity.value
    if span and span.file:
        header = f"{span.file}:{span.start.line}:{span.start.col}: {severity} {diagnostic.code}: {diagnostic.message}"
    else:
        header = f"{severity} {diagnostic.code}: {diagnostic.message}"

    lines = [header]
    for label in diagnostic.labels or []:
        lines.append(_format_label(label))
    for note in diagnostic.notes or []:
        lines.append(f"  note: {note}")
    if diagnostic.help:
        lines.append(f"  help: {diagnostic.help}")
    for fixit in diagnostic.fixits or []:
        lines.append(_format_fixit(fixit))
    return lines


def _pos_to_dict(pos: Optional[SourcePos]) -> Optional[dict]:
    if pos is None:
        return None
    return {"line": pos.line, "col": pos.col}


def _span_to_dict(span: Optional[SourceSpan]) -> Optional[dict]:
    if span is None:
        return None
    return {
        "file": span.file,
        "start": _pos_to_dict(span.start),
        "end": _pos_to_dict(span.end),
        "byte_start": span.byte_start,
        "byte_end": span.byte_end,
    }


def _label_to_dict(label: Label) -> dict:
    return {"span": _span_to_dict(label.span), "message": label.message}


def _fixit_to_dict(fixit: FixIt) -> dict:
    return {
        "span": _span_to_dict(fixit.span),
        "replacement": fixit.replacement,
        "message": fixit.message,
    }


def diagnostics_to_jsonable(diagnostics: Iterable[Diagnostic]) -> List[dict]:
    payload: List[dict] = []
    for diagnostic in sort_diagnostics(diagnostics):
        payload.append(
            {
                "code": diagnostic.code,
                "severity": diagnostic.severity.value,
                "message": diagnostic.message,
                "primary_span": _span_to_dict(diagnostic.primary_span),
                "labels": [_label_to_dict(label) for label in diagnostic.labels or []],
                "notes": list(diagnostic.notes or []),
                "help": diagnostic.help,
                "fixits": [_fixit_to_dict(fixit) for fixit in diagnostic.fixits or []],
                "source": diagnostic.source,
            }
        )
    return payload


def render_json(diagnostics: Iterable[Diagnostic], *, indent: int = 2) -> str:
    return json.dumps(diagnostics_to_jsonable(diagnostics), indent=indent)


__all__ = ["render_text", "render_json", "diagnostics_to_jsonable"]
