"""Shared runtime helpers for `asdlc query` command handlers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

import click

from asdl.diagnostics import Diagnostic, Severity, format_code
from asdl.emit.netlist_ir import NetlistDesign
from asdl.lowering import run_netlist_ir_pipeline

QUERY_RUNTIME_ERROR = format_code("TOOL", 4)
QUERY_JSON_SCHEMA_VERSION = 1


class QueryStage(str, Enum):
    """Supported `asdlc query` pipeline stages."""

    AUTHORED = "authored"
    RESOLVED = "resolved"
    EMITTED = "emitted"


@dataclass(frozen=True)
class QueryRuntime:
    """Shared runtime payload for query subcommands.

    Attributes:
        stage: Requested query stage.
        authored_design: Design produced directly from lowering pipeline.
        resolved_design: View-resolved design (or authored when no view config).
        stage_design: Stage-specific design selected for the query.
        resolved_bindings: Optional view-binding sidecar entries.
    """

    stage: QueryStage
    authored_design: NetlistDesign
    resolved_design: NetlistDesign
    stage_design: NetlistDesign
    resolved_bindings: tuple[Any, ...]


def query_common_options(func: Callable[..., Any]) -> Callable[..., Any]:
    """Attach shared query options to a Click subcommand callback.

    Args:
        func: Query subcommand callback.

    Returns:
        Callback decorated with shared query options.
    """

    decorators = [
        click.argument("input_file", type=click.Path(dir_okay=False, path_type=Path)),
        click.option(
            "--config",
            "config_path",
            type=click.Path(dir_okay=False, path_type=Path),
            help="Explicit .asdlrc path (overrides discovery).",
        ),
        click.option(
            "--lib",
            "lib_roots",
            multiple=True,
            type=click.Path(file_okay=False, path_type=Path),
            help="Library search root (repeatable).",
        ),
        click.option(
            "--view-config",
            "view_config_path",
            type=click.Path(dir_okay=False, path_type=Path),
            help="View-binding config YAML path.",
        ),
        click.option(
            "--view-profile",
            "view_profile",
            type=str,
            help="View-binding profile name from --view-config.",
        ),
        click.option(
            "--top",
            "top_name",
            type=str,
            help="Optional top-module override.",
        ),
        click.option(
            "--stage",
            "stage",
            type=click.Choice([item.value for item in QueryStage], case_sensitive=True),
            default=QueryStage.RESOLVED.value,
            show_default=True,
            help="Query stage to inspect.",
        ),
        click.option(
            "--json",
            "json_output",
            is_flag=True,
            default=False,
            help="Emit machine-readable JSON payload.",
        ),
    ]
    wrapped = func
    for decorator in reversed(decorators):
        wrapped = decorator(wrapped)
    return wrapped


def validate_query_common_options(
    *, view_config_path: Optional[Path], view_profile: Optional[str]
) -> list[str]:
    """Validate shared query option dependencies.

    Args:
        view_config_path: Optional path supplied to `--view-config`.
        view_profile: Optional profile supplied to `--view-profile`.

    Returns:
        Error messages for invalid option combinations.
    """

    errors: list[str] = []
    if view_config_path is None and view_profile is not None:
        errors.append("--view-profile requires --view-config.")
    if view_config_path is not None and view_profile is None:
        errors.append("--view-config requires --view-profile.")
    return errors


def build_query_runtime(
    *,
    entry_file: Path,
    config_path: Optional[Path],
    lib_roots: Iterable[Path],
    stage: QueryStage,
    view_config_path: Optional[Path] = None,
    view_profile: Optional[str] = None,
    verify: bool = True,
) -> tuple[Optional[QueryRuntime], list[Diagnostic]]:
    """Build stage-specific query runtime state from an ASDL entry file.

    Args:
        entry_file: Query entry file.
        config_path: Optional explicit `.asdlrc` path (resolved by caller).
        lib_roots: Resolved library roots.
        stage: Requested stage for subcommand execution.
        view_config_path: Optional view-config path.
        view_profile: Optional view profile when view config is provided.
        verify: Enable verifier passes in the lowering pipeline.

    Returns:
        Tuple of `(runtime, diagnostics)` where runtime is None on failure.
    """

    diagnostics: list[Diagnostic] = []
    del config_path
    authored_design, pipeline_diags = run_netlist_ir_pipeline(
        entry_file=entry_file,
        lib_roots=lib_roots,
        verify=verify,
    )
    diagnostics.extend(pipeline_diags)
    if authored_design is None or _has_error_diagnostics(diagnostics):
        return None, diagnostics

    resolved_design = authored_design
    resolved_bindings: tuple[Any, ...] = ()
    if view_config_path is not None and view_profile is not None:
        try:
            from asdl.views.api import (
                VIEW_APPLY_ERROR,
                apply_resolved_view_bindings,
                resolve_design_view_bindings,
            )
        except Exception as exc:  # pragma: no cover - defensive
            diagnostics.append(
                _diagnostic(f"Failed to load view-binding dependencies: {exc}")
            )
            return None, diagnostics

        bindings, view_diags = resolve_design_view_bindings(
            authored_design,
            config_path=view_config_path,
            profile_name=view_profile,
        )
        diagnostics.extend(view_diags)
        if bindings is None or _has_error_diagnostics(diagnostics):
            return None, diagnostics
        resolved_bindings = tuple(bindings)
        try:
            resolved_design = apply_resolved_view_bindings(authored_design, bindings)
        except ValueError as exc:
            diagnostics.append(_diagnostic(str(exc), code=VIEW_APPLY_ERROR))
            return None, diagnostics

    stage_design = authored_design
    if stage in (QueryStage.RESOLVED, QueryStage.EMITTED):
        stage_design = resolved_design

    return (
        QueryRuntime(
            stage=stage,
            authored_design=authored_design,
            resolved_design=resolved_design,
            stage_design=stage_design,
            resolved_bindings=resolved_bindings,
        ),
        diagnostics,
    )


def query_json_envelope(*, kind: str, payload: Any) -> dict[str, Any]:
    """Build the stable v0 query JSON envelope."""

    return {
        "schema_version": QUERY_JSON_SCHEMA_VERSION,
        "kind": kind,
        "payload": payload,
    }


def render_query_json(*, kind: str, payload: Any, compact: bool = True) -> str:
    """Render query JSON envelope with deterministic key ordering."""

    envelope = query_json_envelope(kind=kind, payload=payload)
    if compact:
        return json.dumps(envelope, sort_keys=True, separators=(",", ":"))
    return json.dumps(envelope, sort_keys=True, indent=2)


def query_exit_code(
    diagnostics: Iterable[Diagnostic], *, missing_anchor: bool = False
) -> int:
    """Return query exit code from diagnostics and anchor lookup state."""

    if missing_anchor:
        return 1
    return 1 if _has_error_diagnostics(diagnostics) else 0


def finalize_query_output(
    *,
    kind: str,
    payload: Any,
    json_output: bool,
    diagnostics: Iterable[Diagnostic],
    missing_anchor: bool = False,
) -> tuple[int, str]:
    """Build query command output text and exit code.

    Args:
        kind: Query payload discriminator.
        payload: Query-specific payload object.
        json_output: Whether JSON output is requested.
        diagnostics: Diagnostics collected during query execution.
        missing_anchor: Whether a required anchor lookup failed.

    Returns:
        Tuple `(exit_code, output_text)`.
    """

    exit_code = query_exit_code(diagnostics, missing_anchor=missing_anchor)
    if json_output:
        return exit_code, render_query_json(kind=kind, payload=payload, compact=True)
    return exit_code, str(payload)


def _has_error_diagnostics(diagnostics: Iterable[Diagnostic]) -> bool:
    return any(
        diagnostic.severity in (Severity.ERROR, Severity.FATAL)
        for diagnostic in diagnostics
    )


def _diagnostic(message: str, *, code: str = QUERY_RUNTIME_ERROR) -> Diagnostic:
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        message=message,
        primary_span=None,
        notes=["No source span available."],
        source="query-runtime",
    )


__all__ = [
    "QueryRuntime",
    "QueryStage",
    "build_query_runtime",
    "finalize_query_output",
    "query_common_options",
    "query_exit_code",
    "query_json_envelope",
    "render_query_json",
    "validate_query_common_options",
]
