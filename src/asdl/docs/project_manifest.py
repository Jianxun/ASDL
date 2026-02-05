"""Project manifest parsing and page generation for ASDL Sphinx docs."""

from __future__ import annotations

from dataclasses import dataclass
import fnmatch
import hashlib
import os
from pathlib import Path
import re
from typing import Iterable, Optional, Sequence, Tuple

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
import yaml as pyyaml

from asdl.ast.parser import parse_file
from asdl.diagnostics import Diagnostic, Severity
from asdl.diagnostics.renderers import render_text

from .depgraph import module_identifier
from .docstrings import DocstringIndex, extract_docstrings_from_file
from .sphinx_domain import AsdlDomainError

ASDL_PROJECT_MANIFEST = "project.yaml"
ASDL_PROJECT_GENERATED_DIR = "_generated"
ASDL_PROJECT_TOC_FILENAME = "project.rst"
ASDL_PROJECT_MANIFEST_SCHEMA_VERSION = 1


try:  # pragma: no cover - optional when Sphinx is missing.
    from sphinx.util import logging

    SPHINX_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised when Sphinx is unavailable.
    logging = None  # type: ignore[assignment]
    SPHINX_AVAILABLE = False


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


@dataclass(frozen=True)
class AsdlProjectEntrance:
    """Manifest-defined top-level entry for the project navigation.

    Args:
        file: ASDL file path relative to the Sphinx source directory.
        module: Module name defined within the ASDL file.
        description: Optional description text for the entrance entry.
    """

    file: str
    module: str
    description: Optional[str]


@dataclass(frozen=True)
class AsdlProjectLibrary:
    """Manifest-defined ASDL library root for project documentation.

    Args:
        name: Display name for the library in navigation.
        path: Directory path relative to the Sphinx source directory.
        exclude: Glob patterns relative to the library root to exclude.
    """

    name: str
    path: str
    exclude: Tuple[str, ...]


@dataclass(frozen=True)
class AsdlProjectLibraryRow:
    """Row entry for a library modules table."""

    file_entry: str
    module: str
    module_id: str
    file_doc_ref: str
    description: str


@dataclass(frozen=True)
class AsdlProjectLibraryPage:
    """Generated page metadata for a project library."""

    name: str
    path: str
    stub_relpath: Path
    docname: str
    rows: Tuple[AsdlProjectLibraryRow, ...]


@dataclass(frozen=True)
class AsdlProjectManifest:
    """Parsed ASDL project manifest (schema v1).

    Args:
        schema_version: Manifest schema version (must be 1).
        project_name: Optional project name override for the README label.
        readme: Optional README doc path relative to the Sphinx source directory.
        docs: Ordered list of standalone doc paths relative to the Sphinx source.
        entrances: Ordered list of navigation entrances.
        libraries: Ordered list of library roots to document.
    """

    schema_version: int
    project_name: Optional[str]
    readme: Optional[str]
    docs: Tuple[str, ...]
    entrances: Tuple[AsdlProjectEntrance, ...]
    libraries: Tuple[AsdlProjectLibrary, ...]


def collect_asdl_project_library_files(
    root: Path,
    *,
    exclude: Sequence[str] = (),
) -> list[Path]:
    """Collect ASDL files for a project library root.

    Args:
        root: Directory (or file) to scan for ``.asdl`` sources.
        exclude: Glob patterns relative to ``root`` that should be excluded.

    Returns:
        List of ``.asdl`` files under ``root`` with excludes applied.
    """
    if root.is_file():
        candidates = [root] if root.suffix == ".asdl" else []
    elif not root.exists():
        return []
    else:
        candidates = [path for path in root.rglob("*.asdl") if path.is_file()]

    if not exclude:
        return candidates

    filtered: list[Path] = []
    for path in candidates:
        rel = _project_library_relative_path(root, path)
        if _matches_project_exclude(rel, exclude):
            continue
        filtered.append(path)
    return filtered


