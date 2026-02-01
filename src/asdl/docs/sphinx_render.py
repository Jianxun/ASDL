"""Render docutils nodes for ASDL documentation."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Iterable, Optional, Sequence

from docutils import nodes

from asdl.ast.models import AsdlDocument, ModuleDecl, PatternDecl

from .depgraph import DependencyGraph, DepGraphModule, instance_identifier, module_identifier
from .docstrings import DocPath, DocstringIndex
from .sphinx_domain import ASDL_DEPGRAPH_ENV_KEY, ASDL_DOMAIN_NAME, make_asdl_target_id

try:  # pragma: no cover - optional when Sphinx is missing.
    from sphinx import addnodes

    SPHINX_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised when Sphinx is unavailable.
    addnodes = None  # type: ignore[assignment]
    SPHINX_AVAILABLE = False


@dataclass(frozen=True)
class DepGraphIndex:
    """Index dependency graph data for renderer lookups.

    Attributes:
        modules_by_id: Mapping of module_id to module metadata.
        modules_by_file: Mapping of (file_id, module_name) to module metadata.
        edges_by_instance: Mapping of instance_id to referenced module_id.
        parents_by_module: Mapping of module_id to parent module_ids.
    """

    modules_by_id: dict[str, DepGraphModule]
    modules_by_file: dict[tuple[str, str], DepGraphModule]
    edges_by_instance: dict[str, str]
    parents_by_module: dict[str, list[str]]


@dataclass(frozen=True)
class RenderContext:
    """Context for rendering Sphinx-linked ASDL docs.

    Attributes:
        file_path: Optional file path for the ASDL document.
        file_id: Normalized file identifier string.
        graph_index: Dependency graph index for cross-reference lookups.
        base_dir: Base directory for relative path display.
        collision_names: Module names that need path disambiguation.
        sphinx_env: Sphinx environment for resolving xrefs.
        docname: Current Sphinx docname for xref nodes.
    """

    file_path: Optional[Path]
    file_id: Optional[str]
    graph_index: Optional[DepGraphIndex]
    base_dir: Optional[Path]
    collision_names: set[str]
    sphinx_env: Optional[object]
    docname: Optional[str]


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
    overview, overview_module = _document_overview(document, docstrings)
    file_namespace = _file_namespace(doc_title, file_path)
    doc_ref_name = _document_ref_name(doc_title, file_path)
    context = _build_render_context(document, file_path, sphinx_env)

    root = nodes.section()
    root += nodes.title(text=doc_title)
    _append_targets(root, "doc", [doc_ref_name])

    if overview:
        overview_section = _section("Overview")
        _append_paragraphs(overview_section, overview)
        root += overview_section

    top_section = _render_top_module_section(document, context)
    if top_section is not None:
        root += top_section

    if document.imports:
        root += _render_imports(document.imports, docstrings, file_namespace=file_namespace)

    if document.modules:
        for module_name, module in document.modules.items():
            root += _render_module(
                module_name,
                module,
                docstrings,
                skip_notes=overview_module == module_name,
                context=context,
            )

    return root


def _build_render_context(
    document: AsdlDocument,
    file_path: Optional[Path],
    sphinx_env: Optional[object],
) -> RenderContext:
    """Build rendering context for the current ASDL document."""
    file_id = _normalize_file_id(file_path)
    graph = _lookup_dependency_graph(sphinx_env)
    graph_index = _build_depgraph_index(graph) if graph is not None else None
    base_dir = _resolve_base_dir(file_path, sphinx_env)
    collision_names = _compute_collision_names(document, file_id, graph_index)
    docname = getattr(sphinx_env, "docname", None) if sphinx_env is not None else None
    return RenderContext(
        file_path=file_path,
        file_id=file_id,
        graph_index=graph_index,
        base_dir=base_dir,
        collision_names=collision_names,
        sphinx_env=sphinx_env,
        docname=docname,
    )


def _normalize_file_id(file_path: Optional[Path]) -> Optional[str]:
    if file_path is None:
        return None
    return str(file_path.resolve(strict=False))


def _lookup_dependency_graph(sphinx_env: Optional[object]) -> Optional[DependencyGraph]:
    if sphinx_env is None:
        return None
    return getattr(sphinx_env, ASDL_DEPGRAPH_ENV_KEY, None)


def _build_depgraph_index(graph: DependencyGraph) -> DepGraphIndex:
    modules_by_id = {module.module_id: module for module in graph.modules}
    modules_by_file = {
        (module.file_id, module.name): module for module in graph.modules
    }
    edges_by_instance = {
        edge.instance_id: edge.to_module_id for edge in graph.edges
    }
    parents_by_module: dict[str, list[str]] = {}
    for edge in graph.edges:
        parents_by_module.setdefault(edge.to_module_id, []).append(edge.from_module_id)
    for module_id, parent_ids in parents_by_module.items():
        parents_by_module[module_id] = list(dict.fromkeys(parent_ids))
    return DepGraphIndex(
        modules_by_id=modules_by_id,
        modules_by_file=modules_by_file,
        edges_by_instance=edges_by_instance,
        parents_by_module=parents_by_module,
    )


def _resolve_base_dir(
    file_path: Optional[Path],
    sphinx_env: Optional[object],
) -> Optional[Path]:
    if sphinx_env is not None:
        srcdir = getattr(sphinx_env, "srcdir", None)
        if srcdir:
            return Path(srcdir)
    if file_path is not None:
        return file_path.parent
    return None


def _compute_collision_names(
    document: AsdlDocument,
    file_id: Optional[str],
    graph_index: Optional[DepGraphIndex],
) -> set[str]:
    if graph_index is None or file_id is None:
        return set()
    referenced = _collect_referenced_modules(document, file_id, graph_index)
    names_to_files: dict[str, set[str]] = {}
    for module_id in referenced:
        module = graph_index.modules_by_id.get(module_id)
        if module is None:
            continue
        names_to_files.setdefault(module.name, set()).add(module.file_id)
    return {name for name, files in names_to_files.items() if len(files) > 1}


def _collect_referenced_modules(
    document: AsdlDocument,
    file_id: str,
    graph_index: DepGraphIndex,
) -> set[str]:
    referenced: set[str] = set()
    for module_name, module in (document.modules or {}).items():
        module_id = _resolve_module_id(module_name, file_id, graph_index)
        if module_id is None:
            continue
        for inst_name in (module.instances or {}).keys():
            instance_id = instance_identifier(module_id, inst_name)
            target_id = graph_index.edges_by_instance.get(instance_id)
            if target_id is not None:
                referenced.add(target_id)
        for parent_id in graph_index.parents_by_module.get(module_id, []):
            referenced.add(parent_id)
    return referenced


def _resolve_module_id(
    module_name: str,
    file_id: Optional[str],
    graph_index: Optional[DepGraphIndex],
) -> Optional[str]:
    if file_id is None:
        return None
    if graph_index is not None:
        module = graph_index.modules_by_file.get((file_id, module_name))
        if module is not None:
            return module.module_id
    return module_identifier(module_name, file_id)


def _relative_file_path(file_id: str, base_dir: Optional[Path]) -> str:
    path = Path(file_id)
    if base_dir is None:
        return path.name
    try:
        return path.relative_to(base_dir).as_posix()
    except ValueError:
        return Path(os.path.relpath(path, base_dir)).as_posix()


def _format_module_display(module: DepGraphModule, context: RenderContext) -> str:
    if module.name not in context.collision_names:
        return module.name
    relpath = _relative_file_path(module.file_id, context.base_dir)
    return f"{module.name} ({relpath})"


def _make_module_link(module: DepGraphModule, context: RenderContext) -> nodes.Node:
    label = _format_module_display(module, context)
    if not SPHINX_AVAILABLE or addnodes is None or context.sphinx_env is None:
        return nodes.Text(label)

    xref = addnodes.pending_xref(
        "",
        refdomain=ASDL_DOMAIN_NAME,
        reftype="module",
        reftarget=module.module_id,
        refexplicit=True,
    )
    if context.docname:
        xref["refdoc"] = context.docname
    xref += nodes.Text(label)
    return xref


def _document_title(document: AsdlDocument, file_path: Optional[Path]) -> str:
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


def _render_top_module_section(
    document: AsdlDocument,
    context: RenderContext,
) -> Optional[nodes.section]:
    if not document.top:
        return None

    section = _section("Top module")
    module_name = document.top
    para = nodes.paragraph()
    link_node = _maybe_link_module(module_name, context)
    para += link_node
    section += para
    return section


def _maybe_link_module(module_name: str, context: RenderContext) -> nodes.Node:
    if context.graph_index is None or context.file_id is None:
        return nodes.literal(text=module_name)
    module = context.graph_index.modules_by_file.get((context.file_id, module_name))
    if module is None:
        return nodes.literal(text=module_name)
    return _make_module_link(module, context)


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
    context: RenderContext,
) -> nodes.section:
    section = _section(f"Module `{name}`")
    module_id = _resolve_module_id(name, context.file_id, context.graph_index) or name
    _append_targets(section, "module", [module_id])

    module_doc = _docstring_text(docstrings, ("modules", name))
    if module_doc and not skip_notes:
        notes = _section("Notes")
        _append_paragraphs(notes, module_doc)
        section += notes

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

    interface_rows = _build_interface_rows(name, module, docstrings)
    if interface_rows:
        interface_section = _section("Interface")
        port_names = _module_port_names(module)
        _append_targets(
            interface_section,
            "port",
            [_qualify_module_name(name, port_name) for port_name in port_names],
        )
        table = _render_table(["Name", "Description"], interface_rows)
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

    instance_rows = _build_instance_rows(
        name,
        module,
        docstrings,
        module_id=module_id,
        context=context,
    )
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

    used_by_section = _render_used_by(module_id, context)
    if used_by_section is not None:
        section += used_by_section

    net_section = _render_nets(name, module, docstrings)
    if net_section is not None:
        section += net_section

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
        rows.append((net_name, doc or ""))
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
    module_name: str,
    module: ModuleDecl,
    docstrings: DocstringIndex,
    *,
    module_id: str,
    context: RenderContext,
) -> list[Sequence[object]]:
    rows: list[Sequence[object]] = []
    instances = module.instances or {}
    for inst_name, expr in instances.items():
        ref, params = _parse_instance_expr(expr)
        ref_cell: object = ref
        if context.graph_index is not None:
            instance_id = instance_identifier(module_id, inst_name)
            target_id = context.graph_index.edges_by_instance.get(instance_id)
            if target_id is not None:
                target_module = context.graph_index.modules_by_id.get(target_id)
                if target_module is not None:
                    ref_cell = _make_module_link(target_module, context)
        doc = _docstring_text(docstrings, ("modules", module_name, "instances", inst_name))
        rows.append((inst_name, ref_cell, params, doc or ""))
    return rows


def _render_used_by(module_id: str, context: RenderContext) -> Optional[nodes.section]:
    if context.graph_index is None:
        return None
    parent_ids = context.graph_index.parents_by_module.get(module_id, [])
    if not parent_ids:
        return None

    parent_modules: list[DepGraphModule] = []
    for parent_id in parent_ids:
        module = context.graph_index.modules_by_id.get(parent_id)
        if module is not None:
            parent_modules.append(module)
    if not parent_modules:
        return None

    parent_modules.sort(key=lambda module: (module.name, module.file_id))

    section = _section("Used by")
    listing = nodes.bullet_list()
    for module in parent_modules:
        item = nodes.list_item()
        para = nodes.paragraph()
        para += _make_module_link(module, context)
        item += para
        listing += item
    section += listing
    return section


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


def _render_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[object]],
) -> Optional[nodes.table]:
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
            if isinstance(cell, nodes.paragraph):
                entry += cell
            elif isinstance(cell, nodes.Node):
                para = nodes.paragraph()
                para += cell
                entry += para
            else:
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
