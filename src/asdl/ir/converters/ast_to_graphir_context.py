"""Conversion context helpers for AST->GraphIR lowering."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from asdl.ast import AsdlDocument
from asdl.imports import ImportGraph, NameEnv, ProgramDB

from .ast_to_graphir_symbols import (
    GraphIdAllocator,
    ResolvedSymbol,
    allocate_document_ids,
    allocate_symbol_ids,
    build_symbol_table,
    build_symbol_tables_by_file,
    import_graph_file_order,
)


@dataclass(frozen=True)
class GraphIrDocumentContext:
    """Per-document context for AST->GraphIR conversion.

    Args:
        document: Parsed AST document.
        file_id: Source file identifier string.
        module_ids: Mapping from module names to IDs.
        device_ids: Mapping from device names to IDs.
        symbol_table: Mapping from symbol names to resolved IDs.
        id_allocator: Shared ID allocator for sub-entities.
        name_env: Optional name environment for import resolution.
        program_db: Optional program database for qualified symbol resolution.
        global_symbols: Optional symbol tables keyed by file ID.
    """

    document: AsdlDocument
    file_id: str
    module_ids: Dict[str, str]
    device_ids: Dict[str, str]
    symbol_table: Dict[str, List[ResolvedSymbol]]
    id_allocator: GraphIdAllocator
    name_env: Optional[NameEnv]
    program_db: Optional[ProgramDB]
    global_symbols: Optional[Dict[Path, Dict[str, List[ResolvedSymbol]]]]


@dataclass(frozen=True)
class GraphIrSessionContext:
    """Session-scoped context for AST->GraphIR conversion.

    Args:
        id_allocator: Shared ID allocator for the conversion session.
        program_db: Optional program database for qualified symbol resolution.
        file_order: Deterministic file ordering for import graphs.
        module_ids_by_file: Module IDs keyed by file ID.
        device_ids_by_file: Device IDs keyed by file ID.
        symbols_by_file: Optional symbol tables keyed by file ID.
    """

    id_allocator: GraphIdAllocator
    program_db: Optional[ProgramDB]
    file_order: List[Path]
    module_ids_by_file: Dict[Path, Dict[str, str]]
    device_ids_by_file: Dict[Path, Dict[str, str]]
    symbols_by_file: Optional[Dict[Path, Dict[str, List[ResolvedSymbol]]]]

    @classmethod
    def for_document(
        cls,
        *,
        program_db: Optional[ProgramDB] = None,
    ) -> "GraphIrSessionContext":
        """Create a session context for a single-document conversion.

        Args:
            program_db: Optional program database for qualified resolution.

        Returns:
            Initialized session context.
        """
        return cls(
            id_allocator=GraphIdAllocator(),
            program_db=program_db,
            file_order=[],
            module_ids_by_file={},
            device_ids_by_file={},
            symbols_by_file=None,
        )

    @classmethod
    def for_import_graph(cls, graph: ImportGraph) -> "GraphIrSessionContext":
        """Create a session context for an import graph conversion.

        Args:
            graph: Import graph with resolved documents.

        Returns:
            Initialized session context.
        """
        file_order = import_graph_file_order(graph)
        id_allocator = GraphIdAllocator()
        module_ids_by_file, device_ids_by_file = allocate_symbol_ids(
            graph,
            file_order,
            id_allocator,
        )
        symbols_by_file = build_symbol_tables_by_file(
            module_ids_by_file,
            device_ids_by_file,
        )
        return cls(
            id_allocator=id_allocator,
            program_db=graph.program_db,
            file_order=file_order,
            module_ids_by_file=module_ids_by_file,
            device_ids_by_file=device_ids_by_file,
            symbols_by_file=symbols_by_file,
        )

    def document_context(
        self,
        document: AsdlDocument,
        *,
        name_env: Optional[NameEnv] = None,
        file_path: Optional[Path] = None,
    ) -> GraphIrDocumentContext:
        """Build per-document context using session state.

        Args:
            document: Parsed AST document to convert.
            name_env: Optional name environment for import resolution.
            file_path: Optional file path for import graph contexts.

        Returns:
            Initialized document context.
        """
        if self.symbols_by_file is not None and file_path is not None:
            module_ids = self.module_ids_by_file.get(file_path, {})
            device_ids = self.device_ids_by_file.get(file_path, {})
            symbol_table = self.symbols_by_file.get(file_path, {})
            file_id = str(file_path)
            global_symbols = self.symbols_by_file
        else:
            file_id = resolve_file_id(document, name_env)
            module_ids, device_ids = allocate_document_ids(
                document,
                self.id_allocator,
            )
            symbol_table = build_symbol_table(module_ids, device_ids)
            global_symbols = None
        return GraphIrDocumentContext(
            document=document,
            file_id=file_id,
            module_ids=module_ids,
            device_ids=device_ids,
            symbol_table=symbol_table,
            id_allocator=self.id_allocator,
            name_env=name_env,
            program_db=self.program_db,
            global_symbols=global_symbols,
        )


def resolve_file_id(document: AsdlDocument, name_env: Optional[NameEnv]) -> str:
    """Resolve a file identifier for GraphIR metadata.

    Args:
        document: AST document to inspect for location metadata.
        name_env: Optional name environment for file identity.

    Returns:
        A file identifier string.
    """
    if name_env is not None:
        return str(name_env.file_id)
    loc = getattr(document, "_loc", None)
    if loc is not None and loc.file:
        return loc.file
    return "<string>"


__all__ = [
    "GraphIrDocumentContext",
    "GraphIrSessionContext",
    "resolve_file_id",
]