def collect_asdl_project_entries(
    manifest_path: Path,
    *,
    srcdir: Optional[Path] = None,
    generated_dirname: str = ASDL_PROJECT_GENERATED_DIR,
    manifest: Optional[AsdlProjectManifest] = None,
) -> list[AsdlProjectEntry]:
    """Load ASDL project manifest entries in manifest order.

    Args:
        manifest_path: Path to the project manifest YAML file.
        srcdir: Sphinx source directory used to resolve entry paths. Defaults to
            the manifest parent directory.
        generated_dirname: Directory name under ``srcdir`` where stub pages live.
        manifest: Optional pre-parsed manifest to reuse.

    Returns:
        Ordered list of project entries with computed stub metadata.
    """
    srcdir = srcdir or manifest_path.parent
    manifest = manifest or load_asdl_project_manifest(manifest_path)
    entries = _expand_project_manifest_libraries(
        manifest,
        srcdir=srcdir,
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
    manifest: Optional[AsdlProjectManifest] = None,
    srcdir: Optional[Path] = None,
    generated_dirname: str = ASDL_PROJECT_GENERATED_DIR,
) -> Path:
    """Write stub pages, library pages, and a toctree for ASDL project docs.

    Args:
        entries: Ordered project entries to render.
        output_dir: Output directory for generated stubs.
        toc_filename: Filename for the generated toctree page.
        manifest: Optional parsed manifest for nav rendering.
        srcdir: Source directory for resolving entrance entries when needed.
        generated_dirname: Generated directory name for entrance stubs.

    Returns:
        Path to the generated toctree page.
    """
    _prepare_generated_dir(output_dir)

    extra_entries: list[AsdlProjectEntry] = []
    library_pages: list[AsdlProjectLibraryPage] = []
    toc_text = _render_project_toc(entries)
    if manifest is not None:
        if srcdir is None:
            raise AsdlDomainError(
                "ASDL project nav rendering requires a srcdir path"
            )
        entrance_entries = _collect_project_entrance_entries(
            manifest,
            srcdir=srcdir,
            generated_dirname=generated_dirname,
        )
        extra_entries = entrance_entries
        library_pages = _collect_project_library_pages(
            manifest,
            srcdir=srcdir,
            generated_dirname=generated_dirname,
        )
        toc_text = _render_project_nav(
            manifest,
            library_pages,
            entrance_entries,
            generated_dirname=generated_dirname,
        )

    for entry in _merge_project_entries(entries, extra_entries):
        stub_path = output_dir / entry.stub_relpath
        stub_path.parent.mkdir(parents=True, exist_ok=True)
        stub_path.write_text(
            _render_project_stub(entry),
            encoding="utf-8",
        )

    for page in library_pages:
        page_path = output_dir / page.stub_relpath
        page_path.parent.mkdir(parents=True, exist_ok=True)
        page_path.write_text(
            _render_project_library_page(page),
            encoding="utf-8",
        )

    toc_path = output_dir / toc_filename
    toc_path.write_text(
        toc_text,
        encoding="utf-8",
    )
    return toc_path


def load_asdl_project_manifest(manifest_path: Path) -> AsdlProjectManifest:
    """Parse the ASDL project manifest (schema v1).

    Args:
        manifest_path: Path to the manifest YAML file.

    Returns:
        Parsed :class:`AsdlProjectManifest` data.

    Raises:
        AsdlDomainError: If the manifest is missing required fields or uses an
            unsupported schema version.
    """
    if not manifest_path.exists():
        return AsdlProjectManifest(
            schema_version=ASDL_PROJECT_MANIFEST_SCHEMA_VERSION,
            project_name=None,
            readme=None,
            docs=(),
            entrances=(),
            libraries=(),
        )

    yaml = YAML(typ="safe")
    try:
        data = yaml.load(manifest_path.read_text(encoding="utf-8"))
    except (OSError, YAMLError) as exc:
        raise AsdlDomainError(
            f"Failed to read ASDL project manifest: {manifest_path}"
        ) from exc

    if not data:
        raise AsdlDomainError("ASDL project manifest is empty")
    if not isinstance(data, dict):
        raise AsdlDomainError(
            "ASDL project manifest must be a mapping with schema keys"
        )

    schema_version = data.get("schema_version")
    if schema_version != ASDL_PROJECT_MANIFEST_SCHEMA_VERSION:
        raise AsdlDomainError(
            "Unsupported ASDL project manifest schema_version; expected 1."
        )

    project_name = _optional_manifest_string(
        data.get("project_name"), "project_name"
    )
    readme = _optional_manifest_path(data.get("readme"), "readme")
    docs = tuple(_load_manifest_path_list(data.get("docs"), "docs"))
    entrances = tuple(_load_manifest_entrances(data.get("entrances")))
    libraries = tuple(_load_manifest_libraries(data.get("libraries")))

    return AsdlProjectManifest(
        schema_version=schema_version,
        project_name=project_name,
        readme=readme,
        docs=docs,
        entrances=entrances,
        libraries=libraries,
    )


