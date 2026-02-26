"""Deterministic view-binding resolver with inspectable sidecar entries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from asdl.core.symbol_resolution import index_symbols, symbol_exists
from asdl.emit.netlist_ir import NetlistDesign, NetlistModule

from .instance_index import (
    ViewInstanceIndex,
    ViewInstanceIndexEntry,
    build_instance_index,
    match_index_entries,
)
from .models import ViewProfile
from .pathing import join_hierarchy_path


@dataclass(frozen=True)
class ResolvedViewBindingEntry:
    """Resolved binding outcome for one indexed hierarchical instance.

    Attributes:
        path: Parent hierarchy path, excluding this instance leaf.
        instance: Instance leaf name.
        resolved: Resolved module symbol in `cell` or `cell@view` form.
        rule_id: Matching rule identifier that last overrode baseline, or None.
    """

    path: str
    instance: str
    resolved: str
    rule_id: Optional[str]

    @property
    def full_path(self) -> str:
        """Return the full hierarchical instance path including the leaf."""
        return join_hierarchy_path(self.path, self.instance)


def resolve_view_bindings(
    design: NetlistDesign, profile: ViewProfile
) -> tuple[ResolvedViewBindingEntry, ...]:
    """Resolve module symbols for indexed instances using profile semantics.

    The resolver applies baseline `view_order` selection first, then ordered
    rule overrides where later matching rules win for each instance.

    Args:
        design: NetlistIR design whose hierarchical instances will be resolved.
        profile: Validated view-binding profile.

    Returns:
        Deterministic sidecar entries in hierarchical index order.

    Raises:
        ValueError: If baseline resolution fails or final resolved symbols are
            unavailable in the loaded design modules.
    """
    index = build_instance_index(design)
    modules_by_key, modules_by_name = index_symbols(design.modules)

    sidecar: list[ResolvedViewBindingEntry] = []
    sidecar_positions: dict[str, int] = {}
    index_entries_by_full_path: dict[str, ViewInstanceIndexEntry] = {}

    for index_entry in index.entries:
        resolved = _resolve_baseline_symbol(
            index_entry,
            view_order=profile.view_order,
            modules_by_key=modules_by_key,
            modules_by_name=modules_by_name,
        )
        resolved_entry = ResolvedViewBindingEntry(
            path=index_entry.path,
            instance=index_entry.instance,
            resolved=resolved,
            rule_id=None,
        )
        sidecar_positions[index_entry.full_path] = len(sidecar)
        index_entries_by_full_path[index_entry.full_path] = index_entry
        sidecar.append(resolved_entry)

    for rule in profile.rules:
        if rule.match.path is not None and not _index_has_hierarchy_path(index, rule.match.path):
            raise ValueError(
                f"Rule '{rule.id}' match.path '{rule.match.path}' does not resolve "
                "to an existing hierarchy node"
            )
        for matched_entry in match_index_entries(index, rule.match):
            position = sidecar_positions[matched_entry.full_path]
            sidecar[position] = ResolvedViewBindingEntry(
                path=matched_entry.path,
                instance=matched_entry.instance,
                resolved=rule.bind,
                rule_id=rule.id,
            )

    for resolved_entry in sidecar:
        source_entry = index_entries_by_full_path[resolved_entry.full_path]
        if not _module_symbol_exists(
            symbol=resolved_entry.resolved,
            file_id=source_entry.ref_file_id,
            modules_by_key=modules_by_key,
            modules_by_name=modules_by_name,
        ):
            raise ValueError(
                "Resolved symbol "
                f"'{resolved_entry.resolved}' for instance "
                f"'{resolved_entry.full_path}' is not defined in the design"
            )

    return tuple(sidecar)


def _resolve_baseline_symbol(
    entry: ViewInstanceIndexEntry,
    *,
    view_order: list[str],
    modules_by_key: dict[tuple[Optional[str], str], NetlistModule],
    modules_by_name: dict[str, list[NetlistModule]],
) -> str:
    """Select baseline resolved symbol for one instance entry.

    Args:
        entry: Indexed instance entry with logical module context.
        view_order: Ordered precedence list from a view profile.
        modules_by_key: Available modules keyed by `(file_id, symbol)`.
        modules_by_name: Modules grouped by symbol name.

    Returns:
        Resolved symbol selected from authored ref or `view_order` candidates.

    Raises:
        ValueError: If no baseline candidate exists for an undecorated ref.
    """
    if "@" in entry.ref:
        return entry.ref

    for token in view_order:
        candidate = entry.module if token == "default" else f"{entry.module}@{token}"
        if _module_symbol_exists(
            symbol=candidate,
            file_id=entry.ref_file_id,
            modules_by_key=modules_by_key,
            modules_by_name=modules_by_name,
        ):
            return candidate

    raise ValueError(
        "Unable to resolve baseline view "
        f"for instance '{entry.full_path}' and logical module '{entry.module}'"
    )


def _module_symbol_exists(
    *,
    symbol: str,
    file_id: Optional[str],
    modules_by_key: dict[tuple[Optional[str], str], NetlistModule],
    modules_by_name: dict[str, list[NetlistModule]],
) -> bool:
    """Check whether a module symbol is present in the loaded design.

    Args:
        symbol: Module symbol to validate.
        file_id: Preferred source file identifier context.
        modules_by_key: Available modules keyed by `(file_id, symbol)`.
        modules_by_name: Modules grouped by symbol name.

    Returns:
        True when symbol exists in-file or is globally unambiguous by name.
    """
    return symbol_exists(
        symbols_by_key=modules_by_key,
        symbols_by_name=modules_by_name,
        name=symbol,
        file_id=file_id,
    )


def _index_has_hierarchy_path(index: ViewInstanceIndex, path: str) -> bool:
    """Return whether `path` resolves to the index root or an instance node."""
    if index.root_path == path:
        return True
    return any(entry.full_path == path for entry in index.entries)


__all__ = ["ResolvedViewBindingEntry", "resolve_view_bindings"]
