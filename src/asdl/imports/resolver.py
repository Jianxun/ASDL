from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from asdl.ast.location import Locatable
from asdl.diagnostics import Diagnostic

from .diagnostics import import_path_malformed, import_path_missing


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

    for candidate in _iter_logical_candidates(
        expanded,
        root,
        include_paths,
        env_paths,
        lib_paths,
    ):
        if candidate.is_file():
            return _normalize_path(candidate), diagnostics

    diagnostics.append(import_path_missing(import_path, loc))
    return None, diagnostics


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


__all__ = ["resolve_import_path"]