def _optional_manifest_string(value: object, field: str) -> Optional[str]:
    """Normalize optional string fields from the project manifest.

    Args:
        value: Raw manifest value.
        field: Field name used for diagnostics.

    Returns:
        Stripped string value, or ``None`` if the field is unset or empty.
    """
    if value is None:
        return None
    if not isinstance(value, str):
        raise AsdlDomainError(
            f"ASDL project manifest '{field}' must be a string"
        )
    cleaned = value.strip()
    return cleaned or None


def _required_manifest_string(value: object, field: str) -> str:
    """Normalize required string fields from the project manifest.

    Args:
        value: Raw manifest value.
        field: Field name used for diagnostics.

    Returns:
        Stripped string value.

    Raises:
        AsdlDomainError: If the value is not a non-empty string.
    """
    if not isinstance(value, str):
        raise AsdlDomainError(
            f"ASDL project manifest '{field}' must be a string"
        )
    cleaned = value.strip()
    if not cleaned:
        raise AsdlDomainError(
            f"ASDL project manifest '{field}' must be a non-empty string"
        )
    return cleaned


def _optional_manifest_path(value: object, field: str) -> Optional[str]:
    """Normalize optional path fields from the project manifest.

    Args:
        value: Raw manifest value.
        field: Field name used for diagnostics.

    Returns:
        POSIX-style path string, or ``None`` if unset.
    """
    cleaned = _optional_manifest_string(value, field)
    if cleaned is None:
        return None
    return Path(cleaned).as_posix()


def _required_manifest_path(value: object, field: str) -> str:
    """Normalize required path fields from the project manifest.

    Args:
        value: Raw manifest value.
        field: Field name used for diagnostics.

    Returns:
        POSIX-style path string.

    Raises:
        AsdlDomainError: If the path is missing or empty.
    """
    cleaned = _required_manifest_string(value, field)
    return Path(cleaned).as_posix()


def _load_manifest_list(value: object, field: str) -> list[object]:
    """Load a list field from the project manifest preserving order.

    Args:
        value: Raw manifest value.
        field: Field name used for diagnostics.

    Returns:
        List of entries in manifest order.
    """
    if value is None:
        return []
    if not isinstance(value, list):
        raise AsdlDomainError(
            f"ASDL project manifest '{field}' must be a list"
        )
    return list(value)


def _load_manifest_path_list(value: object, field: str) -> list[str]:
    """Load a list of path strings from the project manifest.

    Args:
        value: Raw manifest value.
        field: Field name used for diagnostics.

    Returns:
        List of normalized path strings in manifest order.
    """
    entries = _load_manifest_list(value, field)
    normalized: list[str] = []
    for entry in entries:
        normalized.append(_required_manifest_path(entry, field))
    return normalized


def _load_manifest_entrances(value: object) -> list[AsdlProjectEntrance]:
    """Load entrance entries from the project manifest.

    Args:
        value: Raw manifest value.

    Returns:
        List of parsed entrance entries in manifest order.
    """
    entries = _load_manifest_list(value, "entrances")
    normalized: list[AsdlProjectEntrance] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise AsdlDomainError(
                "ASDL project manifest 'entrances' must contain mappings"
            )
        file_value = _required_manifest_path(entry.get("file"), "entrances.file")
        module_value = _required_manifest_string(
            entry.get("module"), "entrances.module"
        )
        description_value = _optional_manifest_string(
            entry.get("description"), "entrances.description"
        )
        normalized.append(
            AsdlProjectEntrance(
                file=file_value,
                module=module_value,
                description=description_value,
            )
        )
    return normalized


