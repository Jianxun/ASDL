import os
from pathlib import Path

from asdl.diagnostics import Severity
from asdl.imports import resolve_program


def _write_module_file(path: Path, *, imports: dict[str, str] | None = None) -> None:
    lines: list[str] = []
    if imports:
        lines.append("imports:")
        for namespace, import_path in imports.items():
            lines.append(f"  {namespace}: {import_path}")
    lines.extend(
        [
            "modules:",
            "  top:",
            "    nets:",
            "      $OUT:",
            "        - I1.P",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_module_and_device(path: Path, name: str) -> None:
    content = "\n".join(
        [
            "modules:",
            f"  {name}:",
            "    nets:",
            "      $OUT:",
            "        - I1.P",
            "devices:",
            f"  {name}:",
            "    backends:",
            "      sim.ngspice:",
            "        template: \"X{ports}\"",
        ]
    )
    path.write_text(content, encoding="utf-8")


def _abs_path(path: Path) -> str:
    return os.path.abspath(os.path.normpath(str(path)))


def test_import_resolution_prefers_root_dir(tmp_path: Path) -> None:
    entry_dir = tmp_path / "entry"
    root_dir = tmp_path / "root"
    include_dir = tmp_path / "include"
    entry_dir.mkdir()
    root_dir.mkdir()
    include_dir.mkdir()

    entry_file = entry_dir / "entry.asdl"
    _write_module_file(entry_file, imports={"lib": "shared.asdl"})

    root_file = root_dir / "shared.asdl"
    include_file = include_dir / "shared.asdl"
    _write_module_file(root_file)
    _write_module_file(include_file)

    resolved, diagnostics = resolve_program(
        entry_file,
        root_dir=root_dir,
        include_dirs=[include_dir],
        lib_path_env="",
    )

    assert resolved is not None
    assert not diagnostics
    entry_env = resolved.name_envs[resolved.entry_file_id]
    assert entry_env.namespaces["lib"] == _abs_path(root_file)


def test_import_cycle_detected(tmp_path: Path) -> None:
    entry_file = tmp_path / "a.asdl"
    b_file = tmp_path / "b.asdl"

    _write_module_file(entry_file, imports={"b": "b.asdl"})
    _write_module_file(b_file, imports={"a": "a.asdl"})

    resolved, diagnostics = resolve_program(entry_file, root_dir=tmp_path, lib_path_env="")

    assert resolved is not None
    cycle_diags = [diag for diag in diagnostics if diag.code == "AST-012"]
    assert cycle_diags
    assert cycle_diags[0].severity is Severity.ERROR


def test_missing_import_diagnostic(tmp_path: Path) -> None:
    entry_file = tmp_path / "entry.asdl"
    _write_module_file(entry_file, imports={"missing": "nope.asdl"})

    resolved, diagnostics = resolve_program(entry_file, root_dir=tmp_path, lib_path_env="")

    assert resolved is not None
    missing_diags = [diag for diag in diagnostics if diag.code == "AST-010"]
    assert missing_diags
    assert missing_diags[0].severity is Severity.ERROR


def test_duplicate_symbol_in_file(tmp_path: Path) -> None:
    entry_file = tmp_path / "dup.asdl"
    _write_module_and_device(entry_file, "same_name")

    resolved, diagnostics = resolve_program(entry_file, root_dir=tmp_path, lib_path_env="")

    assert resolved is not None
    dup_diags = [diag for diag in diagnostics if diag.code == "AST-014"]
    assert dup_diags


def test_dedupe_file_id_across_paths(tmp_path: Path) -> None:
    entry_file = tmp_path / "entry.asdl"
    lib_dir = tmp_path / "lib"
    lib_dir.mkdir()
    target_file = lib_dir / "shared.asdl"

    _write_module_file(target_file)
    _write_module_file(
        entry_file,
        imports={
            "a": "lib/shared.asdl",
            "b": "lib/../lib/shared.asdl",
        },
    )

    resolved, diagnostics = resolve_program(entry_file, root_dir=tmp_path, lib_path_env="")

    assert resolved is not None
    assert not diagnostics
    entry_env = resolved.name_envs[resolved.entry_file_id]
    assert entry_env.namespaces["a"] == entry_env.namespaces["b"]
    assert len(resolved.program.documents) == 2
