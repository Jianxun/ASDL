"""Deterministic view-binding resolver with inspectable sidecar entries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from asdl.emit.netlist_ir import NetlistDesign

from .instance_index import ViewInstanceIndexEntry, build_instance_index, match_index_entries
from .models import ViewProfile


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
        if self.path:
            return f"{self.path}.{self.instance}"
        return self.instance


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
    modules_by_key, module_name_counts = _build_symbol_indexes(design)

    sidecar: list[ResolvedViewBindingEntry] = []
    sidecar_positions: dict[str, int] = {}
    index_entries_by_full_path: dict[str, ViewInstanceIndexEntry] = {}

    for index_entry in index.entries:
        resolved = _resolve_baseline_symbol(
            index_entry,
            view_order=profile.view_order,
            modules_by_key=modules_by_key,
            module_name_counts=module_name_counts,
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
            module_name_counts=module_name_counts,
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
    modules_by_key: set[tuple[Optional[str], str]],
    module_name_counts: Dict[str, int],
) -> str:
    """Select baseline resolved symbol for one instance entry.

    Args:
        entry: Indexed instance entry with logical module context.
        view_order: Ordered precedence list from a view profile.
        modules_by_key: Available modules keyed by `(file_id, symbol)`.
        module_name_counts: Module-name occurrence counts across the design.

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
            module_name_counts=module_name_counts,
        ):
            return candidate

    raise ValueError(
        "Unable to resolve baseline view "
        f"for instance '{entry.full_path}' and logical module '{entry.module}'"
    )


def _build_symbol_indexes(
    design: NetlistDesign,
) -> tuple[set[tuple[Optional[str], str]], Dict[str, int]]:
    """Build symbol lookup indexes used by baseline and final checks.

    Args:
        design: NetlistIR design containing module symbols.

    Returns:
        Tuple of keyed symbol set and global name-count map.
    """
    modules_by_key = {(module.file_id, module.name) for module in design.modules}
    module_name_counts: Dict[str, int] = {}
    for module in design.modules:
        module_name_counts[module.name] = module_name_counts.get(module.name, 0) + 1
    return modules_by_key, module_name_counts


def _module_symbol_exists(
    *,
    symbol: str,
    file_id: Optional[str],
    modules_by_key: set[tuple[Optional[str], str]],
    module_name_counts: Dict[str, int],
) -> bool:
    """Check whether a module symbol is present in the loaded design.

    Args:
        symbol: Module symbol to validate.
        file_id: Preferred source file identifier context.
        modules_by_key: Available modules keyed by `(file_id, symbol)`.
        module_name_counts: Module-name occurrence counts across the design.

    Returns:
        True when symbol exists in-file or is globally unambiguous by name.
    """
    if (file_id, symbol) in modules_by_key:
        return True
    return module_name_counts.get(symbol, 0) == 1


__all__ = ["ResolvedViewBindingEntry", "resolve_view_bindings"]
