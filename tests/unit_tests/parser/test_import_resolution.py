from pathlib import Path

import pytest

from asdl.diagnostics import Severity
from asdl.ast.location import Locatable
from asdl.imports.resolver import resolve_import_graph, resolve_import_path


def _write_stub(path: Path, imports: dict[str, str] | None = None) -> None:
    lines: list[str] = []
    if imports:
        lines.append("imports:")
        for namespace, target in imports.items():
            lines.append(f"  {namespace}: {target}")
    lines.extend(["modules:", "  top: {}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_dup_symbol_stub(path: Path) -> None:
    lines = [
        "modules:",
        "  dup: {}",
        "devices:",
        "  dup:",
        "    backends:",
        "      sim.ngspice:",
        '        template: "X{inst} {ports} {ref}"',
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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


def test_resolve_logical_path_project_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root = tmp_path / "project"
    include_root = tmp_path / "include"
    env_root = tmp_path / "env"
    lib_root = tmp_path / "lib"
    for root in (project_root, include_root, env_root, lib_root):
        root.mkdir()
    entry_file = project_root / "entry.asdl"
    _write_stub(entry_file)
    _write_stub(project_root / "shared.asdl")
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


def test_resolve_logical_path_ambiguity_ordering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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
    loc = Locatable(
        file=str(entry_file),
        start_line=1,
        start_col=1,
        end_line=1,
        end_col=2,
    )

    resolved, diagnostics = resolve_import_path(
        "shared.asdl",
        importing_file=entry_file,
        project_root=project_root,
        include_roots=[include_root],
        lib_roots=[lib_root],
        loc=loc,
    )

    assert resolved is None
    assert diagnostics
    diag = diagnostics[0]
    assert diag.code == "AST-015"
    assert diag.severity is Severity.ERROR
    assert diag.notes == [
        "Matches (root order):",
        str((project_root / "shared.asdl").absolute()),
        str((include_root / "shared.asdl").absolute()),
        str((env_root / "shared.asdl").absolute()),
        str((lib_root / "shared.asdl").absolute()),
    ]


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


def test_resolve_import_cycle_single(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ASDL_LIB_PATH", raising=False)
    project_root = tmp_path / "project"
    project_root.mkdir()
    file_a = project_root / "a.asdl"
    file_b = project_root / "b.asdl"
    _write_stub(file_a, imports={"b": "b.asdl"})
    _write_stub(file_b, imports={"a": "a.asdl"})

    result, diagnostics = resolve_import_graph(
        file_a,
        project_root=project_root,
    )

    assert result is None
    assert diagnostics
    diag = diagnostics[0]
    assert diag.code == "AST-012"
    expected_chain = " -> ".join(
        [str(file_a.absolute()), str(file_b.absolute()), str(file_a.absolute())]
    )
    assert expected_chain in diag.message


def test_resolve_import_cycle_multi_hop(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ASDL_LIB_PATH", raising=False)
    project_root = tmp_path / "project"
    project_root.mkdir()
    file_a = project_root / "a.asdl"
    file_b = project_root / "b.asdl"
    file_c = project_root / "c.asdl"
    _write_stub(file_a, imports={"b": "b.asdl"})
    _write_stub(file_b, imports={"c": "c.asdl"})
    _write_stub(file_c, imports={"a": "a.asdl"})

    result, diagnostics = resolve_import_graph(
        file_a,
        project_root=project_root,
    )

    assert result is None
    assert diagnostics
    diag = diagnostics[0]
    assert diag.code == "AST-012"
    expected_chain = " -> ".join(
        [
            str(file_a.absolute()),
            str(file_b.absolute()),
            str(file_c.absolute()),
            str(file_a.absolute()),
        ]
    )
    assert expected_chain in diag.message


def test_program_db_dedupes_file_ids(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ASDL_LIB_PATH", raising=False)
    project_root = tmp_path / "project"
    project_root.mkdir()
    deps_dir = project_root / "deps"
    deps_dir.mkdir()
    entry_file = project_root / "entry.asdl"
    dep_file = deps_dir / "dep.asdl"
    _write_stub(dep_file)
    _write_stub(
        entry_file,
        imports={
            "a": "./deps/dep.asdl",
            "b": "./deps/../deps/dep.asdl",
        },
    )

    result, diagnostics = resolve_import_graph(
        entry_file,
        project_root=project_root,
    )

    assert diagnostics == []
    assert result is not None
    assert len(result.program_db.documents) == 2
    entry_id = entry_file.absolute()
    dep_id = dep_file.absolute()
    name_env = result.name_envs[entry_id]
    assert name_env.bindings["a"] == dep_id
    assert name_env.bindings["b"] == dep_id


def test_duplicate_symbol_names_emit_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ASDL_LIB_PATH", raising=False)
    entry_file = tmp_path / "entry.asdl"
    _write_dup_symbol_stub(entry_file)

    result, diagnostics = resolve_import_graph(entry_file)

    assert result is None
    assert diagnostics
    diag = diagnostics[0]
    assert diag.code == "AST-014"
    assert diag.severity is Severity.ERROR
