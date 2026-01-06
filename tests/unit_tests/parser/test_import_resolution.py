from pathlib import Path

import pytest

from asdl.imports.resolver import resolve_program


@pytest.fixture(autouse=True)
def _clear_asdl_lib_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ASDL_LIB_PATH", raising=False)


def _module_doc(imports: dict[str, str] | None = None) -> str:
    lines = []
    if imports:
        lines.append("imports:")
        for namespace, path in imports.items():
            lines.append(f"  {namespace}: {path}")
    lines.extend(
        [
            "modules:",
            "  top:",
            "    nets:",
            "      $OUT:",
            "        - I1.P",
        ]
    )
    return "\n".join(lines)


def _device_doc(name: str) -> str:
    return "\n".join(
        [
            "devices:",
            f"  {name}:",
            "    backends:",
            "      ngspice:",
            "        template: \"X{inst} {ports}\"",
        ]
    )


def test_resolve_ambiguous_logical_path_orders_matches(tmp_path: Path) -> None:
    root_dir = tmp_path / "root"
    include_dir = tmp_path / "include"
    root_dir.mkdir()
    include_dir.mkdir()

    entry_path = root_dir / "entry.asdl"
    entry_path.write_text(_module_doc({"lib": "shared.asdl"}), encoding="utf-8")

    shared_root = root_dir / "shared.asdl"
    shared_root.write_text(_module_doc(), encoding="utf-8")

    shared_include = include_dir / "shared.asdl"
    shared_include.write_text(_module_doc(), encoding="utf-8")

    resolved, diagnostics = resolve_program(
        entry_path, root_dir=root_dir, include_roots=[include_dir]
    )

    assert resolved is None
    diag = next(d for d in diagnostics if d.code == "AST-015")
    match_notes = [note for note in (diag.notes or []) if note.startswith("Match:")]
    assert match_notes == [
        f"Match: {shared_root}",
        f"Match: {shared_include}",
    ]


def test_resolve_import_cycle(tmp_path: Path) -> None:
    entry_path = tmp_path / "a.asdl"
    entry_path.write_text(_module_doc({"b": "./b.asdl"}), encoding="utf-8")

    other_path = tmp_path / "b.asdl"
    other_path.write_text(_module_doc({"a": "./a.asdl"}), encoding="utf-8")

    resolved, diagnostics = resolve_program(entry_path)

    assert resolved is None
    diag = next(d for d in diagnostics if d.code == "AST-012")
    assert "a.asdl" in diag.message
    assert "b.asdl" in diag.message


def test_resolve_missing_import(tmp_path: Path) -> None:
    entry_path = tmp_path / "entry.asdl"
    entry_path.write_text(_module_doc({"missing": "missing.asdl"}), encoding="utf-8")

    resolved, diagnostics = resolve_program(entry_path)

    assert resolved is None
    assert any(d.code == "AST-010" for d in diagnostics)


def test_resolve_duplicate_symbols_in_file(tmp_path: Path) -> None:
    entry_path = tmp_path / "dup.asdl"
    entry_path.write_text(
        "\n".join(
            [
                _module_doc(),
                _device_doc("top"),
            ]
        ),
        encoding="utf-8",
    )

    resolved, diagnostics = resolve_program(entry_path)

    assert resolved is None
    assert any(d.code == "AST-014" for d in diagnostics)


def test_dedupe_same_file_id_across_paths(tmp_path: Path) -> None:
    lib_dir = tmp_path / "lib"
    lib_dir.mkdir()
    dep_path = lib_dir / "dep.asdl"
    dep_path.write_text(_module_doc(), encoding="utf-8")

    entry_path = tmp_path / "entry.asdl"
    entry_path.write_text(
        _module_doc({"a": "./lib/dep.asdl", "b": "lib/dep.asdl"}),
        encoding="utf-8",
    )

    resolved, diagnostics = resolve_program(entry_path)

    assert resolved is not None
    assert not any(d.severity.value in ("error", "fatal") for d in diagnostics)
    entry_env = resolved.name_envs[resolved.entry_file_id]
    assert entry_env.namespaces["a"] == entry_env.namespaces["b"]
    assert len(resolved.program.documents) == 2
