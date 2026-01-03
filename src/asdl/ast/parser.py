from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, List, Optional, Tuple

from pydantic import ValidationError
from ruamel.yaml import YAML
from ruamel.yaml.error import MarkedYAMLError, YAMLError

from ..diagnostics import Diagnostic, Severity, SourcePos, SourceSpan
from .location import Locatable, LocationIndex, PathSegment, to_plain
from .models import AsdlDocument, AstBaseModel

PARSE_YAML_ERROR = "PARSE-001"
PARSE_ROOT_ERROR = "PARSE-002"
PARSE_VALIDATION_ERROR = "PARSE-003"
PARSE_FILE_ERROR = "PARSE-004"
NO_SPAN_NOTE = "No source span available."
ENDPOINT_LIST_NOTE = "Endpoint lists must be YAML lists of '<instance>.<pin>' strings"
INSTANCE_EXPR_NOTE = "Instance expressions use '<model> key=value ...' format"


def parse_file(filepath: str) -> Tuple[Optional[AsdlDocument], List[Diagnostic]]:
    file_path = Path(filepath)
    if not file_path.exists():
        return (
            None,
            [
                Diagnostic(
                    code=PARSE_FILE_ERROR,
                    severity=Severity.ERROR,
                    message=f"ASDL file not found: {filepath}",
                    primary_span=None,
                    notes=[NO_SPAN_NOTE],
                    source="parser",
                )
            ],
        )
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        return (
            None,
            [
                Diagnostic(
                    code=PARSE_FILE_ERROR,
                    severity=Severity.ERROR,
                    message=f"Failed to read ASDL file '{filepath}': {exc}",
                    primary_span=None,
                    notes=[NO_SPAN_NOTE],
                    source="parser",
                )
            ],
        )
    return parse_string(content, file_path=file_path)


def parse_string(
    yaml_content: str, file_path: Optional[Path] = None
) -> Tuple[Optional[AsdlDocument], List[Diagnostic]]:
    diagnostics: List[Diagnostic] = []
    file_label = str(file_path) if file_path is not None else "<string>"

    yaml = YAML(typ="rt")
    try:
        data = yaml.load(yaml_content)
    except YAMLError as exc:
        diagnostics.append(_yaml_error_to_diagnostic(exc, file_label))
        return None, diagnostics

    if data is None or not isinstance(data, dict):
        diagnostics.append(
            Diagnostic(
                code=PARSE_ROOT_ERROR,
                severity=Severity.ERROR,
                message="ASDL document root must be a mapping.",
                primary_span=_span_at(file_label, 1, 1),
                source="parser",
            )
        )
        return None, diagnostics

    location_index = LocationIndex.from_yaml(data, file_label)
    plain = to_plain(data)

    try:
        document = AsdlDocument.model_validate(plain)
    except ValidationError as exc:
        diagnostics.extend(_validation_errors_to_diagnostics(exc, location_index))
        return None, diagnostics

    _attach_locations(document, location_index, ())
    return document, diagnostics


def _yaml_error_to_diagnostic(error: YAMLError, file_label: str) -> Diagnostic:
    line = 1
    col = 1
    if isinstance(error, MarkedYAMLError) and error.problem_mark is not None:
        line = error.problem_mark.line + 1
        col = error.problem_mark.column + 1
    message = error.problem or str(error)
    return Diagnostic(
        code=PARSE_YAML_ERROR,
        severity=Severity.ERROR,
        message=f"YAML parse error: {message}",
        primary_span=_span_at(file_label, line, col),
        source="parser",
    )


def _validation_errors_to_diagnostics(
    error: ValidationError, location_index: LocationIndex
) -> List[Diagnostic]:
    diagnostics: List[Diagnostic] = []
    for entry in error.errors():
        loc = entry.get("loc", ())
        prefer_key = entry.get("type") == "extra_forbidden"
        location = location_index.lookup_with_fallback(loc, prefer_key=prefer_key)
        span = location.to_source_span() if location else None
        message = _format_validation_message(entry)
        notes = _hint_notes(entry)
        if span is None:
            notes.append(NO_SPAN_NOTE)
        if not notes:
            notes = None
        path_str = _format_path(loc)
        diagnostics.append(
            Diagnostic(
                code=PARSE_VALIDATION_ERROR,
                severity=Severity.ERROR,
                message=f"{message} at {path_str}",
                primary_span=span,
                notes=notes,
                source="parser",
            )
        )
    return diagnostics


def _format_validation_message(entry: dict) -> str:
    message = entry.get("msg", "Validation error")
    ctx = entry.get("ctx") or {}
    error = ctx.get("error")
    if isinstance(error, ValueError):
        error_message = str(error)
        if ENDPOINT_LIST_NOTE in error_message:
            return error_message
    return message


def _hint_notes(entry: dict) -> List[str]:
    notes: List[str] = []
    loc = entry.get("loc", ())
    if _path_has_segment(loc, "nets"):
        notes.append(ENDPOINT_LIST_NOTE)
    if _path_has_segment(loc, "instances"):
        notes.append(INSTANCE_EXPR_NOTE)
    return notes


def _attach_locations(value: Any, location_index: LocationIndex, path: Iterable[PathSegment]) -> None:
    if isinstance(value, AstBaseModel):
        loc = location_index.lookup_with_fallback(path)
        if loc is not None:
            value.set_loc(loc)
        for field_name in value.__class__.model_fields:
            field_value = getattr(value, field_name)
            _attach_locations(field_value, location_index, (*path, field_name))
        return

    if isinstance(value, dict):
        for key, item in value.items():
            _attach_locations(item, location_index, (*path, key))
        return

    if isinstance(value, list):
        for index, item in enumerate(value):
            _attach_locations(item, location_index, (*path, index))


def _format_path(path: Iterable[PathSegment]) -> str:
    parts: List[str] = []
    for segment in path:
        if isinstance(segment, int):
            parts.append(f"[{segment}]")
        else:
            if parts:
                parts.append(".")
            parts.append(str(segment))
    return "".join(parts) if parts else "<root>"


def _path_has_segment(path: Iterable[PathSegment], segment: str) -> bool:
    return any(isinstance(item, str) and item == segment for item in path)


def _span_at(file_label: str, line: int, col: int) -> SourceSpan:
    return SourceSpan(
        file=file_label,
        start=SourcePos(line, col),
        end=SourcePos(line, col),
    )


__all__ = ["parse_file", "parse_string"]
