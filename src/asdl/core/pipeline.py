"""Pipeline helpers for PatternedGraph generation."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from asdl.ast import AsdlDocument
from asdl.diagnostics import Diagnostic, Severity, format_code
from asdl.imports.resolver import resolve_import_graph
from asdl.lowering.ast_to_patterned_graph import (
    build_patterned_graph,
    build_patterned_graph_from_import_graph,
)

from .graph import ModuleGraph, ProgramGraph

NO_SPAN_NOTE = "No source span available."

PIPELINE_INPUT_ERROR = format_code("PASS", 100)


def run_patterned_graph_pipeline(
    document: Optional[AsdlDocument] = None,
    *,
    entry_file: Optional[Path] = None,
    file_id: Optional[str] = None,
    lib_roots: Optional[Iterable[Path]] = None,
) -> tuple[ProgramGraph | None, list[Diagnostic]]:
    """Parse and lower ASDL into a PatternedGraph program.

    Args:
        document: Optional parsed AST document.
        entry_file: Optional path to parse into an AST document.
        file_id: Optional file identifier to attach when using document input.
        lib_roots: Optional library search roots for import resolution.

    Returns:
        Tuple of (ProgramGraph or None, diagnostics).
    """
    diagnostics: list[Diagnostic] = []
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
        return graph, diagnostics

    if document is None:
        diagnostics.append(
            _diagnostic(PIPELINE_INPUT_ERROR, "Pipeline requires a document or entry file.")
        )
        return None, diagnostics

    graph, lower_diags = build_patterned_graph(document, file_id=file_id)
    diagnostics.extend(lower_diags)
    if _has_error_diagnostics(diagnostics):
        return None, diagnostics
    return graph, diagnostics


def list_entry_modules(graph: ProgramGraph, entry_file: Path) -> list[ModuleGraph]:
    """Return modules defined in the entry file.

    Args:
        graph: Program graph to query.
        entry_file: Entry file path used for compilation.

    Returns:
        Sorted list of module graphs originating from the entry file.
    """
    entry_id = str(Path(entry_file).resolve())
    modules = [
        module
        for module in graph.modules.values()
        if module.file_id == entry_id
    ]
    return sorted(modules, key=lambda module: (module.name, module.module_id))


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
        source="patterned-graph-pipeline",
    )


__all__ = ["list_entry_modules", "run_patterned_graph_pipeline"]
