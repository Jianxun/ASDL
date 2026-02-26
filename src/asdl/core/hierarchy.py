"""Shared hierarchy traversal utilities for NetlistIR designs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from asdl.emit.netlist_ir import NetlistDesign, NetlistModule
from asdl.core.symbol_resolution import index_symbols, select_symbol
from asdl.core.top_resolution import PERMISSIVE_TOP_POLICY, resolve_top_symbol


@dataclass(frozen=True)
class HierarchyEntry:
    """One deterministic hierarchy traversal row.

    Attributes:
        path: Full instance path including the leaf instance name.
        parent_path: Parent path without the leaf instance.
        instance: Leaf instance name.
        ref: Referenced module/device symbol.
        ref_file_id: Source file id for the referenced symbol.
        depth: Hierarchy depth, equal to `path.count(".")`.
        is_device: True for device references, False for module references.
    """

    path: str
    parent_path: str
    instance: str
    ref: str
    ref_file_id: str
    depth: int
    is_device: bool


def traverse_hierarchy(
    design: NetlistDesign,
    *,
    include_devices: bool,
    order: str = "dfs-pre",
) -> list[HierarchyEntry]:
    """Traverse a NetlistIR module hierarchy with deterministic DFS preorder.

    Traversal starts at the resolved top module and walks authored instance
    order. Module targets recurse in preorder; device targets are always leaves.
    Recursion stops when the next module target already exists in module
    ancestry (cycle edge still emits one entry).

    Args:
        design: Design to traverse.
        include_devices: Include device-referencing instances when True.
        order: Traversal order. Only `"dfs-pre"` is supported in v0.

    Returns:
        Deterministically ordered hierarchy entries.
    """

    if order != "dfs-pre":
        raise ValueError(f"Unsupported hierarchy traversal order: {order!r}")

    top = resolve_top_module(design)
    if top is None:
        return []

    modules_by_key, modules_by_name = index_symbols(design.modules)
    devices_by_key, devices_by_name = index_symbols(design.devices)

    entries: list[HierarchyEntry] = []

    def _visit(
        module: NetlistModule,
        parent_path: str,
        ancestry: tuple[tuple[Optional[str], str], ...],
    ) -> None:
        for instance in module.instances:
            full_path = f"{parent_path}.{instance.name}"

            target_module = select_symbol(
                symbols_by_name=modules_by_name,
                symbols_by_key=modules_by_key,
                name=instance.ref,
                file_id=instance.ref_file_id,
            )
            is_device = False
            if target_module is None:
                target_device = select_symbol(
                    symbols_by_name=devices_by_name,
                    symbols_by_key=devices_by_key,
                    name=instance.ref,
                    file_id=instance.ref_file_id,
                )
                if target_device is None or not include_devices:
                    continue
                is_device = True

            entries.append(
                HierarchyEntry(
                    path=full_path,
                    parent_path=parent_path,
                    instance=instance.name,
                    ref=instance.ref,
                    ref_file_id=instance.ref_file_id,
                    depth=full_path.count("."),
                    is_device=is_device,
                )
            )

            if target_module is None:
                continue
            target_key: tuple[Optional[str], str] = (target_module.file_id, target_module.name)
            if target_key in ancestry:
                continue
            _visit(target_module, full_path, ancestry + (target_key,))

    top_key: tuple[Optional[str], str] = (top.file_id, top.name)
    _visit(top, top.name, (top_key,))
    return entries


def resolve_top_module(design: NetlistDesign) -> Optional[NetlistModule]:
    """Resolve top module using current NetlistIR top/entry-file semantics."""
    result = resolve_top_symbol(
        design.modules,
        top_name=design.top,
        entry_file_id=design.entry_file_id,
        policy=PERMISSIVE_TOP_POLICY,
    )
    return result.symbol


__all__ = ["HierarchyEntry", "resolve_top_module", "traverse_hierarchy"]
