"""Public APIs for applying view-binding config profiles to NetlistIR designs."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from asdl.diagnostics import Diagnostic, Severity, format_code
from asdl.emit.netlist_ir import NetlistDesign

from .config import load_view_config
from .resolver import ResolvedViewBindingEntry, resolve_view_bindings

VIEW_PROFILE_NOT_FOUND_ERROR = format_code("PARSE", 104)
VIEW_RESOLUTION_ERROR = format_code("IR", 101)


def resolve_design_view_bindings(
    design: NetlistDesign,
    *,
    config_path: Path,
    profile_name: str,
) -> tuple[Optional[tuple[ResolvedViewBindingEntry, ...]], list[Diagnostic]]:
    """Resolve a design's view bindings using one config profile.

    Args:
        design: NetlistIR design to resolve.
        config_path: View config YAML path.
        profile_name: Selected profile key from the config file.

    Returns:
        Tuple of resolved sidecar entries (or None on failure) and diagnostics.
    """
    config, diagnostics = load_view_config(config_path)
    if config is None:
        return None, diagnostics

    profile = config.profiles.get(profile_name)
    if profile is None:
        diagnostics.append(
            _diagnostic(
                VIEW_PROFILE_NOT_FOUND_ERROR,
                f"View profile '{profile_name}' not found in '{config_path}'.",
            )
        )
        return None, diagnostics

    try:
        resolved = resolve_view_bindings(design, profile)
    except ValueError as exc:
        diagnostics.append(_diagnostic(VIEW_RESOLUTION_ERROR, str(exc)))
        return None, diagnostics

    return resolved, diagnostics


def view_sidecar_to_jsonable(
    entries: tuple[ResolvedViewBindingEntry, ...],
) -> list[dict[str, object]]:
    """Convert resolved sidecar entries into deterministic JSON-ready records.

    Args:
        entries: Ordered resolver output entries.

    Returns:
        JSON-serializable sidecar list preserving resolver ordering.
    """
    return [
        {
            "path": entry.path,
            "instance": entry.instance,
            "resolved": entry.resolved,
            "rule_id": entry.rule_id,
        }
        for entry in entries
    ]


def _diagnostic(code: str, message: str) -> Diagnostic:
    """Build a views API diagnostic entry."""
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        message=message,
        source="views.api",
    )


__all__ = [
    "VIEW_PROFILE_NOT_FOUND_ERROR",
    "VIEW_RESOLUTION_ERROR",
    "resolve_design_view_bindings",
    "view_sidecar_to_jsonable",
]
