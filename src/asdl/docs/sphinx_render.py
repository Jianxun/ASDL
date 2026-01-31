"""Render docutils nodes for ASDL documentation."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Sequence

from docutils import nodes

from asdl.ast.models import AsdlDocument, ModuleDecl, PatternDecl

from .docstrings import DocPath, DocstringIndex
from .sphinx_domain import make_asdl_target_id


def render_docutils(
    document: AsdlDocument,
    docstrings: DocstringIndex,
    *,
    file_path: Optional[Path] = None,
    title: Optional[str] = None,
) -> nodes.section:
    """Render docutils nodes for an ASDL document.

    Args:
        document: Parsed ASDL document.
        docstrings: Extracted docstrings for the source document.
        file_path: Optional file path for fallback title generation.
        title: Optional explicit document title override.

    Returns:
        A docutils section containing the rendered ASDL documentation tree.
    """
    doc_title = title or _document_title(document, file_path)
    overview, overview_module = _document_overview(document, docstrings)
    file_namespace = _file_namespace(doc_title, file_path)
    doc_ref_name = _document_ref_name(doc_title, file_path)

    root = nodes.section()
    root += nodes.title(text=doc_title)
    _append_targets(root, "doc", [doc_ref_name])

    if overview:
        overview_section = _section("Overview")
        _append_paragraphs(overview_section, overview)
        root += overview_section

    if document.imports:
        root += _render_imports(document.imports, docstrings, file_namespace=file_namespace)

    if document.modules:
        for module_name, module in document.modules.items():
            root += _render_module(
                module_name,
                module,
                docstrings,
                skip_notes=overview_module == module_name,
            )

    return root


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
) -> nodes.section:
    """Render an imports section.

    Args:
        imports: Mapping of import alias to file path.
        docstrings: Extracted docstrings.
        file_namespace: File-scoped namespace used for import references.

    Returns:
        Docutils section for the imports block.
    """
    rows: list[Sequence[str]] = []
    import_targets: list[str] = []
    for alias, path in imports.items():
        doc = _docstring_text(docstrings, ("imports", alias)) or ""
        rows.append((alias, path, doc))
        import_targets.append(_qualify_file_name(file_namespace, alias))

    section = _section("Imports")
    _append_targets(section, "import", import_targets)
    table = _render_table(["Alias", "Path", "Description"], rows)
    if table is not None:
        section += table
    return section


def _render_module(
    name: str,
    module: ModuleDecl,
    docstrings: DocstringIndex,
    *,
    skip_notes: bool,
) -> nodes.section:
    section = _section(f"Module `{name}`")
    _append_targets(section, "module", [name])

    module_doc = _docstring_text(docstrings, ("modules", name))
    if module_doc and not skip_notes:
        notes = _section("Notes")
        _append_paragraphs(notes, module_doc)
        section += notes

    interface_rows = _build_interface_rows(name, module, docstrings)
    if interface_rows:
        interface_section = _section("Interface")
        port_names = _module_port_names(module)
        _append_targets(
            interface_section,
            "port",
            [_qualify_module_name(name, port_name) for port_name in port_names],
        )
        table = _render_table(["Name", "Kind", "Direction", "Description"], interface_rows)
        if table is not None:
            interface_section += table
        section += interface_section

    variable_rows = _build_variable_rows(name, module, docstrings)
    if variable_rows:
        variable_section = _section("Variables")
        variable_names = list((module.variables or {}).keys())
        _append_targets(
            variable_section,
            "var",
            [_qualify_module_name(name, var_name) for var_name in variable_names],
        )
        table = _render_table(["Name", "Default", "Description"], variable_rows)
        if table is not None:
            variable_section += table
        section += variable_section

    instance_rows = _build_instance_rows(name, module, docstrings)
    if instance_rows:
        instance_section = _section("Instances")
        instance_names = list((module.instances or {}).keys())
        _append_targets(
            instance_section,
            "inst",
            [_qualify_module_name(name, inst_name) for inst_name in instance_names],
        )
        table = _render_table(["Instance", "Ref", "Params", "Description"], instance_rows)
        if table is not None:
            instance_section += table
        section += instance_section

    net_section = _render_nets(name, module, docstrings)
    if net_section is not None:
        section += net_section

    pattern_rows = _build_pattern_rows(name, module, docstrings)
    if pattern_rows:
        pattern_section = _section("Patterns")
        pattern_names = list((module.patterns or {}).keys())
        _append_targets(
            pattern_section,
            "pattern",
            [_qualify_module_name(name, pattern_name) for pattern_name in pattern_names],
        )
        table = _render_table(["Name", "Expression", "Axis", "Description"], pattern_rows)
        if table is not None:
            pattern_section += table
        section += pattern_section

    return section


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
) -> Optional[nodes.section]:
    nets = module.nets or {}
    if not nets:
        return None

    section = _section("Nets")
    nets_path: DocPath = ("modules", module_name, "nets")
    sections = docstrings.section_docstrings(nets_path)
    rendered_keys: set[str] = set()

    for bundle in sections:
        sub_section = _section(bundle.title)
        _append_targets(
            sub_section,
            "net",
            [_qualify_module_name(module_name, net_name) for net_name in bundle.keys],
        )
        table = _render_net_table(module_name, docstrings, nets, bundle.keys)
        if table is not None:
            sub_section += table
        section += sub_section
        rendered_keys.update(bundle.keys)

    remaining = [name for name in nets.keys() if name not in rendered_keys]
    if remaining:
        if sections:
            sub_section = _section("Other nets")
            _append_targets(
                sub_section,
                "net",
                [_qualify_module_name(module_name, net_name) for net_name in remaining],
            )
            table = _render_net_table(module_name, docstrings, nets, remaining)
            if table is not None:
                sub_section += table
            section += sub_section
        else:
            _append_targets(
                section,
                "net",
                [_qualify_module_name(module_name, net_name) for net_name in remaining],
            )
            table = _render_net_table(module_name, docstrings, nets, remaining)
            if table is not None:
                section += table

    return section


def _render_net_table(
    module_name: str,
    docstrings: DocstringIndex,
    nets: dict[str, Iterable[str]],
    keys: Iterable[str],
) -> Optional[nodes.table]:
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


def _render_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> Optional[nodes.table]:
    if not rows:
        return None

    table = nodes.table()
    tgroup = nodes.tgroup(cols=len(headers))
    table += tgroup
    for _ in headers:
        tgroup += nodes.colspec(colwidth=1)

    thead = nodes.thead()
    tgroup += thead
    header_row = nodes.row()
    for header in headers:
        entry = nodes.entry()
        entry += nodes.paragraph(text=str(header))
        header_row += entry
    thead += header_row

    tbody = nodes.tbody()
    tgroup += tbody
    for row in rows:
        row_node = nodes.row()
        for cell in row:
            entry = nodes.entry()
            text = "" if cell is None else str(cell)
            _append_paragraphs(entry, text)
            row_node += entry
        tbody += row_node

    return table


def _append_targets(container: nodes.Element, objtype: str, names: Iterable[str]) -> None:
    for name in names:
        target_id = make_asdl_target_id(objtype, name)
        target = nodes.target("", "", ids=[target_id])
        container += target


def _section(title: str) -> nodes.section:
    section = nodes.section()
    section += nodes.title(text=title)
    return section


def _append_paragraphs(container: nodes.Element, text: str) -> None:
    if text.strip() == "":
        container += nodes.paragraph(text="")
        return
    for chunk in text.strip().split("\n\n"):
        container += nodes.paragraph(text=chunk)


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


__all__ = ["render_docutils"]
