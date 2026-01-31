"""Render Markdown documentation from ASDL docstrings."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Sequence

from asdl.ast.models import AsdlDocument, ModuleDecl, PatternDecl
from asdl.ast.parser import parse_file
from asdl.diagnostics.renderers import render_text

from .docstrings import DocPath, DocstringIndex, extract_docstrings_from_file


class MarkdownRenderError(RuntimeError):
    """Raised when Markdown rendering cannot proceed."""


def render_markdown_from_file(path: str | Path) -> str:
    """Render Markdown documentation for an ASDL file on disk.

    Args:
        path: Path to the ASDL YAML source file.

    Returns:
        The rendered Markdown document.

    Raises:
        MarkdownRenderError: If parsing diagnostics are emitted.
    """
    file_path = Path(path)
    document, diagnostics = parse_file(str(file_path))
    if diagnostics:
        message = render_text(diagnostics)
        raise MarkdownRenderError(message)
    if document is None:
        raise MarkdownRenderError(f"Failed to parse ASDL file: {file_path}")

    docstrings = extract_docstrings_from_file(file_path)
    return render_markdown(document, docstrings, file_path=file_path)


def render_markdown(
    document: AsdlDocument,
    docstrings: DocstringIndex,
    *,
    file_path: Optional[Path] = None,
    title: Optional[str] = None,
) -> str:
    """Render Markdown documentation from a parsed ASDL document.

    Args:
        document: Parsed ASDL document.
        docstrings: Extracted docstrings for the source document.
        file_path: Optional file path for fallback title generation.
        title: Optional explicit document title override.

    Returns:
        Markdown documentation as a string.
    """
    doc_title = title or _document_title(document, file_path)
    overview, overview_module = _document_overview(document, docstrings)
    file_namespace = _file_namespace(doc_title, file_path)
    doc_ref_name = _document_ref_name(doc_title, file_path)

    lines: list[str] = [f"# {doc_title}", ""]
    lines.extend(_render_asdl_blocks("doc", [doc_ref_name], label=True))
    lines.append("")

    if overview:
        lines.extend(["## Overview", overview, ""])

    if document.imports:
        lines.extend(_render_imports(document.imports, docstrings, file_namespace=file_namespace))
        lines.append("")

    if document.modules:
        for module_name, module in document.modules.items():
            lines.extend(
                _render_module(
                    module_name,
                    module,
                    docstrings,
                    skip_notes=overview_module == module_name,
                )
            )
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _document_title(document: AsdlDocument, file_path: Optional[Path]) -> str:
    if document.top:
        return document.top
    if document.modules and len(document.modules) == 1:
        return next(iter(document.modules.keys()))
    if file_path is not None:
        return file_path.stem
    return "ASDL Document"


def _file_namespace(doc_title: str, file_path: Optional[Path]) -> str:
    """Return the file-scoped namespace for ASDL references.

    Args:
        doc_title: Document title used as a fallback namespace.
        file_path: Optional source file path.

    Returns:
        Namespace string for file-scoped references.
    """
    if file_path is not None:
        return file_path.stem
    return doc_title or "asdl"


def _document_ref_name(doc_title: str, file_path: Optional[Path]) -> str:
    """Build the reference name for the document-level ASDL object.

    Args:
        doc_title: Document title used as a fallback base name.
        file_path: Optional source file path.

    Returns:
        Document-level reference name.
    """
    return f"{_file_namespace(doc_title, file_path)}_doc"


def _document_overview(
    document: AsdlDocument, docstrings: DocstringIndex
) -> tuple[Optional[str], Optional[str]]:
    if docstrings.file_docstring:
        return docstrings.file_docstring, None

    module_name = None
    if document.top:
        module_name = document.top
    elif document.modules and len(document.modules) == 1:
        module_name = next(iter(document.modules.keys()))

    if module_name:
        module_doc = _docstring_text(docstrings, ("modules", module_name))
        if module_doc:
            return module_doc, module_name

    return None, None


def _render_imports(
    imports: dict[str, str],
    docstrings: DocstringIndex,
    *,
    file_namespace: str,
) -> list[str]:
    """Render the imports section, including ASDL domain directives.

    Args:
        imports: Mapping of import alias to file path.
        docstrings: Extracted docstrings.
        file_namespace: File-scoped namespace used for import references.

    Returns:
        Rendered Markdown lines for the imports section.
    """
    rows: list[Sequence[str]] = []
    import_targets: list[str] = []
    for alias, path in imports.items():
        doc = _docstring_text(docstrings, ("imports", alias)) or ""
        rows.append((alias, path, doc))
        import_targets.append(_qualify_file_name(file_namespace, alias))

    lines = ["## Imports"]
    if import_targets:
        lines.append("")
        lines.extend(_render_asdl_blocks("import", import_targets))
        lines.append("")
    lines.extend(_render_table(["Alias", "Path", "Description"], rows))
    return lines


def _render_module(
    name: str,
    module: ModuleDecl,
    docstrings: DocstringIndex,
    *,
    skip_notes: bool,
) -> list[str]:
    lines = [f"## Module `{name}`", ""]
    lines.extend(_render_asdl_blocks("module", [name]))
    lines.append("")

    module_doc = _docstring_text(docstrings, ("modules", name))
    if module_doc and not skip_notes:
        lines.extend(["### Notes", module_doc, ""])

    interface_rows = _build_interface_rows(name, module, docstrings)
    if interface_rows:
        port_names = _module_port_names(module)
        lines.extend(["### Interface", ""])
        lines.extend(
            _render_asdl_blocks(
                "port",
                [_qualify_module_name(name, port_name) for port_name in port_names],
            )
        )
        lines.append("")
        lines.extend(_render_table(["Name", "Kind", "Direction", "Description"], interface_rows))
        lines.append("")

    variable_rows = _build_variable_rows(name, module, docstrings)
    if variable_rows:
        variable_names = list((module.variables or {}).keys())
        lines.extend(["### Variables", ""])
        lines.extend(
            _render_asdl_blocks(
                "var",
                [_qualify_module_name(name, var_name) for var_name in variable_names],
            )
        )
        lines.append("")
        lines.extend(_render_table(["Name", "Default", "Description"], variable_rows))
        lines.append("")

    instance_rows = _build_instance_rows(name, module, docstrings)
    if instance_rows:
        instance_names = list((module.instances or {}).keys())
        lines.extend(["### Instances", ""])
        lines.extend(
            _render_asdl_blocks(
                "inst",
                [_qualify_module_name(name, inst_name) for inst_name in instance_names],
            )
        )
        lines.append("")
        lines.extend(
            _render_table(["Instance", "Ref", "Params", "Description"], instance_rows)
        )
        lines.append("")

    net_lines = _render_nets(name, module, docstrings)
    if net_lines:
        lines.extend(net_lines)
        lines.append("")

    pattern_rows = _build_pattern_rows(name, module, docstrings)
    if pattern_rows:
        pattern_names = list((module.patterns or {}).keys())
        lines.extend(["### Patterns", ""])
        lines.extend(
            _render_asdl_blocks(
                "pattern",
                [_qualify_module_name(name, pattern_name) for pattern_name in pattern_names],
            )
        )
        lines.append("")
        lines.extend(
            _render_table(["Name", "Expression", "Axis", "Description"], pattern_rows)
        )
        lines.append("")

    return lines


def _build_interface_rows(
    module_name: str, module: ModuleDecl, docstrings: DocstringIndex
) -> list[Sequence[str]]:
    rows: list[Sequence[str]] = []
    nets = module.nets or {}
    for net_name in nets.keys():
        if not net_name.startswith("$"):
            continue
        doc = _docstring_text(docstrings, ("modules", module_name, "nets", net_name))
        rows.append((net_name, "", "", doc or ""))
    return rows


def _build_variable_rows(
    module_name: str, module: ModuleDecl, docstrings: DocstringIndex
) -> list[Sequence[str]]:
    rows: list[Sequence[str]] = []
    variables = module.variables or {}
    for name, value in variables.items():
        doc = _docstring_text(docstrings, ("modules", module_name, "variables", name))
        rows.append((name, _stringify_value(value), doc or ""))
    return rows


def _build_instance_rows(
    module_name: str, module: ModuleDecl, docstrings: DocstringIndex
) -> list[Sequence[str]]:
    rows: list[Sequence[str]] = []
    instances = module.instances or {}
    for inst_name, expr in instances.items():
        ref, params = _parse_instance_expr(expr)
        doc = _docstring_text(docstrings, ("modules", module_name, "instances", inst_name))
        rows.append((inst_name, ref, params, doc or ""))
    return rows


def _render_nets(
    module_name: str, module: ModuleDecl, docstrings: DocstringIndex
) -> list[str]:
    nets = module.nets or {}
    if not nets:
        return []

    lines = ["### Nets"]
    nets_path: DocPath = ("modules", module_name, "nets")
    sections = docstrings.section_docstrings(nets_path)
    rendered_keys: set[str] = set()

    for section in sections:
        lines.append(f"#### {section.title}")
        lines.append("")
        lines.extend(
            _render_asdl_blocks(
                "net",
                [_qualify_module_name(module_name, net_name) for net_name in section.keys],
            )
        )
        lines.append("")
        lines.extend(_render_net_table(module_name, docstrings, nets, section.keys))
        rendered_keys.update(section.keys)

    remaining = [name for name in nets.keys() if name not in rendered_keys]
    if remaining:
        if sections:
            lines.append("#### Other nets")
        lines.append("")
        lines.extend(
            _render_asdl_blocks(
                "net",
                [_qualify_module_name(module_name, net_name) for net_name in remaining],
            )
        )
        lines.append("")
        lines.extend(_render_net_table(module_name, docstrings, nets, remaining))

    return lines


def _render_net_table(
    module_name: str,
    docstrings: DocstringIndex,
    nets: dict[str, Iterable[str]],
    keys: Iterable[str],
) -> list[str]:
    rows: list[Sequence[str]] = []
    for net_name in keys:
        endpoints = nets.get(net_name, [])
        endpoints_text = ", ".join(str(endpoint) for endpoint in endpoints)
        doc = _docstring_text(docstrings, ("modules", module_name, "nets", net_name))
        rows.append((net_name, endpoints_text, doc or ""))
    return _render_table(["Name", "Endpoints", "Description"], rows)


def _build_pattern_rows(
    module_name: str, module: ModuleDecl, docstrings: DocstringIndex
) -> list[Sequence[str]]:
    rows: list[Sequence[str]] = []
    patterns = module.patterns or {}
    for name, value in patterns.items():
        axis = name
        expr = ""
        if isinstance(value, PatternDecl):
            expr = value.expr
            axis = value.tag or name
        else:
            expr = value
        doc = _docstring_text(docstrings, ("modules", module_name, "patterns", name))
        rows.append((name, expr, axis, doc or ""))
    return rows


def _module_port_names(module: ModuleDecl) -> list[str]:
    """Return ordered port names derived from `$`-prefixed nets.

    Args:
        module: Module declaration to inspect.

    Returns:
        Ordered list of `$`-prefixed net names.
    """
    nets = module.nets or {}
    return [name for name in nets.keys() if name.startswith("$")]


def _qualify_module_name(module_name: str, name: str) -> str:
    """Build a module-scoped reference name.

    Args:
        module_name: Module namespace.
        name: Object name within the module.

    Returns:
        Qualified name using the ``module::name`` scheme.
    """
    return f"{module_name}::{name}"


def _qualify_file_name(file_namespace: str, alias: str) -> str:
    """Build a file-scoped reference name.

    Args:
        file_namespace: File namespace string.
        alias: Import alias within the file.

    Returns:
        Qualified name using the ``file::alias`` scheme.
    """
    return f"{file_namespace}::{alias}"


def _render_asdl_block(objtype: str, name: str, *, label: bool = False) -> list[str]:
    """Render a MyST directive (and optional label) for an ASDL object.

    Args:
        objtype: ASDL domain object type.
        name: Qualified reference name.
        label: Whether to emit a MyST label line.

    Returns:
        Markdown lines for the label/directive block.
    """
    lines: list[str] = []
    if label:
        lines.append(f"({name})=")
    lines.append(f"```{{asdl:{objtype}}} {name}")
    lines.append("```")
    return lines


def _render_asdl_blocks(
    objtype: str,
    names: Iterable[str],
    *,
    label: bool = False,
) -> list[str]:
    """Render directive blocks for a sequence of ASDL objects.

    Args:
        objtype: ASDL domain object type.
        names: Qualified reference names to register.
        label: Whether to emit MyST labels for each object.

    Returns:
        Markdown lines for the directive blocks.
    """
    lines: list[str] = []
    for name in names:
        lines.extend(_render_asdl_block(objtype, name, label=label))
        lines.append("")
    if lines:
        lines.pop()
    return lines


def _render_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> list[str]:
    if not rows:
        return []
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        cells = ["" if cell is None else str(cell) for cell in row]
        lines.append("| " + " | ".join(_sanitize_cell(cell) for cell in cells) + " |")
    return lines


def _sanitize_cell(text: str) -> str:
    normalized = text.replace("\n", "<br>").replace("|", "\\|").strip()
    return normalized


def _docstring_text(docstrings: DocstringIndex, path: DocPath) -> Optional[str]:
    key_doc = docstrings.key_docstring(path)
    if not key_doc:
        return None
    text = key_doc.text.strip()
    return text or None


def _parse_instance_expr(expr: str) -> tuple[str, str]:
    tokens = expr.split()
    if not tokens:
        return "", ""
    ref = tokens[0]
    params = " ".join(tokens[1:])
    return ref, params


def _stringify_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


__all__ = ["MarkdownRenderError", "render_markdown", "render_markdown_from_file"]
