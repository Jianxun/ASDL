from __future__ import annotations

from pathlib import Path

from asdl.docs.sphinx_domain import (
    collect_asdl_project_entries,
    write_asdl_project_pages,
)


def test_collect_asdl_project_entries_preserves_library_order(
    tmp_path: Path,
) -> None:
    libs = tmp_path / "libs"
    alpha_dir = libs / "alpha"
    zeta_dir = libs / "zeta"
    alpha_dir.mkdir(parents=True)
    zeta_dir.mkdir(parents=True)

    (alpha_dir / "alpha.asdl").write_text(
        "modules:\n  Alpha: {}\n",
        encoding="utf-8",
    )
    (zeta_dir / "zeta.asdl").write_text(
        "modules:\n  Zeta: {}\n",
        encoding="utf-8",
    )

    manifest = tmp_path / "project.yaml"
    manifest.write_text(
        "schema_version: 1\n"
        "libraries:\n"
        "  - name: Zeta\n"
        "    path: libs/zeta\n"
        "  - name: Alpha\n"
        "    path: libs/alpha\n",
        encoding="utf-8",
    )

    entries = collect_asdl_project_entries(manifest, srcdir=tmp_path)

    assert [entry.source for entry in entries] == [
        "libs/zeta/zeta.asdl",
        "libs/alpha/alpha.asdl",
    ]


def test_collect_asdl_project_entries_does_not_expand_import_graph(
    tmp_path: Path,
) -> None:
    entry_dir = tmp_path / "entry"
    entry_dir.mkdir()
    entry = entry_dir / "top.asdl"

    lib_dir = tmp_path / "otherlib"
    lib_dir.mkdir()
    (lib_dir / "child.asdl").write_text(
        "modules:\n  Child: {}\n",
        encoding="utf-8",
    )
    entry.write_text(
        "imports:\n"
        "  lib: ../otherlib/child.asdl\n"
        "modules:\n"
        "  Top:\n"
        "    instances:\n"
        "      u1: \"lib.Child\"\n",
        encoding="utf-8",
    )

    manifest = tmp_path / "project.yaml"
    manifest.write_text(
        "schema_version: 1\n"
        "libraries:\n"
        "  - name: Entry\n"
        "    path: entry\n",
        encoding="utf-8",
    )

    entries = collect_asdl_project_entries(manifest, srcdir=tmp_path)
    sources = [entry.source for entry in entries]

    assert sources == ["entry/top.asdl"]


def test_project_stub_uses_asdl_document_title(tmp_path: Path) -> None:
    libs = tmp_path / "libs"
    libs.mkdir()
    entry = libs / "inv.asdl"
    entry.write_text("modules:\n  inv: {}\n", encoding="utf-8")

    manifest = tmp_path / "project.yaml"
    manifest.write_text(
        "schema_version: 1\n"
        "libraries:\n"
        "  - name: Libs\n"
        "    path: libs\n",
        encoding="utf-8",
    )

    entries = collect_asdl_project_entries(manifest, srcdir=tmp_path)
    output_dir = tmp_path / "_generated"
    write_asdl_project_pages(entries, output_dir=output_dir)

    stub_path = output_dir / entries[0].stub_relpath
    stub_text = stub_path.read_text(encoding="utf-8")
    assert stub_text == (
        "..\n"
        "   Generated file. Do not edit directly.\n"
        "\n"
        ".. asdl:document:: libs/inv.asdl\n"
    )
