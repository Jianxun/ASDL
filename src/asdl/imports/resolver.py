from __future__ import annotations

import os
import re
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
from .name_env import NameEnv
from .program_db import ProgramDB


@dataclass(frozen=True)
class ImportGraph:
    entry_file: Path
    documents: dict[Path, AsdlDocument]
    imports: dict[Path, dict[str, Path]]
    program_db: ProgramDB
    name_envs: dict[Path, NameEnv]


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
    except ValueError as exc:
        diagnostics.append(import_path_malformed(import_path, str(exc), loc))
        return None, diagnostics

    try:
        expanded_path = Path(expanded)
    except (TypeError, ValueError) as exc:
        diagnostics.append(import_path_malformed(import_path, str(exc), loc))
        return None, diagnostics

    importer_dir = Path(importing_file).absolute().parent
    lib_paths = _normalize_roots(lib_roots)
    env_paths, env_diags = _env_lib_roots()
    diagnostics.extend(env_diags)

    if _is_explicit_relative(expanded):
        return _resolve_candidate(importer_dir / expanded, import_path, loc)

    if expanded_path.is_absolute():
        return _resolve_candidate(expanded_path, import_path, loc)

    matches: List[Path] = []
    seen: set[Path] = set()
    for candidate in _iter_logical_candidates(
        expanded,
        lib_paths,
        env_paths,
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

    program_db, program_diags = ProgramDB.build(documents)
    diagnostics.extend(program_diags)
    name_envs = {
        file_id: NameEnv(file_id=file_id, bindings=dict(imports_by_file.get(file_id, {})))
        for file_id in documents.keys()
    }

    if any(diag.severity is Severity.ERROR for diag in diagnostics):
        return None, diagnostics
    return ImportGraph(
        entry_file=_normalize_path(Path(entry_file)),
        documents=documents,
        imports=imports_by_file,
        program_db=program_db,
        name_envs=name_envs,
    ), diagnostics


_ENV_VAR_PATTERN = re.compile(r"\$(\w+|\{[^}]+\})")


def _expand_import_path(import_path: str) -> str:
    return _expand_path(import_path)


def _expand_path(path: str) -> str:
    expanded = os.path.expandvars(path)
    expanded = os.path.expanduser(expanded)
    if expanded.strip() == "":
        raise ValueError("Expanded path is empty.")
    if path.startswith("~") and expanded.startswith("~"):
        raise ValueError("User home expansion failed.")
    if _ENV_VAR_PATTERN.search(path) and _ENV_VAR_PATTERN.search(expanded):
        raise ValueError("Environment variable expansion failed.")
    return expanded


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
    lib_roots: Iterable[Path],
    env_roots: Iterable[Path],
) -> Iterable[Path]:
    for root in (*lib_roots, *env_roots):
        yield root / logical_path


def _env_lib_roots() -> Tuple[List[Path], List[Diagnostic]]:
    raw = os.environ.get("ASDL_LIB_PATH", "")
    if not raw:
        return [], []
    roots: List[Path] = []
    diagnostics: List[Diagnostic] = []
    for entry in raw.split(os.pathsep):
        entry = entry.strip()
        if not entry:
            continue
        try:
            expanded = _expand_path(entry)
        except ValueError as exc:
            diagnostics.append(import_path_malformed(entry, str(exc), None))
            continue
        root = _normalize_root(expanded)
        roots.append(root)
    return roots, diagnostics


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
    return Path(os.path.abspath(path))


__all__ = ["ImportGraph", "resolve_import_graph", "resolve_import_path"]
