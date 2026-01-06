from pathlib import Path

import pytest

from asdl.diagnostics import Severity
from asdl.imports.resolver import resolve_import_path


def _write_stub(path: Path) -> None:
    path.write_text("modules:\n  top: {}\n", encoding="utf-8")


def test_resolve_relative_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ASDL_LIB_PATH", raising=False)
    entry_dir = tmp_path / "project"
    entry_dir.mkdir()
    entry_file = entry_dir / "entry.asdl"
    _write_stub(entry_file)
    lib_dir = entry_dir / "libs"
    lib_dir.mkdir()
    target = lib_dir / "dep.asdl"
    _write_stub(target)

    resolved, diagnostics = resolve_import_path(
        "./libs/dep.asdl",
        importing_file=entry_file,
    )

    assert diagnostics == []
    assert resolved == target.absolute()


def test_resolve_absolute_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ASDL_LIB_PATH", raising=False)
    entry_file = tmp_path / "entry.asdl"
    _write_stub(entry_file)
    target = tmp_path / "dep.asdl"
    _write_stub(target)

    resolved, diagnostics = resolve_import_path(
        str(target),
        importing_file=entry_file,
    )

    assert diagnostics == []
    assert resolved == target.absolute()


def test_resolve_env_expansion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ASDL_LIB_PATH", raising=False)
    env_root = tmp_path / "envroot"
    env_root.mkdir()
    target = env_root / "dep.asdl"
    _write_stub(target)
    entry_file = tmp_path / "entry.asdl"
    _write_stub(entry_file)
    monkeypatch.setenv("ASDL_IMPORT_ROOT", str(env_root))

    resolved, diagnostics = resolve_import_path(
        "$ASDL_IMPORT_ROOT/dep.asdl",
        importing_file=entry_file,
    )

    assert diagnostics == []
    assert resolved == target.absolute()


def test_resolve_logical_path_order(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project_root = tmp_path / "project"
    include_root = tmp_path / "include"
    env_root = tmp_path / "env"
    lib_root = tmp_path / "lib"
    for root in (project_root, include_root, env_root, lib_root):
        root.mkdir()
        _write_stub(root / "shared.asdl")
    entry_file = project_root / "entry.asdl"
    _write_stub(entry_file)
    monkeypatch.setenv("ASDL_LIB_PATH", str(env_root))

    resolved, diagnostics = resolve_import_path(
        "shared.asdl",
        importing_file=entry_file,
        project_root=project_root,
        include_roots=[include_root],
        lib_roots=[lib_root],
    )

    assert diagnostics == []
    assert resolved == (project_root / "shared.asdl").absolute()


def test_resolve_missing_path_emits_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ASDL_LIB_PATH", raising=False)
    entry_file = tmp_path / "entry.asdl"
    _write_stub(entry_file)

    resolved, diagnostics = resolve_import_path(
        "missing.asdl",
        importing_file=entry_file,
    )

    assert resolved is None
    assert diagnostics
    diag = diagnostics[0]
    assert diag.code == "AST-010"
    assert diag.severity is Severity.ERROR
