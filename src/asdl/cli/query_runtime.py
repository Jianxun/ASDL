"""Shared runtime helpers for `asdlc query` command handlers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

import click

from asdl.diagnostics import Diagnostic, Severity, format_code
from asdl.emit.netlist.render import EmissionNameMapEntry, build_emission_name_map
from asdl.emit.netlist_ir import NetlistDesign, NetlistModule
from asdl.lowering import run_netlist_ir_pipeline
from asdl.views.instance_index import build_instance_index

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


@dataclass(frozen=True)
class QueryTreeEntry:
    """One `asdlc query tree` payload row."""

    path: str
    parent_path: Optional[str]
    instance: Optional[str]
    authored_ref: str
    resolved_ref: Optional[str]
    emitted_name: Optional[str]
    depth: int


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


def build_query_tree_payload(runtime: QueryRuntime) -> list[dict[str, Any]]:
    """Build deterministic `query.tree` payload rows for one runtime.

    Args:
        runtime: Query runtime with authored/resolved designs.

    Returns:
        Ordered list of tree rows encoded as JSON-ready dictionaries.
    """

    authored_top = _resolve_top_module(runtime.authored_design)
    if authored_top is None:
        return []

    authored_index = build_instance_index(runtime.authored_design)
    authored_by_path = {entry.full_path: entry for entry in authored_index.entries}

    resolved_top = _resolve_top_module(runtime.resolved_design)
    resolved_index = build_instance_index(runtime.resolved_design)
    resolved_by_path = {entry.full_path: entry for entry in resolved_index.entries}

    emission_lookup = _build_emission_lookup(runtime) if runtime.stage == QueryStage.EMITTED else None

    entries: list[QueryTreeEntry] = []
    top_resolved_ref = (
        resolved_top.name if runtime.stage in (QueryStage.RESOLVED, QueryStage.EMITTED) and resolved_top else None
    )
    top_emitted_name = None
    if emission_lookup is not None and top_resolved_ref is not None:
        top_file_id = resolved_top.file_id if resolved_top is not None else authored_top.file_id
        top_emitted_name = _lookup_emitted_name(
            top_resolved_ref,
            top_file_id,
            emission_lookup,
        )
    entries.append(
        QueryTreeEntry(
            path=authored_top.name,
            parent_path=None,
            instance=None,
            authored_ref=authored_top.name,
            resolved_ref=top_resolved_ref,
            emitted_name=top_emitted_name,
            depth=0,
        )
    )

    for authored_entry in authored_index.entries:
        full_path = authored_entry.full_path
        resolved_entry = resolved_by_path.get(full_path)
        resolved_ref: Optional[str] = None
        if runtime.stage in (QueryStage.RESOLVED, QueryStage.EMITTED):
            resolved_ref = resolved_entry.ref if resolved_entry is not None else None

        emitted_name: Optional[str] = None
        if emission_lookup is not None and resolved_ref is not None:
            emitted_name = _lookup_emitted_name(
                resolved_ref,
                resolved_entry.ref_file_id if resolved_entry is not None else authored_entry.ref_file_id,
                emission_lookup,
            )

        entries.append(
            QueryTreeEntry(
                path=full_path,
                parent_path=authored_entry.path,
                instance=authored_entry.instance,
                authored_ref=authored_entry.ref,
                resolved_ref=resolved_ref,
                emitted_name=emitted_name,
                depth=full_path.count("."),
            )
        )

    return [
        {
            "path": entry.path,
            "parent_path": entry.parent_path,
            "instance": entry.instance,
            "authored_ref": entry.authored_ref,
            "resolved_ref": entry.resolved_ref,
            "emitted_name": entry.emitted_name,
            "depth": entry.depth,
        }
        for entry in entries
    ]


def _build_emission_lookup(
    runtime: QueryRuntime,
) -> tuple[dict[tuple[Optional[str], str], str], dict[str, tuple[EmissionNameMapEntry, ...]]]:
    """Build emitted-name lookups for symbol/file-id keyed queries."""

    by_key: dict[tuple[Optional[str], str], str] = {}
    by_symbol: dict[str, list[EmissionNameMapEntry]] = {}
    for entry in build_emission_name_map(runtime.stage_design):
        by_key[(entry.file_id, entry.symbol)] = entry.emitted_name
        by_symbol.setdefault(entry.symbol, []).append(entry)
    return by_key, {symbol: tuple(entries) for symbol, entries in by_symbol.items()}


def _lookup_emitted_name(
    symbol: str,
    file_id: Optional[str],
    lookup: tuple[dict[tuple[Optional[str], str], str], dict[str, tuple[EmissionNameMapEntry, ...]]],
) -> Optional[str]:
    """Resolve emitted name by exact `(file_id, symbol)` then unique `symbol`."""

    by_key, by_symbol = lookup
    exact = by_key.get((file_id, symbol))
    if exact is not None:
        return exact

    candidates = by_symbol.get(symbol, ())
    if len(candidates) == 1:
        return candidates[0].emitted_name
    return None


def _resolve_top_module(design: NetlistDesign) -> Optional[NetlistModule]:
    """Resolve top module using design top and entry-file semantics."""

    if design.top is not None:
        if design.entry_file_id is not None:
            for module in design.modules:
                if module.name == design.top and module.file_id == design.entry_file_id:
                    return module
        for module in design.modules:
            if module.name == design.top:
                return module
        return None

    if design.entry_file_id is not None:
        entry_modules = [
            module for module in design.modules if module.file_id == design.entry_file_id
        ]
        if len(entry_modules) == 1:
            return entry_modules[0]
        return None

    if len(design.modules) == 1:
        return design.modules[0]
    return None


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
    "build_query_tree_payload",
    "build_query_runtime",
    "finalize_query_output",
    "query_common_options",
    "query_exit_code",
    "query_json_envelope",
    "render_query_json",
    "validate_query_common_options",
]
