from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence

from asdl.ast import parse_file
from asdl.diagnostics import Diagnostic, Severity

from .diagnostics import (
    ambiguous_import_path,
    import_cycle,
    import_malformed_path,
    import_not_found,
)
from .name_env import NameEnv
from .program_db import ProgramDB


@dataclass(frozen=True)
class ResolvedProgram:
    entry_file_id: str
    program: ProgramDB
    name_envs: Dict[str, NameEnv]


def resolve_program(
    entry_path: Path,
    *,
    root_dir: Optional[Path] = None,
    include_roots: Iterable[Path] = (),
    lib_roots: Iterable[Path] | Mapping[str, Path] = (),
    cwd: Optional[Path] = None,
) -> tuple[ResolvedProgram | None, list[Diagnostic]]:
    if isinstance(lib_roots, Mapping):
        lib_items: Sequence[Path] = tuple(lib_roots.values())
    else:
        lib_items = tuple(lib_roots)
    resolver = _ImportResolver(
        root_dir=root_dir,
        include_roots=tuple(include_roots),
        lib_roots=lib_items,
        cwd=cwd,
    )
    return resolver.resolve(entry_path)


@dataclass
class _ImportResolver:
    root_dir: Optional[Path] = None
    include_roots: Sequence[Path] = ()
    lib_roots: Sequence[Path] = ()
    cwd: Optional[Path] = None
    diagnostics: List[Diagnostic] = field(default_factory=list)
    program: ProgramDB = field(default_factory=ProgramDB)
    name_envs: Dict[str, NameEnv] = field(default_factory=dict)
    _stack: List[str] = field(default_factory=list)

    def resolve(self, entry_path: Path) -> tuple[ResolvedProgram | None, list[Diagnostic]]:
        cwd = self.cwd or Path.cwd()
        entry_file_id = _normalize_path(entry_path)
        entry_path = Path(entry_file_id)

        root_dir = self.root_dir or entry_path.parent
        roots = _collect_roots(
            root_dir=root_dir,
            include_roots=self.include_roots,
            lib_roots=self.lib_roots,
            cwd=cwd,
        )

        self._load_file(entry_path, roots)

        resolved = ResolvedProgram(
            entry_file_id=entry_file_id,
            program=self.program,
            name_envs=self.name_envs,
        )
        if _has_errors(self.diagnostics):
            return None, self.diagnostics
        return resolved, self.diagnostics

    def _load_file(self, path: Path, roots: Sequence[Path]) -> Optional[str]:
        file_id = _normalize_path(path)
        if file_id in self._stack:
            chain = _cycle_chain(self._stack, file_id)
            self.diagnostics.append(import_cycle(chain))
            return None
        if file_id in self.program.documents:
            return file_id

        self._stack.append(file_id)
        document, parse_diags = parse_file(file_id)
        self.diagnostics.extend(parse_diags)
        if document is None:
            self._stack.pop()
            return None

        self.diagnostics.extend(self.program.add_document(file_id, document))

        name_env = NameEnv(file_id=file_id)
        self.name_envs[file_id] = name_env

        for namespace, import_path in (document.imports or {}).items():
            if namespace in name_env.namespaces:
                diag = name_env.bind(namespace, file_id)
                if diag:
                    self.diagnostics.append(diag)
                continue

            resolved_id = _resolve_import_path(
                import_path,
                importer_path=Path(file_id),
                roots=roots,
                diagnostics=self.diagnostics,
            )
            if resolved_id is None:
                continue

            diag = name_env.bind(namespace, resolved_id)
            if diag:
                self.diagnostics.append(diag)
                continue

            self._load_file(Path(resolved_id), roots)

        self._stack.pop()
        return file_id


