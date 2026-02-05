from __future__ import annotations

from pathlib import Path
import shutil

from asdl.docs.depgraph import module_identifier
from asdl.docs.sphinx_domain import (
    collect_asdl_project_entries,
    load_asdl_project_manifest,
    write_asdl_project_pages,
)

FIXTURES = Path(__file__).parent / "fixtures" / "project_manifest_v1"


def test_load_asdl_project_manifest_preserves_list_order() -> None:
    manifest = load_asdl_project_manifest(FIXTURES / "project.yaml")

    assert manifest.schema_version == 1
    assert manifest.project_name == "Test Project"
    assert manifest.readme == "README"
    assert list(manifest.docs) == ["docs/intro", "docs/usage"]

    assert [entry.file for entry in manifest.entrances] == [
        "libs/alpha/top.asdl",
        "libs/beta/top.asdl",
    ]
    assert [entry.module for entry in manifest.entrances] == [
        "top_alpha",
        "top_beta",
    ]
    assert manifest.entrances[0].description == "Alpha entry"
    assert manifest.entrances[1].description is None

    assert [library.name for library in manifest.libraries] == [
        "Alpha Library",
        "Beta Library",
    ]
    assert [library.path for library in manifest.libraries] == [
        "libs/alpha",
        "libs/beta",
    ]
    assert list(manifest.libraries[0].exclude) == [
        "_archive/**",
        "skip.asdl",
    ]


def test_collect_asdl_project_entries_expands_libraries_with_excludes() -> None:
    manifest_path = FIXTURES / "project.yaml"
    entries = collect_asdl_project_entries(manifest_path, srcdir=FIXTURES)
    sources = [entry.source for entry in entries]

    assert "libs/alpha/top.asdl" in sources
    assert "libs/alpha/nested/keep.asdl" in sources
    assert "libs/alpha/nested/skip.asdl" in sources
    assert "libs/beta/top.asdl" in sources
    assert "libs/beta/extra.asdl" in sources

    assert "libs/alpha/skip.asdl" not in sources
    assert "libs/alpha/_archive/old.asdl" not in sources

    alpha_indexes = [
        idx for idx, source in enumerate(sources) if source.startswith("libs/alpha/")
    ]
    beta_indexes = [
        idx for idx, source in enumerate(sources) if source.startswith("libs/beta/")
    ]
    assert alpha_indexes
    assert beta_indexes
    assert max(alpha_indexes) < min(beta_indexes)


def test_project_nav_orders_sections(tmp_path: Path) -> None:
    srcdir = tmp_path / "project"
    shutil.copytree(FIXTURES, srcdir)
    manifest_path = srcdir / "project.yaml"
    manifest = load_asdl_project_manifest(manifest_path)
    entries = collect_asdl_project_entries(manifest_path, srcdir=srcdir)

    output_dir = srcdir / "_generated"
    write_asdl_project_pages(
        entries,
        output_dir=output_dir,
        manifest=manifest,
        srcdir=srcdir,
    )

    nav_text = (output_dir / "project.rst").read_text(encoding="utf-8")
    readme_index = nav_text.index("Test Project <../README>")
    intro_index = nav_text.index("../docs/intro")
    entrances_index = nav_text.index("Entrances")
    libraries_index = nav_text.index("Libraries")

    assert readme_index < intro_index < entrances_index < libraries_index


def test_project_nav_renders_entrance_links(tmp_path: Path) -> None:
    srcdir = tmp_path / "project"
    shutil.copytree(FIXTURES, srcdir)
    manifest_path = srcdir / "project.yaml"
    manifest = load_asdl_project_manifest(manifest_path)
    entries = collect_asdl_project_entries(manifest_path, srcdir=srcdir)

    output_dir = srcdir / "_generated"
    write_asdl_project_pages(
        entries,
        output_dir=output_dir,
        manifest=manifest,
        srcdir=srcdir,
    )

    nav_text = (output_dir / "project.rst").read_text(encoding="utf-8")
    alpha_file = (srcdir / "libs" / "alpha" / "top.asdl").resolve(
        strict=False
    )
    alpha_module_id = module_identifier("top_alpha", str(alpha_file))

    assert (
        f":asdl:module:`top_alpha <{alpha_module_id}>`" in nav_text
    )
    assert (
        ":doc:`libs/alpha/top.asdl <libs/alpha/top>`" in nav_text
    )
    assert "Alpha entry" in nav_text


def test_project_library_page_renders_module_table(tmp_path: Path) -> None:
    srcdir = tmp_path / "project"
    srcdir.mkdir()
    libs_dir = srcdir / "libs" / "alpha"
    nested_dir = libs_dir / "nested"
    nested_dir.mkdir(parents=True)

    file_a = libs_dir / "a.asdl"
    file_b = nested_dir / "b.asdl"
    file_a.write_text(
        "modules:\n  # Alpha module.\n  Alpha: {}\n",
        encoding="utf-8",
    )
    file_b.write_text(
        "modules:\n  # Beta module.\n  Beta: {}\n",
        encoding="utf-8",
    )

    manifest_path = srcdir / "project.yaml"
    manifest_path.write_text(
        "schema_version: 1\n"
        "libraries:\n"
        "  - name: Alpha Library\n"
        "    path: libs/alpha\n",
        encoding="utf-8",
    )
    manifest = load_asdl_project_manifest(manifest_path)
    entries = collect_asdl_project_entries(manifest_path, srcdir=srcdir)

    output_dir = srcdir / "_generated"
    write_asdl_project_pages(
        entries,
        output_dir=output_dir,
        manifest=manifest,
        srcdir=srcdir,
    )

    pages = list((output_dir / "libraries").glob("*.rst"))
    assert len(pages) == 1
    text = pages[0].read_text(encoding="utf-8")

    row_a = ":asdl:doc:`libs/alpha/a.asdl <a_doc>`"
    row_b = ":asdl:doc:`libs/alpha/nested/b.asdl <b_doc>`"
    assert text.index(row_a) < text.index(row_b)

    file_a_id = str(file_a.resolve(strict=False))
    file_b_id = str(file_b.resolve(strict=False))
    assert (
        f":asdl:module:`Alpha <{module_identifier('Alpha', file_a_id)}>`"
        in text
    )
    assert (
        f":asdl:module:`Beta <{module_identifier('Beta', file_b_id)}>`"
        in text
    )
    assert "Alpha module." in text
    assert "Beta module." in text
