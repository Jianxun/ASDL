"""Lowering helpers for refactor pipeline artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from asdl.ast import AsdlDocument
from asdl.core.graph import ProgramGraph
from asdl.diagnostics import Diagnostic, Severity, format_code
from asdl.emit.netlist_ir import NetlistDesign
from asdl.imports.resolver import resolve_import_graph

from .ast_to_patterned_graph import (
    build_patterned_graph,
    build_patterned_graph_from_import_graph,
)
from .patterned_graph_to_atomized import (
    build_atomized_graph,
    build_atomized_graph_and_verify,
)
from .atomized_graph_to_netlist_ir import build_netlist_ir_design

NO_SPAN_NOTE = "No source span available."

PIPELINE_INPUT_ERROR = format_code("PASS", 101)


def run_netlist_ir_pipeline(
    document: Optional[AsdlDocument] = None,
    *,
    entry_file: Optional[Path] = None,
    file_id: Optional[str] = None,
    lib_roots: Optional[Iterable[Path]] = None,
    verify: bool = True,
) -> tuple[Optional[NetlistDesign], list[Diagnostic]]:
    """Parse and lower ASDL into a NetlistIR design.

    Args:
        document: Optional parsed AST document.
        entry_file: Optional file path to parse into an AST document.
        file_id: Optional file identifier to attach to module graphs.
        lib_roots: Optional library search roots for import resolution.
        verify: When True, run atomized graph verification.

    Returns:
        Tuple of (NetlistIR design or None, diagnostics).
    """
    diagnostics: list[Diagnostic] = []
    top_module_id: Optional[str] = None

    if entry_file is not None:
        if document is not None:
            diagnostics.append(
                _diagnostic(
                    PIPELINE_INPUT_ERROR,
                    "Provide either document or entry_file, not both.",
                )
            )
            return None, diagnostics
        import_graph, import_diags = resolve_import_graph(
            entry_file, lib_roots=lib_roots
        )
        diagnostics.extend(import_diags)
        if import_graph is None or _has_error_diagnostics(diagnostics):
            return None, diagnostics
        graph, lower_diags = build_patterned_graph_from_import_graph(import_graph)
        diagnostics.extend(lower_diags)
        if _has_error_diagnostics(diagnostics):
            return None, diagnostics
        entry_doc = import_graph.documents.get(import_graph.entry_file)
        top_module_id = _resolve_top_module_id(
            graph,
            entry_doc.top if entry_doc is not None else None,
            str(import_graph.entry_file),
        )
    else:
        if document is None:
            diagnostics.append(
                _diagnostic(PIPELINE_INPUT_ERROR, "Pipeline requires a document or entry file.")
            )
            return None, diagnostics
        graph, lower_diags = build_patterned_graph(document, file_id=file_id)
        diagnostics.extend(lower_diags)
        if _has_error_diagnostics(diagnostics):
            return None, diagnostics
        top_module_id = _resolve_top_module_id(
            graph, document.top, file_id
        )

    if verify:
        atomized, atomized_diags = build_atomized_graph_and_verify(graph)
    else:
        atomized, atomized_diags = build_atomized_graph(graph)
    diagnostics.extend(atomized_diags)
    if _has_error_diagnostics(diagnostics):
        return None, diagnostics

    design = build_netlist_ir_design(atomized, top_module_id=top_module_id)
    return design, diagnostics


def _resolve_top_module_id(
    graph: ProgramGraph,
    top_name: Optional[str],
    file_id: Optional[str],
) -> Optional[str]:
    if top_name is None:
        return None
    for module_id, module in graph.modules.items():
        if module.name != top_name:
            continue
        if file_id is None or module.file_id == file_id:
            return module_id
    return None


def _has_error_diagnostics(diagnostics: Iterable[Diagnostic]) -> bool:
    return any(
        diagnostic.severity in (Severity.ERROR, Severity.FATAL)
        for diagnostic in diagnostics
    )


def _diagnostic(code: str, message: str) -> Diagnostic:
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        message=message,
        primary_span=None,
        notes=[NO_SPAN_NOTE],
        source="netlist-ir-pipeline",
    )

__all__ = [
    "build_atomized_graph",
    "build_atomized_graph_and_verify",
    "build_patterned_graph",
    "build_patterned_graph_from_import_graph",
    "build_netlist_ir_design",
    "run_netlist_ir_pipeline",
]
