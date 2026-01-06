from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

from asdl.ast import AsdlDocument, parse_file
from asdl.ast.location import Locatable
from asdl.diagnostics import Diagnostic, Severity

from .diagnostics import (
    DUPLICATE_NAMESPACE,
    IMPORT_CYCLE,
    IMPORT_PATH_NOT_FOUND,
    MALFORMED_IMPORT_PATH,
    _diagnostic,
)
from .name_env import NameEnv
from .program_db import ProgramDB


@dataclass(frozen=True)
class ResolvedProgram:
    entry_file_id: str
    program: ProgramDB
    name_envs: dict[str, NameEnv]


def resolve_program(
    entry_file: Path,
    *,
    root_dir: Optional[Path] = None,
    include_dirs: Iterable[Path] = (),
    lib_dirs: Iterable[Path] = (),
    lib_path_env: Optional[str] = None,
) -> Tuple[Optional[ResolvedProgram], List[Diagnostic]]:
    diagnostics: List[Diagnostic] = []

    entry_path = _expand_path(entry_file)
    entry_file_id = _normalize_path(entry_path)
    entry_path = Path(entry_file_id)

    if root_dir is None:
        root_dir = entry_path.parent

    root_dir = Path(_normalize_path(_expand_path(root_dir)))
    include_dirs = tuple(_normalize_dir(path) for path in include_dirs)
    lib_dirs = tuple(_normalize_dir(path) for path in lib_dirs)
    lib_path_dirs = _parse_lib_path(lib_path_env)

    resolver = _ImportResolver(
        root_dir=root_dir,
        include_dirs=include_dirs,
        lib_dirs=lib_dirs,
        lib_path_dirs=lib_path_dirs,
    )
    program, name_envs, resolve_diags = resolver.resolve(entry_path)
    diagnostics.extend(resolve_diags)
    if program is None:
        return None, diagnostics

    return ResolvedProgram(
        entry_file_id=entry_file_id, program=program, name_envs=name_envs
    ), diagnostics