def _collect_roots(
    *,
    root_dir: Path,
    include_roots: Sequence[Path],
    lib_roots: Sequence[Path],
    cwd: Path,
) -> List[Path]:
    roots: List[Path] = []
    roots.append(_normalize_root(root_dir, cwd))
    for root in include_roots:
        roots.append(_normalize_root(root, cwd))
    roots.extend(_parse_asdl_lib_path(cwd))
    for root in lib_roots:
        if isinstance(root, tuple) and len(root) == 2:
            root = root[1]
        roots.append(_normalize_root(Path(root), cwd))
    return roots


def _resolve_import_path(
    raw_path: str,
    *,
    importer_path: Path,
    roots: Sequence[Path],
    diagnostics: List[Diagnostic],
) -> Optional[str]:
    expanded = _expand_path(raw_path)
    if not expanded or "\x00" in expanded:
        diagnostics.append(import_malformed_path(raw_path))
        return None

    if _is_explicit_relative(expanded):
        candidate = importer_path.parent / expanded
        return _resolve_candidate(candidate, raw_path, diagnostics)

    candidate_path = Path(expanded)
    if candidate_path.is_absolute():
        return _resolve_candidate(candidate_path, raw_path, diagnostics)

    matches: List[str] = []
    seen: set[str] = set()
    invalid: List[str] = []
    for root in roots:
        candidate = root / expanded
        if not candidate.exists():
            continue
        if not candidate.is_file():
            invalid_path = _normalize_path(candidate)
            if invalid_path not in invalid:
                invalid.append(invalid_path)
            continue
        normalized = _normalize_path(candidate)
        if normalized in seen:
            continue
        seen.add(normalized)
        matches.append(normalized)

    if matches:
        if len(matches) == 1:
            return matches[0]
        diagnostics.append(ambiguous_import_path(raw_path, matches))
        return None

    if invalid:
        diagnostics.append(import_malformed_path(raw_path, notes=invalid))
        return None
    diagnostics.append(import_not_found(raw_path))
    return None


def _resolve_candidate(
    candidate: Path, raw_path: str, diagnostics: List[Diagnostic]
) -> Optional[str]:
    if not candidate.exists():
        diagnostics.append(import_not_found(raw_path))
        return None
    if not candidate.is_file():
        diagnostics.append(import_malformed_path(raw_path))
        return None
    return _normalize_path(candidate)


def _normalize_path(path: Path) -> str:
    return os.path.abspath(os.path.normpath(str(path)))


def _normalize_root(root: Path, cwd: Path) -> Path:
    expanded = Path(_expand_path(str(root)))
    if not expanded.is_absolute():
        expanded = cwd / expanded
    return Path(_normalize_path(expanded))


def _expand_path(path: str) -> str:
    expanded = os.path.expandvars(path)
    return str(Path(expanded).expanduser())


def _parse_asdl_lib_path(cwd: Path) -> List[Path]:
    value = os.environ.get("ASDL_LIB_PATH", "")
    if not value:
        return []
    roots: List[Path] = []
    for entry in value.split(os.pathsep):
        if not entry:
            continue
        expanded = Path(_expand_path(entry))
        if not expanded.is_absolute():
            expanded = cwd / expanded
        roots.append(Path(_normalize_path(expanded)))
    return roots


def _is_explicit_relative(path: str) -> bool:
    prefixes = ("./", "../")
    if os.path.sep != "/":
        prefixes += (f".{os.path.sep}", f"..{os.path.sep}")
    if os.path.altsep:
        prefixes += (f".{os.path.altsep}", f"..{os.path.altsep}")
    return path.startswith(prefixes)


def _cycle_chain(stack: Sequence[str], file_id: str) -> List[str]:
    if file_id in stack:
        start = stack.index(file_id)
        return list(stack[start:]) + [file_id]
    return list(stack) + [file_id]


def _has_errors(diagnostics: Iterable[Diagnostic]) -> bool:
    return any(
        diagnostic.severity in (Severity.ERROR, Severity.FATAL)
        for diagnostic in diagnostics
    )


__all__ = ["ResolvedProgram", "resolve_program"]
