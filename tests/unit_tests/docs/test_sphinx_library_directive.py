from __future__ import annotations

from pathlib import Path

from asdl.docs.sphinx_domain import collect_asdl_library_files


def test_collect_asdl_library_files_orders_by_relative_path(tmp_path: Path) -> None:
    root = tmp_path / "libs"
    (root / "sub").mkdir(parents=True)

    (root / "b.asdl").write_text("modules: {}\n", encoding="utf-8")
    (root / "a.asdl").write_text("modules: {}\n", encoding="utf-8")
    (root / "sub" / "b.asdl").write_text("modules: {}\n", encoding="utf-8")
    (root / "sub" / "a.asdl").write_text("modules: {}\n", encoding="utf-8")
    (root / "notes.txt").write_text("ignore\n", encoding="utf-8")

    files = collect_asdl_library_files(root)

    assert [path.relative_to(root).as_posix() for path in files] == [
        "a.asdl",
        "b.asdl",
        "sub/a.asdl",
        "sub/b.asdl",
    ]
