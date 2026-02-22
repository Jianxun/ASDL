"""Parser APIs for ASDL view binding configuration files."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from pydantic import ValidationError
import yaml

from asdl.diagnostics import Diagnostic, Severity, format_code

from .models import ViewConfig

VIEW_CONFIG_PARSE_ERROR = format_code("PARSE", 101)
VIEW_CONFIG_SCHEMA_ERROR = format_code("PARSE", 102)
VIEW_CONFIG_IO_ERROR = format_code("PARSE", 103)


def load_view_config(config_path: Path) -> tuple[Optional[ViewConfig], list[Diagnostic]]:
    """Load and parse a view-binding config file.

    Args:
        config_path: YAML file path for the view config.

    Returns:
        Tuple of validated config model (or None) and diagnostics.
    """
    try:
        yaml_content = Path(config_path).read_text(encoding="utf-8")
    except OSError as exc:
        return None, [
            _diagnostic(
                VIEW_CONFIG_IO_ERROR,
                f"Failed to read view config file '{config_path}': {exc}",
            )
        ]
    return parse_view_config_string(yaml_content, file_label=str(config_path))


def parse_view_config_string(
    yaml_content: str, *, file_label: str = "<memory>"
) -> tuple[Optional[ViewConfig], list[Diagnostic]]:
    """Parse and validate a view-binding config YAML payload.

    Args:
        yaml_content: Raw YAML source text.
        file_label: Logical source label used in diagnostics.

    Returns:
        Tuple of validated config model (or None) and diagnostics.
    """
    try:
        raw = yaml.safe_load(yaml_content)
    except yaml.YAMLError as exc:
        return None, [
            _diagnostic(
                VIEW_CONFIG_PARSE_ERROR,
                f"Failed to parse view config YAML ({file_label}): {exc}",
            )
        ]

    if raw is None:
        raw = {}

    try:
        config = ViewConfig.model_validate(raw)
    except ValidationError as exc:
        diagnostics = _validation_diagnostics(exc)
        return None, diagnostics

    return config, []


def _validation_diagnostics(error: ValidationError) -> list[Diagnostic]:
    """Convert Pydantic validation failures into deterministic diagnostics.

    Args:
        error: Pydantic validation error raised by model validation.

    Returns:
        Deterministically sorted diagnostics.
    """
    diagnostics: list[Diagnostic] = []
    for item in error.errors(include_url=False):
        location = _format_location(item.get("loc", ()))
        message = item.get("msg", "Invalid configuration value")
        diagnostics.append(
            _diagnostic(
                VIEW_CONFIG_SCHEMA_ERROR,
                f"Invalid view config at {location}: {message}",
            )
        )

    return sorted(diagnostics, key=lambda diag: (diag.code, diag.message))


def _format_location(location: Any) -> str:
    """Render Pydantic error locations as dotted paths.

    Args:
        location: Error location tuple/list from Pydantic.

    Returns:
        Dotted path string for deterministic diagnostics.
    """
    if not isinstance(location, (list, tuple)):
        return "<root>"

    parts: list[str] = []
    for token in location:
        if token == "root":
            continue
        parts.append(str(token))

    if not parts:
        return "<root>"
    return ".".join(parts)


def _diagnostic(code: str, message: str) -> Diagnostic:
    """Build an error diagnostic emitted by the view config parser.

    Args:
        code: Diagnostic code.
        message: User-facing diagnostic message.

    Returns:
        Config parser diagnostic.
    """
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        message=message,
        source="views.config",
    )


__all__ = [
    "VIEW_CONFIG_IO_ERROR",
    "VIEW_CONFIG_PARSE_ERROR",
    "VIEW_CONFIG_SCHEMA_ERROR",
    "load_view_config",
    "parse_view_config_string",
]
