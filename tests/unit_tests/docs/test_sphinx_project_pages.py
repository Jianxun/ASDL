from __future__ import annotations

from pathlib import Path

from asdl.docs.sphinx_domain import collect_asdl_project_entries


def test_collect_asdl_project_entries_orders_by_entry_path(tmp_path: Path) -> None:
    manifest = tmp_path / "project.yaml"
    manifest.write_text(
        """entries:\n  - ../libs/zeta.asdl\n  - ../libs/alpha.asdl\n  - ../libs/sub/beta.asdl\n""",
        encoding="utf-8",
    )

    entries = collect_asdl_project_entries(manifest, srcdir=tmp_path)

    assert [entry.source for entry in entries] == [
        "../libs/alpha.asdl",
        "../libs/sub/beta.asdl",
        "../libs/zeta.asdl",
    ]


def test_collect_asdl_project_entries_expands_import_graph(
    tmp_path: Path,
) -> None:
    entry = tmp_path / "top.asdl"
    lib_dir = tmp_path / "lib"
    lib_dir.mkdir()
    (lib_dir / "child.asdl").write_text(
        "modules:\n  Child: {}\n",
        encoding="utf-8",
    )
    entry.write_text(
        "imports:\n"
        "  lib: ./lib/child.asdl\n"
        "modules:\n"
        "  Top:\n"
        "    instances:\n"
        "      u1: \"lib.Child\"\n",
        encoding="utf-8",
    )

    manifest = tmp_path / "project.yaml"
    manifest.write_text("entries:\n  - top.asdl\n", encoding="utf-8")

    entries = collect_asdl_project_entries(manifest, srcdir=tmp_path)
    sources = [entry.source for entry in entries]

    assert sources == ["lib/child.asdl", "top.asdl"]
    assert len(sources) == len(set(sources))
