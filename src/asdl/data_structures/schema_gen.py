"""
Schema generation from ASDL dataclasses and enums.

- Introspects `data_structures.py` to produce:
  - JSON Schema (dict)
  - Human-readable text schema (string), rendered from JSON Schema

Notes:
- Excludes runtime-only fields declared in `Locatable.__schema_exclude_fields__`
- Avoids static text to prevent drift
"""

from __future__ import annotations

import dataclasses
from dataclasses import is_dataclass, fields
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Mapping, get_args, get_origin, get_type_hints

from . import structures as ds

# Version constant to avoid circular import
ASDL_VERSION = "0.1.0"


def _is_optional(annot: Any) -> bool:
    return get_origin(annot) is Union and type(None) in get_args(annot)


def _unwrap_optional(annot: Any) -> Any:
    if not _is_optional(annot):
        return annot
    non_none_args = [a for a in get_args(annot) if a is not type(None)]
    if len(non_none_args) == 1:
        return non_none_args[0]
    return Union[tuple(non_none_args)]  # type: ignore


def _schema_for_type(annot: Any) -> Dict[str, Any]:
    # Treat Optional[T] as T; optionality is represented via required flags
    if _is_optional(annot):
        annot = _unwrap_optional(annot)
    origin = get_origin(annot)

    if origin is list or origin is List:
        (item_type,) = get_args(annot) or (Any,)
        return {"type": "array", "items": _schema_for_type(item_type)}

    if origin is dict or origin is Dict:
        key_type, val_type = (get_args(annot) or (str, Any))
        # Constrain to string keys, otherwise fall back to object
        if key_type in (str, Optional[str]):
            return {"type": "object", "additionalProperties": _schema_for_type(val_type)}
        return {"type": "object"}

    if origin is Union:
        # For unions (non-optional), use anyOf
        sub_schemas = [_schema_for_type(a) for a in get_args(annot)]
        return {"anyOf": sub_schemas}

    # Enums
    if isinstance(annot, type) and issubclass(annot, Enum):
        return {
            "type": "string",
            "enum": [e.value for e in annot],
        }

    # Dataclasses
    if isinstance(annot, type) and is_dataclass(annot):
        return _schema_for_dataclass(annot)

    # Primitive mappings
    if annot in (str, Optional[str]):
        return {"type": "string"}
    if annot in (int, Optional[int]):
        return {"type": "integer"}
    if annot in (float, Optional[float]):
        return {"type": "number"}
    if annot in (bool, Optional[bool]):
        return {"type": "boolean"}

    # Fallback
    return {}


def _schema_for_dataclass(dc_cls: Any) -> Dict[str, Any]:
    props: Dict[str, Any] = {}
    required: List[str] = []

    # Exclusion set from Locatable (if present)
    exclude = getattr(dc_cls, "__schema_exclude_fields__", set())

    # Resolve forward references using the data structures module namespace so
    # that string annotations like 'FileInfo' or 'DeviceModel' are handled.
    try:
        resolved_types: Dict[str, Any] = get_type_hints(dc_cls, globalns=vars(ds), localns=vars(ds))
    except Exception:
        resolved_types = {}

    for f in fields(dc_cls):
        if f.name in exclude:
            continue

        annot = resolved_types.get(f.name, f.type)
        is_req = f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING  # type: ignore

        field_schema = _schema_for_type(annot)

        # Field-level description via metadata={"schema": {"description": "..."}}
        try:
            metadata: Mapping[str, Any] = getattr(f, "metadata", None) or {}
            schema_meta: Dict[str, Any] = metadata.get("schema", {}) if isinstance(metadata, Mapping) else {}
            desc: Optional[str] = schema_meta.get("description")
            if desc:
                field_schema = {**field_schema, "description": desc}
        except Exception:
            pass

        # Default value support (when explicitly provided and not via factory)
        if f.default is not dataclasses.MISSING and f.default_factory is dataclasses.MISSING:  # type: ignore[attr-defined]
            default_value: Any = f.default
            # Use enum value for JSON default if applicable
            if isinstance(default_value, Enum):
                default_json = default_value.value
            else:
                default_json = default_value
            field_schema = {**field_schema, "default": default_json}
        if is_req:
            required.append(f.name)

        props[f.name] = field_schema

    schema: Dict[str, Any] = {
        "title": getattr(dc_cls, "__name__", "Object"),
        "type": "object",
        "properties": props,
    }
    # Class docstring as description when available
    if isinstance(getattr(dc_cls, "__doc__", None), str):
        raw = (dc_cls.__doc__ or "").strip()
        doc = " ".join(raw.split())
        if doc:
            schema["description"] = doc
    if required:
        schema["required"] = sorted(required)
    return schema