def _load_manifest_libraries(value: object) -> list[AsdlProjectLibrary]:
    """Load library entries from the project manifest.

    Args:
        value: Raw manifest value.

    Returns:
        List of parsed library entries in manifest order.
    """
    entries = _load_manifest_list(value, "libraries")
    normalized: list[AsdlProjectLibrary] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise AsdlDomainError(
                "ASDL project manifest 'libraries' must contain mappings"
            )
        name_value = _required_manifest_string(entry.get("name"), "libraries.name")
        path_value = _required_manifest_path(entry.get("path"), "libraries.path")
        exclude_value = _load_manifest_path_list(entry.get("exclude"), "libraries.exclude")
        normalized.append(
            AsdlProjectLibrary(
                name=name_value,
                path=path_value,
                exclude=tuple(exclude_value),
            )
        )
    return normalized


def _project_library_relative_path(root: Path, path: Path) -> str:
    """Compute the POSIX relative path from a library root to a file.

    Args:
        root: Library root path.
        path: File path under the library root.

    Returns:
        POSIX relative path string from ``root`` to ``path``.
    """
    try:
        relative = path.relative_to(root)
    except ValueError:
        relative = Path(os.path.relpath(path, root))
    return relative.as_posix()


def _document_ref_name_for_path(file_path: Path) -> str:
    """Build the doc reference name for an ASDL file."""
    return f"{file_path.stem}_doc"


def _matches_project_exclude(relative: str, patterns: Sequence[str]) -> bool:
    """Return True if a relative path matches any exclude glob.

    Args:
        relative: POSIX relative path string.
        patterns: Glob patterns relative to the library root.

    Returns:
        ``True`` if the path matches any pattern.
    """
    for pattern in patterns:
        normalized = Path(pattern).as_posix()
        if fnmatch.fnmatchcase(relative, normalized):
            return True
    return False


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^0-9A-Za-z]+", "-", value).strip("-").lower()
    return normalized or "asdl"


def _library_page_stub_relpath(library: AsdlProjectLibrary) -> Path:
    """Compute the stub relative path for a library page."""
    slug = _slugify(library.name)
    digest = hashlib.sha1(
        f"{library.name}:{library.path}".encode("utf-8")
    ).hexdigest()[:8]
    return Path("libraries") / f"{slug}-{digest}.rst"


def _module_doc_summary(docstrings: DocstringIndex, module_name: str) -> str:
    """Return a one-line summary for a module docstring."""
    key_doc = docstrings.key_docstring(("modules", module_name))
    if key_doc is None or not key_doc.text:
        return ""
    for line in key_doc.text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _report_diagnostics(diagnostics: Iterable[Diagnostic]) -> None:
    """Emit ASDL diagnostics through the Sphinx logger when available."""
    if not SPHINX_AVAILABLE or logging is None:
        return
    logger = logging.getLogger(__name__)
    for diagnostic in diagnostics:
        message = render_text([diagnostic])
        location = None
        if diagnostic.primary_span is not None:
            location = (
                diagnostic.primary_span.file,
                diagnostic.primary_span.start.line,
            )
        if diagnostic.severity in (Severity.ERROR, Severity.FATAL):
            logger.error(message, location=location)
        elif diagnostic.severity is Severity.WARNING:
            logger.warning(message, location=location)
        else:
            logger.info(message, location=location)


def _build_project_library_page(
    library: AsdlProjectLibrary,
    *,
    srcdir: Path,
    generated_dirname: str,
) -> AsdlProjectLibraryPage:
    """Build the library page metadata and module rows."""
    library_root = _resolve_project_entry_path(srcdir, library.path)
    stub_relpath = _library_page_stub_relpath(library)
    docname = (
        Path(generated_dirname) / stub_relpath.with_suffix("")
    ).as_posix()

    rows: list[AsdlProjectLibraryRow] = []
    for path in collect_asdl_project_library_files(
        library_root,
        exclude=library.exclude,
    ):
        file_entry = _path_to_manifest_entry(srcdir, path)
        file_doc_ref = _document_ref_name_for_path(path)
        file_id = str(path.resolve(strict=False))
        document, diagnostics = parse_file(str(path))
        if diagnostics:
            _report_diagnostics(diagnostics)
        if document is None:
            continue
        docstrings = extract_docstrings_from_file(path)
        for module_name in (document.modules or {}).keys():
            module_id = module_identifier(module_name, file_id)
            description = _module_doc_summary(docstrings, module_name)
            rows.append(
                AsdlProjectLibraryRow(
                    file_entry=file_entry,
                    module=module_name,
                    module_id=module_id,
                    file_doc_ref=file_doc_ref,
                    description=description,
                )
            )

    rows.sort(key=lambda row: row.file_entry)
    return AsdlProjectLibraryPage(
        name=library.name,
        path=library.path,
        stub_relpath=stub_relpath,
        docname=docname,
        rows=tuple(rows),
    )


