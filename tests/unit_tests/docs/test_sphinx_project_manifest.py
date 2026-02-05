from __future__ import annotations

from pathlib import Path

from asdl.docs.sphinx_domain import (
    collect_asdl_project_entries,
    load_asdl_project_manifest,
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
