"""Deterministic hierarchical instance indexing for view-binding resolution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from asdl.emit.netlist_ir import NetlistDesign, NetlistModule

from .models import ViewMatch


@dataclass(frozen=True)
class ViewInstanceIndexEntry:
    """One hierarchical module-instance occurrence for view-binding matching.

    Attributes:
        path: Parent hierarchy path, excluding this instance leaf name.
        instance: Instance leaf name.
        module: Logical (undecorated) referenced module symbol.
        ref: Authored referenced module symbol (`cell` or `cell@view`).
        ref_file_id: Source file identifier for the referenced symbol.
    """

    path: str
    instance: str
    module: str
    ref: str
    ref_file_id: str

    @property
    def full_path(self) -> str:
        """Return the full instance occurrence path including the leaf."""
        if self.path:
            return f"{self.path}.{self.instance}"
        return self.instance


@dataclass(frozen=True)
class ViewInstanceIndex:
    """Deterministic hierarchical instance index used by view rule matching."""

    entries: tuple[ViewInstanceIndexEntry, ...]
    root_path: Optional[str] = None


def build_instance_index(design: NetlistDesign) -> ViewInstanceIndex:
    """Build a deterministic hierarchical index of module instance occurrences.

    The index walks module instances in preorder DFS starting from the resolved
    top module and includes only instances that reference modules.

    Args:
        design: NetlistIR design to index.

    Returns:
        Deterministic instance index.
    """
    top = _resolve_top_module(design)
    if top is None:
        return ViewInstanceIndex(entries=(), root_path=None)

    modules_by_key = {
        (module.file_id, module.name): module for module in design.modules
    }
    modules_by_name: Dict[str, List[NetlistModule]] = {}
    for module in design.modules:
        modules_by_name.setdefault(module.name, []).append(module)

    entries: list[ViewInstanceIndexEntry] = []

    def _visit(
        module: NetlistModule,
        parent_path: str,
        ancestry: Tuple[Tuple[Optional[str], str], ...],
    ) -> None:
        for instance in module.instances:
            target = _select_module(
                modules_by_name,
                modules_by_key,
                instance.ref,
                instance.ref_file_id,
            )
            if target is None:
                continue

            entry = ViewInstanceIndexEntry(
                path=parent_path,
                instance=instance.name,
                module=_logical_module_name(instance.ref),
                ref=instance.ref,
                ref_file_id=instance.ref_file_id,
            )
            entries.append(entry)

            child_parent_path = entry.full_path
            target_key: Tuple[Optional[str], str] = (target.file_id, target.name)
            if target_key in ancestry:
                continue
            _visit(target, child_parent_path, ancestry + (target_key,))

    top_key: Tuple[Optional[str], str] = (top.file_id, top.name)
    _visit(top, top.name, (top_key,))
    return ViewInstanceIndex(entries=tuple(entries), root_path=top.name)


def match_index_entries(
    index: ViewInstanceIndex, match: ViewMatch
) -> tuple[ViewInstanceIndexEntry, ...]:
    """Match index entries against view-rule predicates.

    Args:
        index: Instance index from ``build_instance_index``.
        match: Validated view-rule predicates.

    Returns:
        Deterministically ordered matching entries.
    """
    return tuple(
        entry
        for entry in index.entries
        if _entry_matches_scope(entry, match.path, index.root_path)
        and (match.instance is None or entry.instance == match.instance)
        and (match.module is None or entry.module == match.module)
    )


def _entry_matches_scope(
    entry: ViewInstanceIndexEntry, path: Optional[str], root_path: Optional[str]
) -> bool:
    """Apply scope semantics for optional path predicates."""
    if path is None:
        return root_path is not None and entry.path == root_path

    full_path = entry.full_path
    return full_path == path or full_path.startswith(f"{path}.")


def _logical_module_name(module_symbol: str) -> str:
    """Return logical cell name for a module symbol (`cell` or `cell@view`)."""
    return module_symbol.split("@", 1)[0]


def _resolve_top_module(design: NetlistDesign) -> Optional[NetlistModule]:
    """Resolve the top module for hierarchical index traversal."""
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
    modules_by_name: Dict[str, List[NetlistModule]],
    modules_by_key: Dict[Tuple[Optional[str], str], NetlistModule],
    name: str,
    file_id: Optional[str],
) -> Optional[NetlistModule]:
    """Select a module symbol by name and optional file id."""
    if file_id is not None:
        return modules_by_key.get((file_id, name))
    candidates = modules_by_name.get(name, [])
    if len(candidates) == 1:
        return candidates[0]
    if candidates:
        return candidates[-1]
    return None


__all__ = [
    "ViewInstanceIndex",
    "ViewInstanceIndexEntry",
    "build_instance_index",
    "match_index_entries",
]