def _collect_project_library_pages(
    manifest: AsdlProjectManifest,
    *,
    srcdir: Path,
    generated_dirname: str,
) -> list[AsdlProjectLibraryPage]:
    """Build generated library pages for the project manifest."""
    pages: list[AsdlProjectLibraryPage] = []
    for library in manifest.libraries:
        pages.append(
            _build_project_library_page(
                library,
                srcdir=srcdir,
                generated_dirname=generated_dirname,
            )
        )
    return pages


def _expand_project_manifest_libraries(
    manifest: AsdlProjectManifest,
    *,
    srcdir: Path,
) -> list[str]:
    """Expand manifest libraries into ASDL file entries.

    Args:
        manifest: Parsed project manifest data.
        srcdir: Sphinx source directory used for relative path conversion.

    Returns:
        Ordered list of ASDL file entries derived from manifest libraries.
    """
    entries: list[str] = []
    for library in manifest.libraries:
        library_root = _resolve_project_entry_path(srcdir, library.path)
        for path in collect_asdl_project_library_files(
            library_root,
            exclude=library.exclude,
        ):
            entries.append(_path_to_manifest_entry(srcdir, path))
    return entries


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


def _normalize_project_docname(entry: str) -> str:
    """Normalize a doc path into a Sphinx docname string.

    Args:
        entry: Manifest doc path (relative path or docname).

    Returns:
        Normalized docname without ``.rst`` or ``.md`` suffixes.
    """
    path = Path(entry)
    if path.suffix in (".rst", ".md"):
        path = path.with_suffix("")
    return path.as_posix()


def _project_nav_docname(entry: str, generated_dirname: str) -> str:
    """Return a docname relative to the generated nav page location.

    Args:
        entry: Manifest doc path (relative path or docname).
        generated_dirname: Directory name that holds generated pages.

    Returns:
        Relative docname suitable for use in the project nav toctree.
    """
    normalized = _normalize_project_docname(entry)
    relative = Path(os.path.relpath(normalized, generated_dirname))
    return relative.as_posix()


def _collect_project_entrance_entries(
    manifest: AsdlProjectManifest,
    *,
    srcdir: Path,
    generated_dirname: str,
) -> list[AsdlProjectEntry]:
    """Build stub metadata for manifest entrances.

    Args:
        manifest: Parsed project manifest.
        srcdir: Sphinx source directory for resolving entrance paths.
        generated_dirname: Directory name for generated stub pages.

    Returns:
        Ordered list of entrance entries for stub generation.
    """
    return [
        _build_project_entry(entrance.file, srcdir, generated_dirname)
        for entrance in manifest.entrances
    ]


def _merge_project_entries(
    entries: Sequence[AsdlProjectEntry],
    extras: Sequence[AsdlProjectEntry],
) -> list[AsdlProjectEntry]:
    """Combine project entries while preserving first-seen order.

    Args:
        entries: Primary entry list.
        extras: Additional entries to append if missing.

    Returns:
        Combined list without duplicate ``source`` values.
    """
    merged: list[AsdlProjectEntry] = []
    seen: set[str] = set()
    for entry in list(entries) + list(extras):
        if entry.source in seen:
            continue
        seen.add(entry.source)
        merged.append(entry)
    return merged


def _has_project_nav_content(manifest: AsdlProjectManifest) -> bool:
    """Return True when the manifest contains any nav-visible content."""
    return bool(
        manifest.readme
        or manifest.docs
        or manifest.entrances
        or manifest.libraries
    )


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
        ":orphan:",
        "",
        f".. asdl:document:: {entry.source}",
        "",
    ]
    return "\n".join(lines)


