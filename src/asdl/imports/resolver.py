from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from asdl.ast import AsdlDocument, parse_file
from asdl.ast.location import Locatable
from asdl.diagnostics import Diagnostic, Severity

from .diagnostics import (
    import_cycle,
    import_path_ambiguous,
    import_path_malformed,
    import_path_missing,
)


@dataclass(frozen=True)
class ImportGraph:
    entry_file: Path
    documents: dict[Path, AsdlDocument]
    imports: dict[Path, dict[str, Path]]


def resolve_import_path(
    import_path: str,
    *,
    importing_file: Path,
    project_root: Optional[Path] = None,
    include_roots: Optional[Iterable[Path]] = None,
    lib_roots: Optional[Iterable[Path]] = None,
    loc: Optional[Locatable] = None,
) -> Tuple[Optional[Path], List[Diagnostic]]:
    diagnostics: List[Diagnostic] = []
    try:
        expanded = _expand_import_path(import_path)
    except Exception as exc:
        diagnostics.append(import_path_malformed(import_path, str(exc), loc))
        return None, diagnostics

    if expanded.strip() == "":
        diagnostics.append(import_path_malformed(import_path, "Import path is empty.", loc))
        return None, diagnostics

    try:
        expanded_path = Path(expanded)
    except (TypeError, ValueError) as exc:
        diagnostics.append(import_path_malformed(import_path, str(exc), loc))
        return None, diagnostics

    importer_dir = Path(importing_file).absolute().parent
    root = _normalize_root(project_root) if project_root is not None else importer_dir
    include_paths = _normalize_roots(include_roots)
    lib_paths = _normalize_roots(lib_roots)
    env_paths = _env_lib_roots()

    if _is_explicit_relative(expanded):
        return _resolve_candidate(importer_dir / expanded, import_path, loc)

    if expanded_path.is_absolute():
        return _resolve_candidate(expanded_path, import_path, loc)

    matches: List[Path] = []
    seen: set[Path] = set()
    for candidate in _iter_logical_candidates(
        expanded,
        root,
        include_paths,
        env_paths,
        lib_paths,
    ):
        if not candidate.is_file():
            continue
        normalized = _normalize_path(candidate)
        if normalized in seen:
            continue
        matches.append(normalized)
        seen.add(normalized)

    if len(matches) == 1:
        return matches[0], diagnostics
    if len(matches) > 1:
        diagnostics.append(import_path_ambiguous(import_path, matches, loc))
        return None, diagnostics

    diagnostics.append(import_path_missing(import_path, loc))
    return None, diagnostics


def resolve_import_graph(
    entry_file: Path,
    *,
    project_root: Optional[Path] = None,
    include_roots: Optional[Iterable[Path]] = None,
    lib_roots: Optional[Iterable[Path]] = None,
) -> Tuple[Optional[ImportGraph], List[Diagnostic]]:
    diagnostics: List[Diagnostic] = []
    documents: dict[Path, AsdlDocument] = {}
    imports_by_file: dict[Path, dict[str, Path]] = {}
    visit_stack: list[Path] = []
    visit_index: dict[Path, int] = {}
    visited: set[Path] = set()

    def visit(path: Path) -> bool:
        file_id = _normalize_path(path)
        if file_id in visited:
            return True
        if file_id in visit_index:
            start = visit_index[file_id]
            chain = [*visit_stack[start:], file_id]
            diagnostics.append(import_cycle(chain))
            return False

        visit_index[file_id] = len(visit_stack)
        visit_stack.append(file_id)

        document, parse_diags = parse_file(str(file_id))
        diagnostics.extend(parse_diags)
        if document is None:
            visit_stack.pop()
            visit_index.pop(file_id, None)
            return False

        documents[file_id] = document
        resolved_imports: dict[str, Path] = {}
        for namespace, import_path in (document.imports or {}).items():
            resolved, resolve_diags = resolve_import_path(
                import_path,
                importing_file=file_id,
                project_root=project_root,
                include_roots=include_roots,
                lib_roots=lib_roots,
                loc=None,
            )
            diagnostics.extend(resolve_diags)
            if resolved is not None:
                resolved_imports[namespace] = resolved

        imports_by_file[file_id] = resolved_imports
        ok = True
        for resolved in resolved_imports.values():
            if not visit(resolved):
                ok = False

        visit_stack.pop()
        visit_index.pop(file_id, None)
        visited.add(file_id)
        return ok

    ok = visit(Path(entry_file))
    if not ok:
        return None, diagnostics
    if any(diag.severity is Severity.ERROR for diag in diagnostics):
        return None, diagnostics
    return ImportGraph(
        entry_file=_normalize_path(Path(entry_file)),
        documents=documents,
        imports=imports_by_file,
    ), diagnostics


def _expand_import_path(import_path: str) -> str:
    return os.path.expanduser(os.path.expandvars(import_path))


def _is_explicit_relative(path: str) -> bool:
    if path.startswith("./") or path.startswith("../"):
        return True
    sep = os.sep
    if sep != "/":
        return path.startswith(f".{sep}") or path.startswith(f"..{sep}")
    return False


def _resolve_candidate(
    path: Path,
    display_path: str,
    loc: Optional[Locatable],
) -> Tuple[Optional[Path], List[Diagnostic]]:
    if path.is_file():
        return _normalize_path(path), []
    return None, [import_path_missing(display_path, loc)]


def _iter_logical_candidates(
    logical_path: str,
    project_root: Path,
    include_roots: Iterable[Path],
    env_roots: Iterable[Path],
    lib_roots: Iterable[Path],
) -> Iterable[Path]:
    for root in (project_root, *include_roots, *env_roots, *lib_roots):
        yield root / logical_path


def _env_lib_roots() -> List[Path]:
    raw = os.environ.get("ASDL_LIB_PATH", "")
    if not raw:
        return []
    roots: List[Path] = []
    for entry in raw.split(os.pathsep):
        entry = entry.strip()
        if not entry:
            continue
        root = _normalize_root(entry)
        roots.append(root)
    return roots


def _normalize_roots(roots: Optional[Iterable[Path]]) -> List[Path]:
    if roots is None:
        return []
    normalized: List[Path] = []
    for root in roots:
        normalized.append(_normalize_root(root))
    return normalized


def _normalize_root(root: Path | str) -> Path:
    expanded = os.path.expanduser(os.path.expandvars(str(root)))
    path = Path(expanded)
    if not path.is_absolute():
        path = Path.cwd() / path
    return _normalize_path(path)


def _normalize_path(path: Path) -> Path:
    return path.absolute()


__all__ = ["ImportGraph", "resolve_import_graph", "resolve_import_path"]
