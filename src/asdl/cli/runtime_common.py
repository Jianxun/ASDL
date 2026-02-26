"""Shared CLI runtime helpers for view-binding orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Optional

from asdl.diagnostics import Diagnostic, Severity
from asdl.emit.netlist_ir import NetlistDesign


def validate_view_binding_options(
    *, view_config_path: Optional[Path], view_profile: Optional[str]
) -> list[str]:
    """Validate view-binding option dependencies for CLI commands.

    Args:
        view_config_path: Optional path supplied by ``--view-config``.
        view_profile: Optional value supplied by ``--view-profile``.

    Returns:
        Error messages for invalid option combinations.
    """

    errors: list[str] = []
    if view_config_path is None and view_profile is not None:
        errors.append("--view-profile requires --view-config.")
    if view_config_path is not None and view_profile is None:
        errors.append("--view-config requires --view-profile.")
    return errors


def resolve_and_apply_view_bindings(
    *,
    design: NetlistDesign,
    view_config_path: Optional[Path],
    view_profile: Optional[str],
    diagnostic_builder: Callable[[str, str], Diagnostic],
    import_error_code: str,
) -> tuple[Optional[NetlistDesign], tuple[Any, ...], list[Diagnostic]]:
    """Resolve and apply optional view bindings for a compiled design.

    This helper encapsulates the shared query/netlist orchestration for:
    loading view APIs, resolving bindings, validating diagnostics, and applying
    resolved bindings to produce the runtime design.

    Args:
        design: Authored pipeline output design.
        view_config_path: Optional view config path.
        view_profile: Optional profile name from the view config.
        diagnostic_builder: Callback used to construct CLI diagnostics.
        import_error_code: Diagnostic code for dependency import failures.

    Returns:
        Tuple ``(resolved_design, resolved_bindings, diagnostics)`` where
        ``resolved_design`` is ``None`` on failure and ``resolved_bindings`` is
        always a tuple.
    """

    if view_config_path is None or view_profile is None:
        return design, (), []

    diagnostics: list[Diagnostic] = []
    try:
        from asdl.views.api import (
            VIEW_APPLY_ERROR,
            apply_resolved_view_bindings,
            resolve_design_view_bindings,
        )
    except Exception as exc:  # pragma: no cover - defensive
        diagnostics.append(
            diagnostic_builder(
                import_error_code, f"Failed to load view-binding dependencies: {exc}"
            )
        )
        return None, (), diagnostics

    bindings, view_diags = resolve_design_view_bindings(
        design,
        config_path=view_config_path,
        profile_name=view_profile,
    )
    diagnostics.extend(view_diags)
    if bindings is None or _has_error_diagnostics(diagnostics):
        return None, (), diagnostics

    try:
        resolved_design = apply_resolved_view_bindings(design, bindings)
    except ValueError as exc:
        diagnostics.append(diagnostic_builder(VIEW_APPLY_ERROR, str(exc)))
        return None, (), diagnostics
    return resolved_design, tuple(bindings), diagnostics


def _has_error_diagnostics(diagnostics: list[Diagnostic]) -> bool:
    return any(
        diagnostic.severity in (Severity.ERROR, Severity.FATAL)
        for diagnostic in diagnostics
    )
