"""Symbol table and ID allocation helpers for AST->GraphIR conversion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Set, Tuple

from asdl.ast import AsdlDocument
from asdl.imports import ImportGraph


@dataclass(frozen=True)
class ResolvedSymbol:
    """Resolved symbol metadata for GraphIR instance references.

    Args:
        kind: Symbol kind ("module" or "device").
        sym_id: Stable symbol identifier.
    """

    kind: str
    sym_id: str


class GraphIdAllocator:
    """Deterministic ID generator for GraphIR entities.

    IDs are scoped by a prefix to preserve readability while keeping string
    values stable across a single conversion session.
    """

    def __init__(self) -> None:
        self._counts: Dict[str, int] = {}

    def next(self, prefix: str) -> str:
        """Return the next ID for a given prefix.

        Args:
            prefix: Prefix indicating the entity type.

        Returns:
            The next stable ID string.
        """
        count = self._counts.get(prefix, 0) + 1
        self._counts[prefix] = count
        return f"{prefix}{count}"


def allocate_document_ids(
    document: AsdlDocument,
    id_allocator: GraphIdAllocator,
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Allocate stable IDs for modules and devices in a document.

    Args:
        document: AST document to inspect.
        id_allocator: Shared ID allocator.

    Returns:
        Tuple of module IDs and device IDs keyed by name.
    """
    module_ids = {
        name: id_allocator.next("m") for name in (document.modules or {}).keys()
    }
    device_ids = {
        name: id_allocator.next("d") for name in (document.devices or {}).keys()
    }
    return module_ids, device_ids


def import_graph_file_order(graph: ImportGraph) -> List[Path]:
    """Return the deterministic file order for an import graph.

    Args:
        graph: Import graph with resolved imports.

    Returns:
        Ordered list of file IDs (entry first, then imports in resolution order).
    """
    order: List[Path] = []
    seen: Set[Path] = set()

    def visit(file_id: Path) -> None:
        if file_id in seen:
            return
        seen.add(file_id)
        order.append(file_id)
        for resolved in graph.imports.get(file_id, {}).values():
            visit(resolved)

    visit(graph.entry_file)
    for file_id in graph.documents.keys():
        if file_id not in seen:
            order.append(file_id)
    return order


def allocate_symbol_ids(
    graph: ImportGraph,
    file_order: Sequence[Path],
    id_allocator: GraphIdAllocator,
) -> Tuple[Dict[Path, Dict[str, str]], Dict[Path, Dict[str, str]]]:
    """Allocate stable IDs for modules and devices across files.

    Args:
        graph: Import graph with resolved documents.
        file_order: Deterministic file ordering for ID assignment.
        id_allocator: Shared ID allocator.

    Returns:
        Tuple of module IDs and device IDs keyed by file ID.
    """
    module_ids_by_file: Dict[Path, Dict[str, str]] = {}
    device_ids_by_file: Dict[Path, Dict[str, str]] = {}
    for file_id in file_order:
        document = graph.documents.get(file_id)
        if document is None:
            module_ids_by_file[file_id] = {}
            device_ids_by_file[file_id] = {}
            continue
        module_ids_by_file[file_id] = {
            name: id_allocator.next("m") for name in (document.modules or {}).keys()
        }
        device_ids_by_file[file_id] = {
            name: id_allocator.next("d") for name in (document.devices or {}).keys()
        }
    return module_ids_by_file, device_ids_by_file


def build_symbol_table(
    module_ids: Dict[str, str],
    device_ids: Dict[str, str],
) -> Dict[str, List[ResolvedSymbol]]:
    """Build a symbol table for local module/device names.

    Args:
        module_ids: Mapping from module names to IDs.
        device_ids: Mapping from device names to IDs.

    Returns:
        Mapping from symbol name to resolved symbol metadata.
    """
    table: Dict[str, List[ResolvedSymbol]] = {}
    for name, module_id in module_ids.items():
        table.setdefault(name, []).append(ResolvedSymbol("module", module_id))
    for name, device_id in device_ids.items():
        table.setdefault(name, []).append(ResolvedSymbol("device", device_id))
    return table


def build_symbol_tables_by_file(
    module_ids_by_file: Dict[Path, Dict[str, str]],
    device_ids_by_file: Dict[Path, Dict[str, str]],
) -> Dict[Path, Dict[str, List[ResolvedSymbol]]]:
    """Build per-file symbol tables for module/device IDs.

    Args:
        module_ids_by_file: Module ID mappings keyed by file ID.
        device_ids_by_file: Device ID mappings keyed by file ID.

    Returns:
        Mapping from file IDs to symbol tables.
    """
    tables: Dict[Path, Dict[str, List[ResolvedSymbol]]] = {}
    for file_id, module_ids in module_ids_by_file.items():
        device_ids = device_ids_by_file.get(file_id, {})
        tables[file_id] = build_symbol_table(module_ids, device_ids)
    for file_id, device_ids in device_ids_by_file.items():
        if file_id in tables:
            continue
        tables[file_id] = build_symbol_table({}, device_ids)
    return tables


__all__ = [
    "GraphIdAllocator",
    "ResolvedSymbol",
    "allocate_document_ids",
    "allocate_symbol_ids",
    "build_symbol_table",
    "build_symbol_tables_by_file",
    "import_graph_file_order",
]
