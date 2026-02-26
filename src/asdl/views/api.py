"""Public APIs for applying view-binding config profiles to NetlistIR designs."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path
from typing import Optional

from asdl.core.symbol_resolution import index_symbols, select_symbol
from asdl.diagnostics import Diagnostic, Severity, format_code
from asdl.emit.netlist_ir import NetlistDesign, NetlistModule

from .config import load_view_config
from .instance_index import ViewInstanceIndexEntry, build_instance_index
from .resolver import ResolvedViewBindingEntry, resolve_view_bindings

VIEW_PROFILE_NOT_FOUND_ERROR = format_code("PARSE", 104)
VIEW_RESOLUTION_ERROR = format_code("IR", 101)
VIEW_APPLY_ERROR = format_code("IR", 102)


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


def apply_resolved_view_bindings(
    design: NetlistDesign, entries: tuple[ResolvedViewBindingEntry, ...]
) -> NetlistDesign:
    """Return a design copy with resolved module symbols applied to instances.

    Args:
        design: NetlistIR design to rewrite.
        entries: Ordered resolved sidecar entries from `resolve_view_bindings`.

    Returns:
        New NetlistIR design with updated instance `ref` symbols.

    Raises:
        ValueError: If sidecar entries do not match design hierarchy paths or
            if top resolution fails while applying bindings.
    """
    index = build_instance_index(design)
    if not index.entries:
        if entries:
            raise ValueError(
                "Resolved sidecar entries are present but the design has no "
                "hierarchical module instances"
            )
        return design

    resolved_by_path: dict[str, str] = {}
    for entry in entries:
        full_path = entry.full_path
        if full_path in resolved_by_path:
            raise ValueError(f"Resolved sidecar contains duplicate entry for '{full_path}'")
        resolved_by_path[full_path] = entry.resolved

    index_paths = tuple(index_entry.full_path for index_entry in index.entries)
    index_path_set = set(index_paths)
    missing_paths = [path for path in index_paths if path not in resolved_by_path]
    extra_paths = sorted(path for path in resolved_by_path if path not in index_path_set)
    if missing_paths or extra_paths:
        parts: list[str] = []
        if missing_paths:
            parts.append(f"missing paths: {', '.join(missing_paths)}")
        if extra_paths:
            parts.append(f"unknown paths: {', '.join(extra_paths)}")
        raise ValueError("Resolved sidecar does not match design index (" + "; ".join(parts) + ")")

    modules_by_key, modules_by_name = index_symbols(design.modules)
    base_modules_by_name = {
        module_name: candidates.copy() for module_name, candidates in modules_by_name.items()
    }

    top_module = _resolve_top_module(design)
    if top_module is None:
        raise ValueError("Unable to resolve top module for applying view bindings")

    child_entries_by_parent: dict[str, list[ViewInstanceIndexEntry]] = {}
    for index_entry in index.entries:
        child_entries_by_parent.setdefault(index_entry.path, []).append(index_entry)

    used_module_keys = {(module.file_id, module.name) for module in design.modules}
    specialized_modules: list[NetlistModule] = []
    top_override: Optional[NetlistModule] = None
    specialized_ref_by_path: dict[str, tuple[str, str]] = {}

    def _specialize_occurrence(
        path: str, module: NetlistModule, *, is_top: bool
    ) -> tuple[str, str]:
        nonlocal top_override
        cached = specialized_ref_by_path.get(path)
        if cached is not None:
            return cached

        child_entries = child_entries_by_parent.get(path, [])
        if not child_entries:
            specialized_ref_by_path[path] = (module.name, module.file_id)
            return module.name, module.file_id

        child_entries_by_instance = {
            child_entry.instance: child_entry for child_entry in child_entries
        }
        rewritten_instances = []
        changed = False
        for instance in module.instances:
            child_entry = child_entries_by_instance.get(instance.name)
            if child_entry is None:
                rewritten_instances.append(instance)
                continue

            resolved_symbol = resolved_by_path[child_entry.full_path]
            child_module = _select_module(
                modules_by_name,
                modules_by_key,
                base_modules_by_name,
                name=resolved_symbol,
                file_id=child_entry.ref_file_id,
            )
            rewritten_ref = resolved_symbol
            rewritten_ref_file_id = instance.ref_file_id
            if child_module is not None:
                rewritten_ref, rewritten_ref_file_id = _specialize_occurrence(
                    child_entry.full_path,
                    child_module,
                    is_top=False,
                )

            if rewritten_ref == instance.ref and rewritten_ref_file_id == instance.ref_file_id:
                rewritten_instances.append(instance)
                continue

            rewritten_instances.append(
                replace(instance, ref=rewritten_ref, ref_file_id=rewritten_ref_file_id)
            )
            changed = True

        if not changed:
            specialized_ref_by_path[path] = (module.name, module.file_id)
            return module.name, module.file_id

        rewritten_module = replace(module, instances=rewritten_instances)
        if is_top:
            top_override = rewritten_module
            specialized_ref_by_path[path] = (rewritten_module.name, rewritten_module.file_id)
            return rewritten_module.name, rewritten_module.file_id

        specialized_file_id = _build_occurrence_module_file_id(
            path,
            module_name=module.name,
            file_id=module.file_id,
            used_module_keys=used_module_keys,
        )
        specialized_module = replace(rewritten_module, file_id=specialized_file_id)
        specialized_modules.append(specialized_module)
        used_module_keys.add((specialized_module.file_id, specialized_module.name))
        modules_by_key[(specialized_module.file_id, specialized_module.name)] = specialized_module
        modules_by_name.setdefault(specialized_module.name, []).append(specialized_module)
        specialized_ref_by_path[path] = (
            specialized_module.name,
            specialized_module.file_id,
        )
        return specialized_module.name, specialized_module.file_id

    _specialize_occurrence(top_module.name, top_module, is_top=True)

    rewritten_modules: list[NetlistModule] = []
    top_key = (top_module.file_id, top_module.name)
    for module in design.modules:
        if top_override is not None and (module.file_id, module.name) == top_key:
            rewritten_modules.append(top_override)
        else:
            rewritten_modules.append(module)
    rewritten_modules.extend(specialized_modules)
    return replace(design, modules=rewritten_modules)


def _resolve_top_module(design: NetlistDesign) -> Optional[NetlistModule]:
    """Resolve top module by honoring explicit top and optional entry file id."""
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


def _select_module(
    modules_by_name: dict[str, list[NetlistModule]],
    modules_by_key: dict[tuple[Optional[str], str], NetlistModule],
    base_modules_by_name: dict[str, list[NetlistModule]],
    *,
    name: str,
    file_id: Optional[str],
) -> Optional[NetlistModule]:
    """Select one module by symbol name with optional file-id disambiguation."""
    return select_symbol(
        symbols_by_key=modules_by_key,
        symbols_by_name=modules_by_name,
        name=name,
        file_id=file_id,
        fallback_by_name=base_modules_by_name,
    )


def _build_occurrence_module_file_id(
    path: str,
    *,
    module_name: str,
    file_id: Optional[str],
    used_module_keys: set[tuple[Optional[str], str]],
) -> str:
    """Build a deterministic, collision-safe module file-id for one occurrence."""
    digest = hashlib.sha1(path.encode("utf-8")).hexdigest()[:8]
    base_file_id = f"{file_id}#viewocc_{digest}" if file_id else f"viewocc:{digest}"
    candidate = base_file_id
    suffix = 2
    while (candidate, module_name) in used_module_keys:
        candidate = f"{base_file_id}_{suffix}"
        suffix += 1
    return candidate


def _diagnostic(code: str, message: str) -> Diagnostic:
    """Build a views API diagnostic entry."""
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        message=message,
        source="views.api",
    )


__all__ = [
    "VIEW_APPLY_ERROR",
    "VIEW_PROFILE_NOT_FOUND_ERROR",
    "VIEW_RESOLUTION_ERROR",
    "apply_resolved_view_bindings",
    "resolve_design_view_bindings",
    "view_sidecar_to_jsonable",
]
