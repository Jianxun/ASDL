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