def _render_project_nav(
    manifest: AsdlProjectManifest,
    library_pages: Sequence[AsdlProjectLibraryPage],
    entrance_entries: Sequence[AsdlProjectEntry],
    *,
    generated_dirname: str,
) -> str:
    """Render the project navigation page for manifest-backed docs."""
    title = "ASDL Project"
    underline = "=" * len(title)
    lines = [
        "..",
        "   Generated file. Do not edit directly.",
        "",
        title,
        underline,
        "",
    ]

    if manifest.readme or manifest.docs:
        lines.extend(
            [
                ".. toctree::",
                "   :maxdepth: 1",
                "",
            ]
        )
        if manifest.readme:
            readme_docname = _project_nav_docname(
                manifest.readme, generated_dirname
            )
            if manifest.project_name:
                lines.append(
                    f"   {manifest.project_name} <{readme_docname}>"
                )
            else:
                lines.append(f"   {readme_docname}")
        for doc in manifest.docs:
            lines.append(
                f"   {_project_nav_docname(doc, generated_dirname)}"
            )
        lines.append("")

    if manifest.entrances:
        entry_map = {entry.source: entry for entry in entrance_entries}
        lines.extend(
            [
                "Entrances",
                "-" * len("Entrances"),
                "",
            ]
        )
        for entrance in manifest.entrances:
            entry = entry_map.get(entrance.file)
            if entry is None:
                continue
            module_id = module_identifier(
                entrance.module, str(entry.source_path.resolve(strict=False))
            )
            module_ref = (
                f":asdl:module:`{entrance.module} <{module_id}>`"
            )
            file_ref = (
                f":doc:`{entrance.file} <{entry.stub_relpath.with_suffix('').as_posix()}>`"
            )
            base_line = f"- {module_ref} in {file_ref}"
            if entrance.description:
                desc_lines = entrance.description.splitlines()
                lines.append(f"{base_line} - {desc_lines[0]}")
                for continuation in desc_lines[1:]:
                    lines.append(f"  {continuation}")
            else:
                lines.append(base_line)
        lines.append("")

    if library_pages:
        lines.extend(
            [
                "Libraries",
                "-" * len("Libraries"),
                "",
                ".. toctree::",
                "   :maxdepth: 1",
                "",
            ]
        )
        for page in library_pages:
            page_docname = page.stub_relpath.with_suffix("").as_posix()
            lines.append(f"   {page.name} <{page_docname}>")
        lines.append("")

    return "\n".join(lines)


def _render_project_library_page(page: AsdlProjectLibraryPage) -> str:
    """Render the generated page for a library module table."""
    title = page.name
    underline = "=" * len(title)
    lines = [
        "..",
        "   Generated file. Do not edit directly.",
        "",
        title,
        underline,
        "",
    ]

    if not page.rows:
        lines.append("No modules found.")
        lines.append("")
        return "\n".join(lines)

    lines.extend(
        [
            ".. list-table::",
            "   :header-rows: 1",
            "   :widths: 45 25 30",
            "",
            "   * - ASDL file",
            "     - Module",
            "     - Summary",
        ]
    )
    for row in page.rows:
        file_link = f":asdl:doc:`{row.file_entry} <{row.file_doc_ref}>`"
        module_link = f":asdl:module:`{row.module} <{row.module_id}>`"
        lines.extend(
            [
                f"   * - {file_link}",
                f"     - {module_link}",
                f"     - {row.description}" if row.description else "     -",
            ]
        )
    lines.append("")
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


__all__ = [
    "ASDL_PROJECT_GENERATED_DIR",
    "ASDL_PROJECT_MANIFEST",
    "ASDL_PROJECT_MANIFEST_SCHEMA_VERSION",
    "ASDL_PROJECT_TOC_FILENAME",
    "AsdlProjectEntry",
    "AsdlProjectEntrance",
    "AsdlProjectLibrary",
    "AsdlProjectManifest",
    "collect_asdl_project_entries",
    "load_asdl_project_manifest",
    "write_asdl_project_pages",
]
