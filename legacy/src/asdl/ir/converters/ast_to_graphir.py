"""AST to GraphIR conversion for ASDL documents and import graphs."""

from __future__ import annotations

from typing import List, Optional, Tuple

from asdl.ast import AsdlDocument, elaborate_named_patterns
from asdl.diagnostics import Diagnostic
from asdl.imports import ImportGraph, NameEnv, ProgramDB
from asdl.ir.converters.ast_to_graphir_context import GraphIrSessionContext
from asdl.ir.converters.ast_to_graphir_lowering import (
    UNRESOLVED_UNQUALIFIED,
    lower_document_ops,
)
from asdl.ir.converters.ast_to_graphir_utils import diagnostic
from asdl.ir.graphir import ProgramOp


def convert_document(
    document: AsdlDocument,
    *,
    name_env: Optional[NameEnv] = None,
    program_db: Optional[ProgramDB] = None,
) -> Tuple[Optional[ProgramOp], List[Diagnostic]]:
    """Convert a single ASDL document into GraphIR.

    Args:
        document: Parsed AST document.
        name_env: Optional name environment for file identity.
        program_db: Optional program database for symbol resolution.

    Returns:
        The GraphIR program op (or None on error) and diagnostics.
    """
    diagnostics: List[Diagnostic] = []
    had_error = False

    named_diags, named_error = elaborate_named_patterns(document)
    diagnostics.extend(named_diags)
    had_error = had_error or named_error

    session = GraphIrSessionContext.for_document(program_db=program_db)
    doc_context = session.document_context(document, name_env=name_env)

    modules, devices, doc_diags, doc_error = lower_document_ops(doc_context)
    diagnostics.extend(doc_diags)
    had_error = had_error or doc_error

    entry_id: Optional[str] = None
    if document.top is not None:
        entry_id = doc_context.module_ids.get(document.top)
        if entry_id is None:
            diagnostics.append(
                diagnostic(
                    UNRESOLVED_UNQUALIFIED,
                    f"Unresolved top module '{document.top}'.",
                    getattr(document, "_loc", None),
                )
            )
            had_error = True

    program = ProgramOp(region=modules + devices, entry=entry_id)
    if had_error:
        return None, diagnostics
    return program, diagnostics


def convert_import_graph(
    graph: ImportGraph,
) -> Tuple[Optional[ProgramOp], List[Diagnostic]]:
    """Convert an import graph into a unified GraphIR program.

    Args:
        graph: Resolved import graph with documents, name envs, and ProgramDB.

    Returns:
        The GraphIR program op (or None on error) and diagnostics.
    """
    diagnostics: List[Diagnostic] = []
    had_error = False
    session = GraphIrSessionContext.for_import_graph(graph)
    file_order = session.file_order

    ops: List[object] = []
    for file_id in file_order:
        document = graph.documents.get(file_id)
        if document is None:
            diagnostics.append(
                diagnostic(
                    UNRESOLVED_UNQUALIFIED,
                    f"Import graph missing document '{file_id}'.",
                    None,
                )
            )
            had_error = True
            continue
        doc_context = session.document_context(
            document,
            name_env=graph.name_envs.get(file_id),
            file_path=file_id,
        )
        named_diags, named_error = elaborate_named_patterns(document)
        diagnostics.extend(named_diags)
        had_error = had_error or named_error
        modules, devices, doc_diags, doc_error = lower_document_ops(doc_context)
        ops.extend(modules)
        ops.extend(devices)
        diagnostics.extend(doc_diags)
        had_error = had_error or doc_error

    entry_id: Optional[str] = None
    entry_document = graph.documents.get(graph.entry_file)
    if entry_document is None:
        diagnostics.append(
            diagnostic(
                UNRESOLVED_UNQUALIFIED,
                f"Import graph missing entry document '{graph.entry_file}'.",
                None,
            )
        )
        had_error = True
    elif entry_document.top is not None:
        entry_id = session.module_ids_by_file.get(graph.entry_file, {}).get(
            entry_document.top
        )
        if entry_id is None:
            diagnostics.append(
                diagnostic(
                    UNRESOLVED_UNQUALIFIED,
                    f"Unresolved top module '{entry_document.top}'.",
                    getattr(entry_document, "_loc", None),
                )
            )
            had_error = True

    program = ProgramOp(
        region=ops,
        entry=entry_id,
        file_order=[str(file_id) for file_id in file_order],
    )
    if had_error:
        return None, diagnostics
    return program, diagnostics


__all__ = ["convert_document", "convert_import_graph"]
