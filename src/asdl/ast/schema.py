from __future__ import annotations

import json
from pathlib import Path

from asdl.ast import model_json_schema


def build_json_schema() -> dict:
    """Build the JSON schema for the AST document."""
    return model_json_schema()


def render_text_schema() -> str:
    """Render a human-readable summary of the AST JSON schema."""
    schema = build_json_schema()
    lines = ["ASDL schema overview"]

    title = schema.get("title")
    if title:
        lines.append(f"Root: {title}")

    lines.append("")
    lines.append("Top-level fields (required vs optional):")
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))
    if properties:
        for name, entry in properties.items():
            requirement = "required" if name in required else "optional"
            lines.append(f"- {name} ({requirement}): {_schema_summary(entry)}")
    else:
        lines.append("- (none)")

    definitions = schema.get("$defs") or schema.get("definitions")
    if definitions:
        lines.append("")
        lines.append("Definitions:")
        for name in sorted(definitions.keys()):
            lines.append(f"- {name}: {_schema_summary(definitions[name])}")

    return "\n".join(lines).rstrip() + "\n"


def write_schema_artifacts(out_dir: Path) -> tuple[Path, Path]:
    """Write JSON and text schema artifacts to the provided directory."""
    out_dir.mkdir(parents=True, exist_ok=True)

    json_schema = build_json_schema()
    json_path = out_dir / "schema.json"
    json_path.write_text(
        json.dumps(json_schema, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    txt_schema = render_text_schema()
    txt_path = out_dir / "schema.txt"
    txt_path.write_text(txt_schema, encoding="utf-8")

    return json_path, txt_path


def _schema_summary(schema: dict) -> str:
    """Summarize a JSON schema node into a short human-readable form."""
    if "$ref" in schema:
        return schema["$ref"].split("/")[-1]

    if "type" in schema:
        schema_type = schema["type"]
        if schema_type == "array":
            items = schema.get("items", {})
            return f"list[{_schema_summary(items)}]"
        return str(schema_type)

    for key, joiner in (("anyOf", " | "), ("oneOf", " | "), ("allOf", " & ")):
        if key in schema:
            parts = [_schema_summary(entry) for entry in schema[key]]
            return joiner.join(parts)

    if "enum" in schema:
        values = ", ".join(str(value) for value in schema["enum"])
        return f"enum({values})"

    return "object"


__all__ = ["build_json_schema", "render_text_schema", "write_schema_artifacts"]