def build_json_schema() -> Dict[str, Any]:
    """
    Build JSON Schema for the root ASDL document (ASDLFile).
    """
    root = _schema_for_dataclass(ds.ASDLFile)
    # Attach root metadata suitable for tooling
    root["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    root["$id"] = f"https://osic-suite.org/asdl/schema/{ASDL_VERSION}"
    root["version"] = ASDL_VERSION
    root.setdefault("title", "ASDLFile")
    root.setdefault("description", "Root ASDL YAML document structure")
    return root


def render_text_schema() -> str:
    """
    Render a human-readable schema overview using JSON Schema as input.
    """
    schema = build_json_schema()

    lines: List[str] = []
    lines.append("=" * 40)
    lines.append("ASDL YAML Configuration Schema")
    lines.append("=" * 40)
    lines.append("")

    def type_label(s: Dict[str, Any]) -> str:
        # Prefer title if present (dataclasses), otherwise fallback to JSON Schema type
        if isinstance(s, dict) and "title" in s:
            return str(s["title"])  # e.g., Port, Module, DeviceModel
        return str(s.get("type", "any"))

    def describe_object(name: str, obj_schema: Dict[str, Any], indent: int = 0) -> None:
        ind = "  " * indent
        header = f"{ind}{name}:"
        # Try to include a short description when available
        desc = obj_schema.get("description")
        extras: List[str] = []
        if desc:
            extras.append(str(desc))
        if "default" in obj_schema:
            extras.append(f"default: {obj_schema['default']}")
        if extras:
            header += f"  # {' — '.join(extras)}"
        lines.append(header)
        props = obj_schema.get("properties", {})
        required = set(obj_schema.get("required", []))
        for key, val in props.items():
            req = " (required)" if key in required else ""
            # Compose trailing comment parts (description, default)
            tail_parts: List[str] = []
            if "description" in val:
                tail_parts.append(str(val["description"]))
            if "default" in val:
                tail_parts.append(f"default: {val['default']}")
            tail = f"  # {' — '.join(tail_parts)}" if tail_parts else ""

            # Enum
            if "enum" in val:
                choices = "|".join(str(v) for v in val["enum"])
                line = f"{ind}  {key}:{req}  <enum: {choices}>{tail}"
                lines.append(line)
            # Array
            elif val.get("type") == "array":
                item_schema = val.get("items", {})
                label = type_label(item_schema)
                line = f"{ind}  {key}:{req}  [ {label} ]{tail}"
                lines.append(line)
                # Expand item schema if it is an object with properties
                if isinstance(item_schema, dict) and item_schema.get("type") == "object" and item_schema.get("properties"):
                    describe_object(f"{key}[]", item_schema, indent + 2)
            # Object with additionalProperties
            elif val.get("type") == "object" and "additionalProperties" in val:
                ap = val.get("additionalProperties", {})
                label = type_label(ap)
                line = f"{ind}  {key}:{req}  {{ <string>: {label} }}{tail}"
                lines.append(line)
                # Expand value schema if it is an object with properties
                if isinstance(ap, dict) and ap.get("type") == "object" and ap.get("properties"):
                    describe_object(f"{key}[*]", ap, indent + 2)
            # Nested object (inline expansion; avoid duplicate header)
            elif val.get("type") == "object":
                line = f"{ind}  {key}:{req}{tail}"
                lines.append(line)
                # Inline list nested properties under this key
                nested_props = val.get("properties", {})
                nested_required = set(val.get("required", []))
                # Recurse by temporarily building a faux object without emitting another header
                if nested_props:
                    # Manually render nested properties at increased indent
                    save_lines_len = len(lines)
                    # Iterate nested properties similar to top-level rendering
                    nind = "  " * (indent + 2)
                    for nkey, nval in nested_props.items():
                        nreq = " (required)" if nkey in nested_required else ""
                        n_tail_parts: List[str] = []
                        if "description" in nval:
                            n_tail_parts.append(str(nval["description"]))
                        if "default" in nval:
                            n_tail_parts.append(f"default: {nval['default']}")
                        n_tail = f"  # {' — '.join(n_tail_parts)}" if n_tail_parts else ""

                        if "enum" in nval:
                            choices = "|".join(str(v) for v in nval["enum"])
                            lines.append(f"{nind}{nkey}:{nreq}  <enum: {choices}>{n_tail}")
                        elif nval.get("type") == "array":
                            item_schema = nval.get("items", {})
                            label = type_label(item_schema)
                            lines.append(f"{nind}{nkey}:{nreq}  [ {label} ]{n_tail}")
                            if isinstance(item_schema, dict) and item_schema.get("type") == "object" and item_schema.get("properties"):
                                describe_object(f"{key}[]", item_schema, indent + 4)
                        elif nval.get("type") == "object" and "additionalProperties" in nval:
                            ap2 = nval.get("additionalProperties", {})
                            label2 = type_label(ap2)
                            lines.append(f"{nind}{nkey}:{nreq}  {{ <string>: {label2} }}{n_tail}")
                            if isinstance(ap2, dict) and ap2.get("type") == "object" and ap2.get("properties"):
                                describe_object(f"{nkey}[*]", ap2, indent + 4)
                        elif nval.get("type") == "object":
                            lines.append(f"{nind}{nkey}:{nreq}{n_tail}")
                            describe_object(f"{nkey}", nval, indent + 4)
                        else:
                            ntyp = nval.get("type", "any")
                            lines.append(f"{nind}{nkey}:{nreq}  <{ntyp}>{n_tail}")
            else:
                typ = val.get("type", "any")
                line = f"{ind}  {key}:{req}  <{typ}>{tail}"
                lines.append(line)

    describe_object("root", schema, 0)

    return "\n".join(lines) + "\n"


