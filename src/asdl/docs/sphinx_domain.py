"""Sphinx domain helpers for ASDL documentation cross-references."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
from typing import Iterable, MutableMapping, Optional, Sequence, Tuple

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
import yaml as pyyaml

from asdl.ast.models import AsdlDocument, ModuleDecl
from asdl.ast.parser import parse_file
from asdl.diagnostics import Diagnostic, Severity
from asdl.diagnostics.renderers import render_text

from .depgraph import build_dependency_graph, module_identifier
from .docstrings import extract_docstrings_from_file

ASDL_DOMAIN_NAME = "asdl"
ASDL_OBJECT_TYPES = (
    "doc",
    "module",
    "port",
    "net",
    "inst",
    "var",
    "pattern",
    "import",
)

ASDL_PROJECT_MANIFEST = "project.yaml"
ASDL_PROJECT_GENERATED_DIR = "_generated"
ASDL_PROJECT_TOC_FILENAME = "project.rst"
ASDL_DEPGRAPH_ENV_KEY = "asdl_dependency_graph"


@dataclass(frozen=True)
class AsdlObjectEntry:
    """Registered ASDL object entry for Sphinx inventories.

    Args:
        objtype: Object type registered in the ASDL domain.
        name: Qualified reference name for the object.
        docname: Sphinx docname where the object is defined.
        target_id: Stable target id used for anchor lookup.
        display_name: Display name for inventory listings.
    """

    objtype: str
    name: str
    docname: str
    target_id: str
    display_name: str


@dataclass(frozen=True)
class AsdlProjectEntry:
    """Manifest-backed ASDL documentation entry for generated pages.

    Args:
        source: Manifest entry string (POSIX-style path relative to Sphinx srcdir).
        source_path: Absolute path to the ASDL file on disk.
        stub_relpath: Relative path to the generated stub page under ``_generated``.
        docname: Sphinx docname for the stub page.
        title: Title rendered in the stub page.
    """

    source: str
    source_path: Path
    stub_relpath: Path
    docname: str
    title: str


class AsdlDomainError(ValueError):
    """Raised when ASDL domain helpers receive invalid input."""


def make_asdl_target_id(objtype: str, name: str) -> str:
    """Build a stable target id for an ASDL object.

    Args:
        objtype: ASDL object type.
        name: Qualified reference name for the object.

    Returns:
        A stable anchor id string suitable for Sphinx targets.
    """
    _validate_objtype(objtype)
    slug = _slugify(f"{objtype}-{name}")
    digest = hashlib.sha1(f"{objtype}:{name}".encode("utf-8")).hexdigest()[:8]
    return f"{ASDL_DOMAIN_NAME}-{slug}-{digest}"


def register_asdl_object(
    objects: MutableMapping[Tuple[str, str], AsdlObjectEntry],
    objtype: str,
    name: str,
    docname: str,
    display_name: Optional[str] = None,
) -> AsdlObjectEntry:
    """Register an ASDL object in a domain data mapping.

    Args:
        objects: Mapping of ``(objtype, name)`` keys to entries.
        objtype: ASDL object type.
        name: Qualified reference name for the object.
        docname: Sphinx docname where the object appears.
        display_name: Optional display name override for inventories.

    Returns:
        The registered :class:`AsdlObjectEntry`.
    """
    _validate_objtype(objtype)
    entry = AsdlObjectEntry(
        objtype=objtype,
        name=name,
        docname=docname,
        target_id=make_asdl_target_id(objtype, name),
        display_name=display_name or name,
    )
    objects[(objtype, name)] = entry
    return entry


def _validate_objtype(objtype: str) -> None:
    if objtype not in ASDL_OBJECT_TYPES:
        raise AsdlDomainError(f"Unknown ASDL object type: {objtype}")


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^0-9A-Za-z]+", "-", value).strip("-").lower()
    return normalized or "asdl"


def collect_asdl_library_files(
    root: Path,
    *,
    include_archive: bool = False,
    prefer_doc: bool = True,
) -> list[Path]:
    """Collect ASDL files under a directory in deterministic order.

    Args:
        root: Directory (or file) to scan for ``.asdl`` sources.
        include_archive: Whether to include ``_archive`` directories.
        prefer_doc: Prefer ``*_doc.asdl`` files over sibling ``*.asdl`` files.

    Returns:
        Sorted list of ``.asdl`` files, ordered by relative path from ``root``.
    """
    if root.is_file():
        return [root] if root.suffix == ".asdl" else []
    if not root.exists():
        return []

    candidates = []
    for path in root.rglob("*.asdl"):
        if not path.is_file():
            continue
        if not include_archive and "_archive" in path.parts:
            continue
        candidates.append(path)

    if prefer_doc:
        doc_overrides: set[Path] = set()
        for path in candidates:
            if not path.stem.endswith("_doc"):
                continue
            base_stem = path.stem[: -len("_doc")]
            base_path = path.with_name(f"{base_stem}{path.suffix}")
            doc_overrides.add(base_path)
        candidates = [path for path in candidates if path not in doc_overrides]
    return sorted(candidates, key=lambda path: path.relative_to(root).as_posix())


def collect_asdl_project_entries(
    manifest_path: Path,
    *,
    srcdir: Optional[Path] = None,
    generated_dirname: str = ASDL_PROJECT_GENERATED_DIR,
    lib_roots: Optional[Iterable[Path]] = None,
) -> list[AsdlProjectEntry]:
    """Load ASDL project manifest entries in deterministic order.

    Args:
        manifest_path: Path to the project manifest YAML file.
        srcdir: Sphinx source directory used to resolve entry paths. Defaults to
            the manifest parent directory.
        generated_dirname: Directory name under ``srcdir`` where stub pages live.
        lib_roots: Optional library roots for import resolution when expanding
            manifest entries.

    Returns:
        Ordered list of project entries with computed stub metadata.
    """
    srcdir = srcdir or manifest_path.parent
    entries = _load_asdl_project_manifest(manifest_path)
    entries = _expand_project_manifest_entries(
        entries,
        srcdir=srcdir,
        lib_roots=lib_roots,
    )
    return [
        _build_project_entry(entry, srcdir, generated_dirname)
        for entry in entries
    ]


def write_asdl_project_pages(
    entries: Sequence[AsdlProjectEntry],
    *,
    output_dir: Path,
    toc_filename: str = ASDL_PROJECT_TOC_FILENAME,
) -> Path:
    """Write stub pages and a toctree for the ASDL project entries.

    Args:
        entries: Ordered project entries to render.
        output_dir: Output directory for generated stubs.
        toc_filename: Filename for the generated toctree page.

    Returns:
        Path to the generated toctree page.
    """
    _prepare_generated_dir(output_dir)

    for entry in entries:
        stub_path = output_dir / entry.stub_relpath
        stub_path.parent.mkdir(parents=True, exist_ok=True)
        stub_path.write_text(
            _render_project_stub(entry),
            encoding="utf-8",
        )

    toc_path = output_dir / toc_filename
    toc_path.write_text(
        _render_project_toc(entries),
        encoding="utf-8",
    )
    return toc_path


def _load_asdl_project_manifest(manifest_path: Path) -> list[str]:
    """Parse the project manifest and normalize its entries.

    Args:
        manifest_path: Path to the manifest YAML file.

    Returns:
        Sorted list of manifest entry strings.
    """
    if not manifest_path.exists():
        return []

    yaml = YAML(typ="safe")
    try:
        data = yaml.load(manifest_path.read_text(encoding="utf-8"))
    except (OSError, YAMLError) as exc:
        raise AsdlDomainError(
            f"Failed to read ASDL project manifest: {manifest_path}"
        ) from exc

    if not data:
        return []
    if not isinstance(data, dict):
        raise AsdlDomainError(
            "ASDL project manifest must be a mapping with an 'entries' list"
        )

    entries = data.get("entries", [])
    if entries is None:
        return []
    if not isinstance(entries, list):
        raise AsdlDomainError("ASDL project manifest 'entries' must be a list")

    normalized: list[str] = []
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, str):
            raise AsdlDomainError("ASDL project manifest entries must be strings")
        cleaned = Path(entry.strip()).as_posix()
        if not cleaned:
            continue
        if cleaned in seen:
            continue
        seen.add(cleaned)
        normalized.append(cleaned)

    return sorted(normalized)


def _expand_project_manifest_entries(
    entries: Sequence[str],
    *,
    srcdir: Path,
    lib_roots: Optional[Iterable[Path]] = None,
) -> list[str]:
    """Expand manifest entries using the resolved import graph.

    Args:
        entries: Normalized manifest entry strings.
        srcdir: Sphinx source directory used for relative path conversion.
        lib_roots: Optional library roots for import resolution.

    Returns:
        Ordered list of entry strings including imported files.
    """
    if not entries:
        return []

    entry_paths = [
        _resolve_project_entry_path(srcdir, entry)
        for entry in entries
    ]
    graph, _diagnostics = build_dependency_graph(
        entry_paths,
        lib_roots=lib_roots,
    )
    if graph is None:
        return list(entries)

    expanded: list[str] = []
    seen: set[str] = set()
    for file_entry in graph.files:
        entry = _path_to_manifest_entry(srcdir, Path(file_entry.file_id))
        if entry in seen:
            continue
        seen.add(entry)
        expanded.append(entry)
    return expanded


def _build_project_entry(
    entry: str,
    srcdir: Path,
    generated_dirname: str,
) -> AsdlProjectEntry:
    """Build a project entry with derived metadata."""
    source_path = _resolve_project_entry_path(srcdir, entry)
    stub_relpath = _entry_to_stub_relpath(entry)
    stub_docname = (
        Path(generated_dirname) / stub_relpath.with_suffix("")
    ).as_posix()
    title = source_path.name or stub_relpath.name
    return AsdlProjectEntry(
        source=entry,
        source_path=source_path,
        stub_relpath=stub_relpath,
        docname=stub_docname,
        title=title,
    )


def _resolve_project_entry_path(srcdir: Path, entry: str) -> Path:
    """Resolve a manifest entry path relative to the Sphinx source directory."""
    candidate = Path(entry)
    if not candidate.is_absolute():
        candidate = srcdir / candidate
    return candidate.resolve(strict=False)


def _path_to_manifest_entry(srcdir: Path, entry_path: Path) -> str:
    """Convert an absolute entry path to a manifest-relative path string."""
    try:
        relative = entry_path.relative_to(srcdir)
    except ValueError:
        relative = Path(os.path.relpath(entry_path, srcdir))
    return relative.as_posix()


def _entry_to_stub_relpath(entry: str) -> Path:
    """Map a manifest entry path to a generated stub relative path."""
    parts = [
        part
        for part in Path(entry).as_posix().split("/")
        if part not in ("", ".", "..")
    ]
    if not parts:
        raise AsdlDomainError(f"Invalid ASDL project entry: {entry}")
    filename = parts[-1]
    if filename.endswith(".asdl"):
        filename = filename[: -len(".asdl")]
    parts[-1] = f"{filename}.rst"
    return Path(*parts)


def _prepare_generated_dir(output_dir: Path) -> None:
    """Ensure the generated directory exists and remove old stub pages."""
    if output_dir.exists():
        for path in output_dir.rglob("*.rst"):
            path.unlink()
        for path in sorted(output_dir.rglob("*"), reverse=True):
            if path.is_dir():
                try:
                    next(path.iterdir())
                except StopIteration:
                    path.rmdir()
    output_dir.mkdir(parents=True, exist_ok=True)


def _render_project_stub(entry: AsdlProjectEntry) -> str:
    """Render a single stub page for a project entry."""
    lines = [
        "..",
        "   Generated file. Do not edit directly.",
        "",
        f".. asdl:document:: {entry.source}",
        "",
    ]
    return "\n".join(lines)


def _render_project_toc(entries: Sequence[AsdlProjectEntry]) -> str:
    """Render the toctree page for generated project entries."""
    title = "ASDL Project Files"
    underline = "=" * len(title)
    lines = [
        "..",
        "   Generated file. Do not edit directly.",
        "",
        title,
        underline,
        "",
        ".. toctree::",
        "   :maxdepth: 2",
        "",
    ]
    for entry in entries:
        lines.append(f"   {entry.stub_relpath.with_suffix('').as_posix()}")
    lines.append("")
    return "\n".join(lines)


try:  # pragma: no cover - exercised indirectly when Sphinx is available.
    from docutils import nodes
    from sphinx.domains import Domain, ObjType
    from sphinx.roles import XRefRole
    from sphinx.util import logging
    from sphinx.util.docutils import SphinxDirective
    from sphinx.util.nodes import make_refnode

    SPHINX_AVAILABLE = True
except ImportError:  # pragma: no cover - Sphinx optional.
    Domain = object  # type: ignore[assignment]
    ObjType = object  # type: ignore[assignment]
    XRefRole = object  # type: ignore[assignment]
    SphinxDirective = object  # type: ignore[assignment]
    make_refnode = None  # type: ignore[assignment]
    nodes = None  # type: ignore[assignment]
    SPHINX_AVAILABLE = False


if SPHINX_AVAILABLE:

    _LOGGER = logging.getLogger(__name__)

    def _resolve_asdl_path(srcdir: str, argument: str) -> Path:
        """Resolve an ASDL path relative to the Sphinx source directory.

        Args:
            srcdir: Sphinx source directory path.
            argument: Directive argument containing the file path.

        Returns:
            Resolved absolute path for the ASDL document.
        """
        candidate = Path(argument)
        if not candidate.is_absolute():
            candidate = Path(srcdir) / candidate
        return candidate.resolve(strict=False)

    def _document_title(document: AsdlDocument, file_path: Optional[Path]) -> str:
        """Determine the display title for an ASDL document.

        Args:
            document: Parsed ASDL document.
            file_path: Optional source file path.

        Returns:
            Title string for the rendered document.
        """
        if file_path is not None:
            return file_path.stem
        return "ASDL Document"

    def _file_namespace(doc_title: str, file_path: Optional[Path]) -> str:
        """Return the namespace used for file-scoped references.

        Args:
            doc_title: Document title used as a fallback.
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

    def _module_port_names(module: ModuleDecl) -> list[str]:
        """Return ordered port names derived from `$`-prefixed nets.

        Args:
            module: Module declaration to inspect.

        Returns:
            Ordered list of `$`-prefixed net names.
        """
        nets = module.nets or {}
        return [name for name in nets.keys() if name.startswith("$")]

    def _report_diagnostics(diagnostics: Iterable[Diagnostic]) -> None:
        """Emit ASDL diagnostics through the Sphinx logger.

        Args:
            diagnostics: Diagnostics to log as Sphinx warnings/errors.
        """
        for diagnostic in diagnostics:
            message = render_text([diagnostic])
            location = None
            if diagnostic.primary_span is not None:
                location = (diagnostic.primary_span.file, diagnostic.primary_span.start.line)
            if diagnostic.severity in (Severity.ERROR, Severity.FATAL):
                _LOGGER.error(message, location=location)
            elif diagnostic.severity is Severity.WARNING:
                _LOGGER.warning(message, location=location)
            else:
                _LOGGER.info(message, location=location)

    def _merge_rc_env(env: dict[str, str]) -> None:
        """Merge rc env entries into os.environ without overriding existing keys."""
        for key, value in env.items():
            os.environ.setdefault(key, value)

    def _resolve_project_config_path(
        srcdir: Path, config_value: Optional[str | Path]
    ) -> Optional[Path]:
        """Resolve the rc config override path relative to the Sphinx source dir."""
        if config_value is None:
            return None
        if isinstance(config_value, str) and config_value.strip() == "":
            return None
        candidate = Path(config_value)
        if not candidate.is_absolute():
            candidate = srcdir / candidate
        return candidate.resolve(strict=False)

    def _resolve_project_lib_roots(
        manifest_path: Path,
        config_path: Optional[Path],
    ) -> list[Path]:
        """Load .asdlrc settings for project builds and return lib roots."""
        try:
            from asdl.cli.config import load_asdlrc
        except Exception as exc:  # pragma: no cover - defensive: missing optional deps
            _LOGGER.error("Failed to load .asdlrc support: %s", exc)
            return []

        try:
            rc_config = load_asdlrc(manifest_path, config_path=config_path)
        except (FileNotFoundError, TypeError, ValueError, pyyaml.YAMLError) as exc:
            _LOGGER.error("Failed to load .asdlrc: %s", exc)
            return []

        if rc_config is None:
            return []

        _merge_rc_env(rc_config.env)
        return list(rc_config.lib_roots)

    def _render_asdl_document(
        domain: "AsdlDomain",
        state_document: nodes.document,
        file_path: Path,
    ) -> Optional[nodes.section]:
        """Parse and render a single ASDL document for Sphinx.

        Args:
            domain: ASDL domain used to register cross-reference targets.
            state_document: Docutils document to receive target registrations.
            file_path: Path to the ASDL file to parse.

        Returns:
            Rendered docutils section, or ``None`` when parsing fails.
        """
        document, diagnostics = parse_file(str(file_path))
        if diagnostics:
            _report_diagnostics(diagnostics)
        if document is None:
            return None

        docstrings = extract_docstrings_from_file(file_path)
        doc_title = _document_title(document, file_path)

        _register_document_objects(
            domain,
            document,
            file_path=file_path,
            doc_title=doc_title,
        )

        from .sphinx_render import render_docutils

        rendered = render_docutils(
            document,
            docstrings,
            file_path=file_path,
            title=doc_title,
            sphinx_env=domain.env,
        )
        for section in rendered.findall(nodes.section):
            if not section.get("ids"):
                state_document.note_implicit_target(section)
        for target in rendered.findall(nodes.target):
            state_document.note_explicit_target(target)
        return rendered

    def _store_dependency_graph(
        app: "Sphinx",
        entries: Sequence[AsdlProjectEntry],
        *,
        lib_roots: Optional[Sequence[Path]] = None,
    ) -> None:
        """Build and store the ASDL dependency graph on the Sphinx environment."""
        if not hasattr(app, "env"):
            return

        graph = None
        if entries:
            graph, diagnostics = build_dependency_graph(
                [entry.source_path for entry in entries],
                lib_roots=lib_roots,
            )
            if diagnostics:
                _report_diagnostics(diagnostics)
        setattr(app.env, ASDL_DEPGRAPH_ENV_KEY, graph)

    def _generate_project_pages(app: "Sphinx") -> None:
        """Generate per-file ASDL stub pages from the project manifest."""
        srcdir = Path(app.srcdir)
        manifest_rel = app.config.asdl_project_manifest
        config_value = app.config.asdl_project_config
        generated_dirname = app.config.asdl_project_generated_dir
        toc_filename = app.config.asdl_project_toc_filename
        manifest_path = srcdir / manifest_rel

        if not manifest_path.exists():
            _LOGGER.info("ASDL project manifest not found: %s", manifest_path)
            _store_dependency_graph(app, [])
            return

        config_path = _resolve_project_config_path(srcdir, config_value)
        lib_roots = _resolve_project_lib_roots(manifest_path, config_path)

        try:
            entries = collect_asdl_project_entries(
                manifest_path,
                srcdir=srcdir,
                generated_dirname=generated_dirname,
                lib_roots=lib_roots,
            )
        except AsdlDomainError as exc:
            _LOGGER.error(str(exc))
            _store_dependency_graph(app, [], lib_roots=lib_roots)
            return

        if not entries:
            _LOGGER.warning("ASDL project manifest is empty: %s", manifest_path)
            _store_dependency_graph(app, [], lib_roots=lib_roots)
            return

        output_dir = srcdir / generated_dirname
        write_asdl_project_pages(
            entries,
            output_dir=output_dir,
            toc_filename=toc_filename,
        )
        _store_dependency_graph(app, entries, lib_roots=lib_roots)

    def _register_document_objects(
        domain: "AsdlDomain",
        document: AsdlDocument,
        *,
        file_path: Optional[Path],
        doc_title: str,
    ) -> None:
        """Register ASDL objects in the Sphinx domain for cross-references.

        Args:
            domain: ASDL Sphinx domain to populate.
            document: Parsed ASDL document.
            file_path: Optional source file path for namespace resolution.
            doc_title: Document title for display names.
        """
        file_namespace = _file_namespace(doc_title, file_path)
        doc_ref_name = _document_ref_name(doc_title, file_path)
        domain.note_object("doc", doc_ref_name, display_name=doc_title)

        file_id = None
        if file_path is not None:
            file_id = str(file_path.resolve(strict=False))

        for alias in (document.imports or {}).keys():
            domain.note_object(
                "import",
                _qualify_file_name(file_namespace, alias),
                display_name=alias,
            )

        for module_name, module in (document.modules or {}).items():
            module_key = module_name
            if file_id is not None:
                module_key = module_identifier(module_name, file_id)
            domain.note_object("module", module_key, display_name=module_name)
            nets = module.nets or {}
            for port_name in _module_port_names(module):
                domain.note_object(
                    "port",
                    _qualify_module_name(module_name, port_name),
                    display_name=port_name,
                )
            for net_name in nets.keys():
                domain.note_object(
                    "net",
                    _qualify_module_name(module_name, net_name),
                    display_name=net_name,
                )
            for var_name in (module.variables or {}).keys():
                domain.note_object(
                    "var",
                    _qualify_module_name(module_name, var_name),
                    display_name=var_name,
                )
            for inst_name in (module.instances or {}).keys():
                domain.note_object(
                    "inst",
                    _qualify_module_name(module_name, inst_name),
                    display_name=inst_name,
                )
            for pattern_name in (module.patterns or {}).keys():
                domain.note_object(
                    "pattern",
                    _qualify_module_name(module_name, pattern_name),
                    display_name=pattern_name,
                )


    class AsdlObjectDirective(SphinxDirective):
        """Register a named ASDL object without parsing ASDL sources."""

        has_content = False
        required_arguments = 1
        optional_arguments = 0
        final_argument_whitespace = True
        objtype = ""

        def run(self) -> list[nodes.Node]:  # type: ignore[name-defined]
            name = self.arguments[0].strip()
            if not name:
                raise AsdlDomainError("ASDL directive requires a non-empty name")

            domain = self.env.get_domain(ASDL_DOMAIN_NAME)
            if not isinstance(domain, AsdlDomain):
                raise AsdlDomainError("ASDL domain is not available")

            entry = domain.note_object(self.objtype, name)
            target_node = nodes.target("", "", ids=[entry.target_id])
            self.state.document.note_explicit_target(target_node)
            return [target_node]


    class AsdlDocumentDirective(SphinxDirective):
        """Render an ASDL document and register cross-reference targets."""

        has_content = False
        required_arguments = 1
        optional_arguments = 0
        final_argument_whitespace = True

        def run(self) -> list[nodes.Node]:  # type: ignore[name-defined]
            argument = self.arguments[0].strip()
            if not argument:
                raise AsdlDomainError("ASDL document directive requires a file path")

            file_path = _resolve_asdl_path(self.env.srcdir, argument)

            domain = self.env.get_domain(ASDL_DOMAIN_NAME)
            if not isinstance(domain, AsdlDomain):
                raise AsdlDomainError("ASDL domain is not available")

            rendered = _render_asdl_document(domain, self.state.document, file_path)
            return [rendered] if rendered is not None else []

    class AsdlLibraryDirective(SphinxDirective):
        """Render all ASDL documents under a directory."""

        has_content = False
        required_arguments = 1
        optional_arguments = 0
        final_argument_whitespace = True

        def run(self) -> list[nodes.Node]:  # type: ignore[name-defined]
            argument = self.arguments[0].strip()
            if not argument:
                raise AsdlDomainError("ASDL library directive requires a directory path")

            library_path = _resolve_asdl_path(self.env.srcdir, argument)
            if not library_path.exists():
                _LOGGER.error("ASDL library path not found: %s", library_path)
                return []

            domain = self.env.get_domain(ASDL_DOMAIN_NAME)
            if not isinstance(domain, AsdlDomain):
                raise AsdlDomainError("ASDL domain is not available")

            asdl_files = collect_asdl_library_files(library_path)
            if not asdl_files:
                _LOGGER.warning("No ASDL files found under: %s", library_path)
                return []

            rendered_nodes: list[nodes.Node] = []
            for file_path in asdl_files:
                rendered = _render_asdl_document(domain, self.state.document, file_path)
                if rendered is not None:
                    rendered_nodes.append(rendered)
            return rendered_nodes

    def _build_directives() -> dict[str, type[SphinxDirective]]:
        directives: dict[str, type[SphinxDirective]] = {}
        for objtype in ASDL_OBJECT_TYPES:
            directives[objtype] = type(
                f"Asdl{objtype.title()}Directive",
                (AsdlObjectDirective,),
                {"objtype": objtype},
            )
        directives["document"] = AsdlDocumentDirective
        directives["library"] = AsdlLibraryDirective
        return directives


    class AsdlDomain(Domain):
        """Sphinx domain for ASDL reference targets."""

        name = ASDL_DOMAIN_NAME
        label = "ASDL"
        object_types = {obj: ObjType(obj, obj) for obj in ASDL_OBJECT_TYPES}
        roles = {obj: XRefRole() for obj in ASDL_OBJECT_TYPES}
        directives = _build_directives()
        initial_data = {"objects": {}}

        def note_object(
            self,
            objtype: str,
            name: str,
            docname: Optional[str] = None,
            display_name: Optional[str] = None,
        ) -> AsdlObjectEntry:
            """Record an ASDL object for later cross-reference resolution."""
            entry = register_asdl_object(
                self.data.setdefault("objects", {}),
                objtype,
                name,
                docname or self.env.docname,
                display_name=display_name,
            )
            return entry

        def clear_doc(self, docname: str) -> None:
            to_remove = [
                key
                for key, entry in self.data.get("objects", {}).items()
                if entry.docname == docname
            ]
            for key in to_remove:
                del self.data["objects"][key]

        def merge_domaindata(self, docnames: Iterable[str], otherdata: dict) -> None:
            for key, entry in otherdata.get("objects", {}).items():
                if entry.docname in docnames:
                    self.data.setdefault("objects", {})[key] = entry

        def resolve_xref(
            self,
            env: "Environment",
            fromdocname: str,
            builder: "Builder",
            typ: str,
            target: str,
            node: nodes.Node,
            contnode: nodes.Node,
        ) -> Optional[nodes.Node]:
            entry = self.data.get("objects", {}).get((typ, target))
            if entry is None:
                return None
            return make_refnode(
                builder,
                fromdocname,
                entry.docname,
                entry.target_id,
                contnode,
                entry.display_name,
            )

        def resolve_any_xref(
            self,
            env: "Environment",
            fromdocname: str,
            builder: "Builder",
            target: str,
            node: nodes.Node,
            contnode: nodes.Node,
        ) -> list[tuple[str, nodes.Node]]:
            results: list[tuple[str, nodes.Node]] = []
            for entry in self.data.get("objects", {}).values():
                if entry.name != target:
                    continue
                ref = make_refnode(
                    builder,
                    fromdocname,
                    entry.docname,
                    entry.target_id,
                    contnode,
                    entry.display_name,
                )
                results.append((entry.objtype, ref))
            return results

        def get_objects(self) -> Iterable[tuple[str, str, str, str, str, int]]:
            for entry in self.data.get("objects", {}).values():
                yield (
                    entry.name,
                    entry.display_name,
                    entry.objtype,
                    entry.docname,
                    entry.target_id,
                    1,
                )