@dataclass
class _ImportResolver:
    root_dir: Path
    include_dirs: Sequence[Path]
    lib_dirs: Sequence[Path]
    lib_path_dirs: Sequence[Path]

    def resolve(
        self, entry_path: Path
    ) -> Tuple[Optional[ProgramDB], dict[str, NameEnv], List[Diagnostic]]:
        diagnostics: List[Diagnostic] = []
        program = ProgramDB()
        name_envs: dict[str, NameEnv] = {}

        visiting: set[str] = set()
        visited: set[str] = set()

        def load_file(file_path: Path, stack: List[str]) -> None:
            file_id = _normalize_path(file_path)
            if file_id in visiting:
                diagnostics.append(self._cycle_diagnostic(file_id, stack))
                return
            if file_id in visited:
                return

            visiting.add(file_id)
            stack.append(file_id)

            document, parse_diags = parse_file(str(file_id))
            diagnostics.extend(parse_diags)
            if document is None:
                visiting.remove(file_id)
                stack.pop()
                return

            diagnostics.extend(program.register_document(file_id, document))
            name_envs[file_id] = self._resolve_imports(file_id, document, diagnostics)

            for imported_file_id in name_envs[file_id].namespaces.values():
                load_file(Path(imported_file_id), stack)

            visiting.remove(file_id)
            visited.add(file_id)
            stack.pop()

        load_file(entry_path, [])

        if not program.documents:
            return None, name_envs, diagnostics

        return program, name_envs, diagnostics

    def _resolve_imports(
        self,
        file_id: str,
        document: AsdlDocument,
        diagnostics: List[Diagnostic],
    ) -> NameEnv:
        namespaces: dict[str, str] = {}
        imports = document.imports or {}
        for namespace, import_path in imports.items():
            if namespace in namespaces:
                diagnostics.append(
                    _diagnostic(
                        DUPLICATE_NAMESPACE,
                        f"Duplicate import namespace '{namespace}' in '{file_id}'",
                        Severity.ERROR,
                        loc=self._import_loc(document, namespace),
                    )
                )
                continue

            resolved = self._resolve_import_path(
                file_id,
                import_path,
                diagnostics,
                loc=self._import_loc(document, namespace),
            )
            if resolved is None:
                continue
            namespaces[namespace] = resolved
        return NameEnv(file_id=file_id, namespaces=namespaces)

    def _resolve_import_path(
        self,
        file_id: str,
        import_path: str,
        diagnostics: List[Diagnostic],
        *,
        loc: Locatable | None,
    ) -> Optional[str]:
        expanded = _expand_path(import_path)
        if not expanded:
            diagnostics.append(
                _diagnostic(
                    MALFORMED_IMPORT_PATH,
                    f"Malformed import path in '{file_id}': '{import_path}'",
                    Severity.ERROR,
                    loc=loc,
                )
            )
            return None

        try:
            expanded_path = Path(expanded)
        except (TypeError, ValueError) as exc:
            diagnostics.append(
                _diagnostic(
                    MALFORMED_IMPORT_PATH,
                    f"Malformed import path in '{file_id}': '{import_path}' ({exc})",
                    Severity.ERROR,
                    loc=loc,
                )
            )
            return None

        if _is_explicit_relative(expanded):
            candidate = Path(file_id).parent / expanded
            return self._finalize_candidate(
                candidate,
                file_id,
                import_path,
                diagnostics,
                loc=loc,
            )

        if expanded_path.is_absolute():
            return self._finalize_candidate(
                expanded_path,
                file_id,
                import_path,
                diagnostics,
                loc=loc,
            )

        roots = (
            (self.root_dir,) + tuple(self.include_dirs) + tuple(self.lib_path_dirs) + tuple(self.lib_dirs)
        )
        dir_candidates: List[Path] = []
        for root in roots:
            candidate = root / expanded
            if candidate.exists():
                if candidate.is_dir():
                    dir_candidates.append(candidate)
                    continue
                return _normalize_path(candidate)

        if dir_candidates:
            diagnostics.append(
                _diagnostic(
                    MALFORMED_IMPORT_PATH,
                    f"Import path is a directory: '{import_path}'",
                    Severity.ERROR,
                    loc=loc,
                )
            )
            return None

        diagnostics.append(
            _diagnostic(
                IMPORT_PATH_NOT_FOUND,
                f"Import path not found: '{import_path}'",
                Severity.ERROR,
                loc=loc,
            )
        )
        return None

    def _finalize_candidate(
        self,
        candidate: Path,
        file_id: str,
        import_path: str,
        diagnostics: List[Diagnostic],
        *,
        loc: Locatable | None,
    ) -> Optional[str]:
        if candidate.exists():
            if candidate.is_dir():
                diagnostics.append(
                    _diagnostic(
                        MALFORMED_IMPORT_PATH,
                        f"Import path is a directory: '{import_path}'",
                        Severity.ERROR,
                        loc=loc,
                    )
                )
                return None
            return _normalize_path(candidate)

        diagnostics.append(
            _diagnostic(
                IMPORT_PATH_NOT_FOUND,
                f"Import path not found: '{import_path}'",
                Severity.ERROR,
                loc=loc,
            )
        )
        return None

    def _cycle_diagnostic(self, file_id: str, stack: List[str]) -> Diagnostic:
        if file_id in stack:
            idx = stack.index(file_id)
            chain = stack[idx:] + [file_id]
        else:
            chain = stack + [file_id]
        chain_str = " -> ".join(chain)
        return _diagnostic(
            IMPORT_CYCLE,
            f"Import cycle detected: {chain_str}",
            Severity.ERROR,
            loc=None,
        )

    def _import_loc(self, document: AsdlDocument, namespace: str) -> Locatable | None:
        imports = document.imports
        if not imports:
            return None
        entry = imports.get(namespace)
        if entry is None:
            return None
        return getattr(entry, "_loc", None)


def _expand_path(path: Path | str) -> str:
    return os.path.expandvars(os.path.expanduser(str(path)))


def _normalize_path(path: Path | str) -> str:
    return os.path.abspath(os.path.normpath(str(path)))


def _normalize_dir(path: Path | str) -> Path:
    return Path(_normalize_path(_expand_path(path)))


def _parse_lib_path(lib_path_env: Optional[str]) -> Tuple[Path, ...]:
    raw = lib_path_env if lib_path_env is not None else os.getenv("ASDL_LIB_PATH", "")
    if not raw:
        return ()

    paths: List[Path] = []
    cwd = Path.cwd()
    for entry in raw.split(os.pathsep):
        if not entry:
            continue
        expanded = _expand_path(entry)
        entry_path = Path(expanded)
        if not entry_path.is_absolute():
            entry_path = cwd / entry_path
        paths.append(_normalize_dir(entry_path))
    return tuple(paths)


def _is_explicit_relative(path: str) -> bool:
    return path.startswith("./") or path.startswith("../")


__all__ = ["ResolvedProgram", "resolve_program"]
