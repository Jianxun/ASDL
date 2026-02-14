"""YAML-aware completion context detection for ASDL documents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CompletionContext:
    """Cursor context information for completion routing.

    Args:
        kind: Semantic completion class (`endpoint`, `import_symbol`, `param`).
        module_name: Module name when available.
        instance_name: Instance map key when available.
        prefix: Text prefix before the cursor in the active token/value.
    """

    kind: str
    module_name: Optional[str]
    instance_name: Optional[str]
    prefix: str


@dataclass(frozen=True)
class _YamlKey:
    indent: int
    key: str


def detect_completion_context(text: str, line: int, character: int) -> Optional[CompletionContext]:
    """Detect completion context from YAML structure and cursor position.

    Args:
        text: Full document text snapshot.
        line: Zero-based line index.
        character: Zero-based character index in the line.

    Returns:
        CompletionContext when the cursor is in a supported ASDL completion
        location, otherwise None.
    """
    lines = text.splitlines()
    if line < 0 or line >= len(lines):
        return None

    stack = _yaml_stack_until(lines, line)
    line_text = lines[line]
    clamped_char = max(0, min(character, len(line_text)))
    prefix_line = line_text[:clamped_char]

    stripped = line_text.lstrip(" ")
    indent = len(line_text) - len(stripped)

    module_name = _module_name_from_stack(stack)

    if _is_endpoint_location(stack, stripped, indent):
        endpoint_prefix = prefix_line.split("-", 1)[-1].strip() if "-" in prefix_line else prefix_line.strip()
        return CompletionContext(
            kind="endpoint",
            module_name=module_name,
            instance_name=None,
            prefix=endpoint_prefix,
        )

    if _is_instance_mapping_line(stack, stripped):
        instance_name, value_prefix = _instance_value_prefix(prefix_line)
        if instance_name is None:
            return None
        first_token, has_params = _instance_expr_shape(value_prefix)
        if has_params:
            return CompletionContext(
                kind="param",
                module_name=module_name,
                instance_name=instance_name,
                prefix=value_prefix,
            )
        return CompletionContext(
            kind="import_symbol",
            module_name=module_name,
            instance_name=instance_name,
            prefix=first_token,
        )

    return None


def _yaml_stack_until(lines: list[str], target_line: int) -> list[_YamlKey]:
    stack: list[_YamlKey] = []
    for index in range(target_line + 1):
        line_text = lines[index]
        stripped = line_text.lstrip(" ")
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line_text) - len(stripped)

        while stack and indent <= stack[-1].indent:
            stack.pop()

        if stripped.startswith("- "):
            continue

        key = _mapping_key(stripped)
        if key is None:
            continue
        stack.append(_YamlKey(indent=indent, key=key))
    return stack


def _mapping_key(stripped: str) -> Optional[str]:
    if ":" not in stripped:
        return None
    key = stripped.split(":", 1)[0].strip()
    if not key:
        return None
    if key.startswith('"') and key.endswith('"'):
        return key[1:-1]
    if key.startswith("'") and key.endswith("'"):
        return key[1:-1]
    return key


def _module_name_from_stack(stack: list[_YamlKey]) -> Optional[str]:
    keys = [entry.key for entry in stack]
    if "modules" not in keys:
        return None
    modules_index = keys.index("modules")
    if modules_index + 1 >= len(keys):
        return None
    return keys[modules_index + 1]


def _is_endpoint_location(stack: list[_YamlKey], stripped: str, indent: int) -> bool:
    if not stripped.startswith("- "):
        return False
    keys = [entry.key for entry in stack]
    if "modules" not in keys or "nets" not in keys:
        return False
    nets_index = keys.index("nets")
    if nets_index + 1 >= len(keys):
        return False
    net_entry = stack[nets_index + 1]
    return indent > net_entry.indent


def _is_instance_mapping_line(stack: list[_YamlKey], stripped: str) -> bool:
    if ":" not in stripped:
        return False
    keys = [entry.key for entry in stack]
    return "modules" in keys and "instances" in keys


def _instance_value_prefix(prefix_line: str) -> tuple[Optional[str], str]:
    if ":" not in prefix_line:
        return None, ""
    key, value = prefix_line.split(":", 1)
    instance_name = key.strip()
    if instance_name.startswith('"') and instance_name.endswith('"'):
        instance_name = instance_name[1:-1]
    if instance_name.startswith("'") and instance_name.endswith("'"):
        instance_name = instance_name[1:-1]
    if not instance_name:
        return None, ""
    return instance_name, value.strip()


def _instance_expr_shape(prefix: str) -> tuple[str, bool]:
    parts = prefix.split()
    if not parts:
        return "", False
    if len(parts) > 1:
        return parts[0], True
    trailing_space = prefix.endswith(" ")
    return parts[0], trailing_space


__all__ = ["CompletionContext", "detect_completion_context"]
