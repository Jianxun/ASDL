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
from typing import Any, Dict, List, Optional, Union, get_args, get_origin

from . import data_structures as ds


def _is_optional(annot: Any) -> bool:
    return get_origin(annot) is Union and type(None) in get_args(annot)


def _unwrap_optional(annot: Any) -> Any:
    if _is_optional(annot):
        return Union[tuple(a for a in get_args(annot) if a is not type(None))]  # type: ignore
    return annot


def _schema_for_type(annot: Any) -> Dict[str, Any]:
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

    for f in fields(dc_cls):
        if f.name in exclude:
            continue

        annot = f.type
        is_req = f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING  # type: ignore

        # Optional detection
        if _is_optional(annot):
            inner = _unwrap_optional(annot)
            field_schema = _schema_for_type(inner)
        else:
            field_schema = _schema_for_type(annot)
            if is_req:
                required.append(f.name)

        props[f.name] = field_schema

    schema: Dict[str, Any] = {
        "type": "object",
        "properties": props,
    }
    if required:
        schema["required"] = sorted(required)
    return schema


def build_json_schema() -> Dict[str, Any]:
    """
    Build JSON Schema for the root ASDL document (ASDLFile).
    """
    return _schema_for_dataclass(ds.ASDLFile)


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

    def describe_object(name: str, obj_schema: Dict[str, Any], indent: int = 0) -> None:
        ind = "  " * indent
        lines.append(f"{ind}{name}:")
        props = obj_schema.get("properties", {})
        required = set(obj_schema.get("required", []))
        for key, val in props.items():
            req = " (required)" if key in required else ""
            # Enum
            if "enum" in val:
                choices = "|".join(str(v) for v in val["enum"])
                lines.append(f"{ind}  {key}:{req}  <enum: {choices}>")
            # Array
            elif val.get("type") == "array":
                lines.append(f"{ind}  {key}:{req}  [items]")
            # Object with additionalProperties
            elif val.get("type") == "object" and "additionalProperties" in val:
                lines.append(f"{ind}  {key}:{req}  {{ <string>: value }}")
            # Nested object
            elif val.get("type") == "object":
                lines.append(f"{ind}  {key}:{req}")
                describe_object(f"{key}", val, indent + 2)
            else:
                typ = val.get("type", "any")
                lines.append(f"{ind}  {key}:{req}  <{typ}>")

    describe_object("root", schema, 0)

    return "\n".join(lines) + "\n"