else:

    class AsdlDomain:  # pragma: no cover - Sphinx optional.
        """Placeholder when Sphinx is unavailable."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            raise RuntimeError("Sphinx is required to use the ASDL domain.")


def setup(app: "Sphinx") -> dict[str, object]:
    """Register the ASDL Sphinx domain."""
    if not SPHINX_AVAILABLE:
        raise RuntimeError("Sphinx is required to register the ASDL domain.")

    app.add_domain(AsdlDomain)
    app.add_config_value("asdl_project_manifest", ASDL_PROJECT_MANIFEST, "env")
    app.add_config_value("asdl_project_config", None, "env")
    app.add_config_value(
        "asdl_project_generated_dir", ASDL_PROJECT_GENERATED_DIR, "env"
    )
    app.add_config_value(
        "asdl_project_toc_filename", ASDL_PROJECT_TOC_FILENAME, "env"
    )
    app.connect("builder-inited", _generate_project_pages)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


__all__ = [
    "ASDL_DOMAIN_NAME",
    "ASDL_OBJECT_TYPES",
    "AsdlDomain",
    "AsdlDomainError",
    "AsdlObjectEntry",
    "AsdlProjectEntry",
    "SPHINX_AVAILABLE",
    "ASDL_PROJECT_GENERATED_DIR",
    "ASDL_PROJECT_MANIFEST",
    "ASDL_PROJECT_TOC_FILENAME",
    "make_asdl_target_id",
    "register_asdl_object",
    "collect_asdl_project_entries",
    "write_asdl_project_pages",
    "setup",
]
