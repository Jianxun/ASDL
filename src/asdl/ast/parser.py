"""Parse ASDL YAML into AST models with diagnostics."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable, List, Optional, Tuple

from pydantic import ValidationError
from ruamel.yaml import YAML
from ruamel.yaml.error import MarkedYAMLError, YAMLError
from ruamel.yaml.nodes import MappingNode, ScalarNode

from ..diagnostics import Diagnostic, Severity, SourcePos, SourceSpan
from .location import Locatable, LocationIndex, PathSegment, to_plain
from .models import AsdlDocument, AstBaseModel, InstanceDefaultsDecl, ModuleDecl, PatternDecl

PARSE_YAML_ERROR = "PARSE-001"
PARSE_ROOT_ERROR = "PARSE-002"
PARSE_VALIDATION_ERROR = "PARSE-003"
PARSE_FILE_ERROR = "PARSE-004"
AST_IMPORT_PATH_ERROR = "AST-011"
AST_IMPORT_DUP_NAMESPACE_ERROR = "AST-013"
NO_SPAN_NOTE = "No source span available."
ENDPOINT_LIST_NOTE = "Endpoint lists must be YAML lists of '<instance>.<pin>' strings"
INSTANCE_EXPR_NOTE = "Instance expressions use '<model> key=value ...' format"
IMPORT_NAMESPACE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def parse_file(filepath: str) -> Tuple[Optional[AsdlDocument], List[Diagnostic]]:
    """Parse an ASDL file from disk.

    Args:
        filepath: Path to the YAML file.

    Returns:
        The parsed document (or None) and any diagnostics emitted.
    """
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
    """Parse ASDL YAML content into an AST document.

    Args:
        yaml_content: Raw YAML source text.
        file_path: Optional source file path for diagnostics and spans.

    Returns:
        The parsed document (or None) and any diagnostics emitted.
    """
    diagnostics: List[Diagnostic] = []
    file_label = str(file_path) if file_path is not None else "<string>"

    yaml = YAML(typ="rt")
    try:
        root_node = yaml.compose(yaml_content)
    except YAMLError as exc:
        diagnostics.append(_yaml_error_to_diagnostic(exc, file_label))
        return None, diagnostics

    duplicate_imports = _duplicate_import_namespace_diagnostics(root_node, file_label)
    if duplicate_imports:
        return None, duplicate_imports

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

    import_errors = _validate_imports(plain, location_index)
    if import_errors:
        return None, import_errors

    try:
        document = AsdlDocument.model_validate(plain)
    except ValidationError as exc:
        diagnostics.extend(_validation_errors_to_diagnostics(exc, location_index))
        return None, diagnostics

    _attach_locations(document, location_index, ())
    return document, diagnostics


def _yaml_error_to_diagnostic(error: YAMLError, file_label: str) -> Diagnostic:
    """Convert a YAML parser error into a diagnostic."""
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
    """Translate Pydantic validation errors into diagnostics.

    Args:
        error: Validation error from Pydantic.
        location_index: Lookup table for source spans.

    Returns:
        Diagnostics describing validation failures.
    """
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


def _duplicate_import_namespace_diagnostics(
    root_node: Optional[MappingNode], file_label: str
) -> List[Diagnostic]:
    """Find duplicate import namespaces before YAML load normalizes keys."""
    if root_node is None or not isinstance(root_node, MappingNode):
        return []

    imports_node = None
    for key_node, value_node in root_node.value:
        if isinstance(key_node, ScalarNode) and key_node.value == "imports":
            if isinstance(value_node, MappingNode):
                imports_node = value_node
            break

    if imports_node is None:
        return []

    seen = set()
    diagnostics: List[Diagnostic] = []
    for key_node, _value_node in imports_node.value:
        if not isinstance(key_node, ScalarNode):
            continue
        namespace = key_node.value
        if namespace in seen:
            span = _span_from_mark(file_label, getattr(key_node, "start_mark", None), len(str(namespace)))
            diagnostics.append(
                _import_diagnostic(
                    code=AST_IMPORT_DUP_NAMESPACE_ERROR,
                    message=f"Duplicate import namespace '{namespace}'.",
                    span=span,
                )
            )
        else:
            seen.add(namespace)
    return diagnostics


def _validate_imports(plain: Any, location_index: LocationIndex) -> List[Diagnostic]:
    """Validate import namespace syntax and path types."""
    if not isinstance(plain, dict):
        return []
    imports = plain.get("imports")
    if imports is None or not isinstance(imports, dict):
        return []

    diagnostics: List[Diagnostic] = []
    for namespace, path in imports.items():
        if not isinstance(namespace, str) or not IMPORT_NAMESPACE_RE.fullmatch(namespace):
            key_loc = location_index.lookup_with_fallback(("imports", namespace), prefer_key=True)
            span = key_loc.to_source_span() if key_loc else None
            diagnostics.append(
                _import_diagnostic(
                    code=AST_IMPORT_PATH_ERROR,
                    message=(
                        f"Invalid import namespace '{namespace}'. "
                        "Namespaces must match [A-Za-z_][A-Za-z0-9_]*."
                    ),
                    span=span,
                )
            )

        if not isinstance(path, str):
            value_loc = location_index.lookup_with_fallback(("imports", namespace))
            span = value_loc.to_source_span() if value_loc else None
            diagnostics.append(
                _import_diagnostic(
                    code=AST_IMPORT_PATH_ERROR,
                    message=f"Import path for namespace '{namespace}' must be a string.",
                    span=span,
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


def _import_diagnostic(code: str, message: str, span: Optional[SourceSpan]) -> Diagnostic:
    """Create an import-related diagnostic with span fallback notes."""
    notes = [NO_SPAN_NOTE] if span is None else None
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        message=message,
        primary_span=span,
        notes=notes,
        source="parser",
    )


def _attach_locations(value: Any, location_index: LocationIndex, path: Iterable[PathSegment]) -> None:
    """Recursively attach source locations to AST nodes.

    Notes:
        This mutates AST models in-place by setting private location fields.
    """
    if isinstance(value, AstBaseModel):
        loc = location_index.lookup_with_fallback(path)
        if loc is not None:
            value.set_loc(loc)
        if isinstance(value, ModuleDecl):
            _attach_module_entry_locations(value, location_index, path)
        if isinstance(value, InstanceDefaultsDecl):
            _attach_instance_defaults_locations(value, location_index, path)
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


def _attach_module_entry_locations(
    module: ModuleDecl, location_index: LocationIndex, path: Iterable[PathSegment]
) -> None:
    """Attach key locations for module instance/net entries."""
    base_path = tuple(path)
    if module.patterns:
        for pattern_name, pattern_value in module.patterns.items():
            key_loc = location_index.lookup(
                (*base_path, "patterns", pattern_name), prefer_key=True
            )
            if key_loc is not None:
                module._patterns_loc[pattern_name] = key_loc
            if isinstance(pattern_value, PatternDecl):
                expr_loc = location_index.lookup((*base_path, "patterns", pattern_name, "expr"))
                if expr_loc is not None:
                    module._pattern_value_loc[pattern_name] = expr_loc
                tag_loc = location_index.lookup((*base_path, "patterns", pattern_name, "tag"))
                if tag_loc is not None:
                    module._pattern_tag_loc[pattern_name] = tag_loc
            else:
                value_loc = location_index.lookup((*base_path, "patterns", pattern_name))
                if value_loc is not None:
                    module._pattern_value_loc[pattern_name] = value_loc
    if module.nets:
        for net_name, endpoints in module.nets.items():
            loc = location_index.lookup((*base_path, "nets", net_name), prefer_key=True)
            if loc is not None:
                module._nets_loc[net_name] = loc
            if isinstance(endpoints, list):
                endpoint_locs: List[Optional[Locatable]] = []
                for index, _endpoint in enumerate(endpoints):
                    endpoint_locs.append(
                        location_index.lookup((*base_path, "nets", net_name, index))
                    )
                module._net_endpoint_locs[net_name] = endpoint_locs
    if module.instances:
        for inst_name in module.instances.keys():
            loc = location_index.lookup((*base_path, "instances", inst_name), prefer_key=True)
            if loc is not None:
                module._instances_loc[inst_name] = loc
            value_loc = location_index.lookup((*base_path, "instances", inst_name))
            if value_loc is not None:
                module._instance_expr_loc[inst_name] = value_loc


def _attach_instance_defaults_locations(
    defaults: InstanceDefaultsDecl,
    location_index: LocationIndex,
    path: Iterable[PathSegment],
) -> None:
    """Attach value locations for instance default bindings."""
    base_path = tuple(path)
    if defaults.bindings:
        for binding_name in defaults.bindings.keys():
            loc = location_index.lookup((*base_path, "bindings", binding_name))
            if loc is not None:
                defaults._bindings_loc[binding_name] = loc


def _format_path(path: Iterable[PathSegment]) -> str:
    """Format a location path into a dotted/ indexed string."""
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


def _span_from_mark(file_label: str, mark: Any, length: int) -> Optional[SourceSpan]:
    """Create a source span from a ruamel mark and scalar length."""
    if mark is None:
        return None
    line = getattr(mark, "line", None)
    col = getattr(mark, "column", None)
    if line is None or col is None:
        return None
    start_line = line + 1
    start_col = col + 1
    end_col = start_col + max(length, 0)
    return SourceSpan(
        file=file_label,
        start=SourcePos(start_line, start_col),
        end=SourcePos(start_line, end_col),
    )


__all__ = ["parse_file", "parse_string"]
