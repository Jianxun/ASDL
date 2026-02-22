"""Public APIs for applying view-binding config profiles to NetlistIR designs."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Optional

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
            if shared module definitions would require non-uniform rewrites.
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

    modules_by_key = {(module.file_id, module.name): module for module in design.modules}
    modules_by_name: dict[str, list[NetlistModule]] = {}
    for module in design.modules:
        modules_by_name.setdefault(module.name, []).append(module)

    top_module = _resolve_top_module(design)
    if top_module is None:
        raise ValueError("Unable to resolve top module for applying view bindings")

    path_to_module_key: dict[str, tuple[Optional[str], str]] = {
        top_module.name: (top_module.file_id, top_module.name)
    }
    overrides_by_module_key: dict[tuple[Optional[str], str], dict[str, str]] = {}
    for index_entry in index.entries:
        parent_key = path_to_module_key.get(index_entry.path)
        if parent_key is None:
            raise ValueError(
                "Resolved sidecar path mapping is incomplete for "
                f"parent path '{index_entry.path}'"
            )
        resolved_symbol = resolved_by_path[index_entry.full_path]
        module_overrides = overrides_by_module_key.setdefault(parent_key, {})
        existing = module_overrides.get(index_entry.instance)
        if existing is None:
            module_overrides[index_entry.instance] = resolved_symbol
        elif existing != resolved_symbol:
            raise ValueError(
                "Resolved sidecar requires non-uniform rewrite for shared module "
                f"'{parent_key[1]}' instance '{index_entry.instance}' "
                f"({existing} vs {resolved_symbol})"
            )

        child_module = _select_module(
            modules_by_name,
            modules_by_key,
            index_entry,
        )
        if child_module is not None:
            path_to_module_key[index_entry.full_path] = (
                child_module.file_id,
                child_module.name,
            )

    rewritten_modules: list[NetlistModule] = []
    for module in design.modules:
        module_key = (module.file_id, module.name)
        instance_overrides = overrides_by_module_key.get(module_key)
        if instance_overrides is None:
            rewritten_modules.append(module)
            continue

        rewritten_instances = []
        changed = False
        for instance in module.instances:
            resolved_ref = instance_overrides.get(instance.name)
            if resolved_ref is None or resolved_ref == instance.ref:
                rewritten_instances.append(instance)
                continue
            rewritten_instances.append(replace(instance, ref=resolved_ref))
            changed = True

        if changed:
            rewritten_modules.append(replace(module, instances=rewritten_instances))
        else:
            rewritten_modules.append(module)

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
    index_entry: ViewInstanceIndexEntry,
) -> Optional[NetlistModule]:
    """Select the module target for one index entry's authored reference."""
    ref_name = index_entry.ref
    ref_file_id = index_entry.ref_file_id
    if ref_file_id is not None:
        return modules_by_key.get((ref_file_id, ref_name))

    candidates = modules_by_name.get(ref_name, [])
    if len(candidates) == 1:
        return candidates[0]
    if candidates:
        return candidates[-1]
    return None


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
