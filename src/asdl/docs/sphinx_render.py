"""Render docutils nodes for ASDL documentation."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from docutils import nodes

from asdl.ast.models import AsdlDocument

from .docstrings import DocstringIndex
from .render_helpers import (
    _append_paragraphs,
    _append_targets,
    _build_render_context,
    _document_overview,
    _document_ref_name,
    _document_title,
    _file_namespace,
    _render_imports,
    _render_module,
    _render_top_module_section,
    _section,
)


def render_docutils(
    document: AsdlDocument,
    docstrings: DocstringIndex,
    *,
    file_path: Optional[Path] = None,
    title: Optional[str] = None,
    sphinx_env: Optional[object] = None,
) -> nodes.section:
    """Render docutils nodes for an ASDL document.

    Args:
        document: Parsed ASDL document.
        docstrings: Extracted docstrings for the source document.
        file_path: Optional file path for fallback title generation.
        title: Optional explicit document title override when no file path is available.
        sphinx_env: Optional Sphinx environment for cross-reference lookups.

    Returns:
        A docutils section containing the rendered ASDL documentation tree.
    """
    if file_path is None and title is not None:
        doc_title = title
    else:
        doc_title = _document_title(document, file_path)
    overview = _document_overview(document, docstrings)
    file_namespace = _file_namespace(doc_title, file_path)
    doc_ref_name = _document_ref_name(doc_title, file_path)
    context = _build_render_context(document, file_path, sphinx_env)

    root = nodes.section()
    root += nodes.title(text=doc_title)
    _append_targets(root, "doc", [doc_ref_name])

    if overview:
        overview_section = _section("Overview")
        _append_paragraphs(overview_section, overview, preserve_line_breaks=True)
        root += overview_section

    if document.imports:
        root += _render_imports(document.imports, docstrings, file_namespace=file_namespace)

    top_section = _render_top_module_section(document, context)
    if top_section is not None:
        root += top_section

    if document.modules:
        modules_section = _section("Modules")
        for module_name, module in document.modules.items():
            modules_section += _render_module(
                module_name,
                module,
                docstrings,
                context=context,
            )
        root += modules_section

    return root


__all__ = ["render_docutils"]
