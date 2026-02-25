"""Deterministic hierarchical instance indexing for view-binding resolution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from asdl.core.hierarchy import traverse_hierarchy
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

    traversal = traverse_hierarchy(design, include_devices=False, order="dfs-pre")
    entries = tuple(
        ViewInstanceIndexEntry(
            path=row.parent_path,
            instance=row.instance,
            module=_logical_module_name(row.ref),
            ref=row.ref,
            ref_file_id=row.ref_file_id,
        )
        for row in traversal
    )
    return ViewInstanceIndex(entries=entries, root_path=top.name)


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


__all__ = [
    "ViewInstanceIndex",
    "ViewInstanceIndexEntry",
    "build_instance_index",
    "match_index_entries",
]
