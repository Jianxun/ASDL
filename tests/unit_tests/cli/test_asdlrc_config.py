from __future__ import annotations

from pathlib import Path

import pytest

from asdl.cli.config import discover_asdlrc, load_asdlrc


def _write_rc(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_discover_asdlrc_prefers_nearest_parent(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    project_root = repo_root / "project"
    entry_dir = project_root / "src" / "design"
    entry_dir.mkdir(parents=True)
    entry_file = entry_dir / "design.asdl"
    entry_file.write_text("top: top\n", encoding="utf-8")

    top_rc = repo_root / ".asdlrc"
    project_rc = project_root / ".asdlrc"
    _write_rc(top_rc, "schema_version: 1\n")
    _write_rc(project_rc, "schema_version: 1\n")

    found = discover_asdlrc(entry_file)

    assert found == project_rc.absolute()


def test_load_asdlrc_expands_env_and_resolves_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    rc_path = project_root / ".asdlrc"
    rc_path.write_text(
        "\n".join(
            [
                "schema_version: 1",
                "lib_roots:",
                "  - libs",
                "  - ${ASDLRC_DIR}/shared",
                "  - ${EXTRA_ROOT}",
                "  - ${OVERRIDE}/lib",
                "backend_config: configs/backends.yaml",
                "env:",
                "  EXTRA_ROOT: ${ASDLRC_DIR}/extra",
                "  NESTED: ${EXTRA_ROOT}/nested",
                "  OVERRIDE: ${ASDLRC_DIR}/rc_override",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    entry_file = project_root / "entry.asdl"
    entry_file.write_text("top: top\n", encoding="utf-8")

    monkeypatch.setenv("OVERRIDE", "/shell")

    config = load_asdlrc(entry_file)

    assert config is not None
    rc_dir = project_root.absolute()
    assert config.backend_config == rc_dir / "configs" / "backends.yaml"
    assert config.lib_roots == [
        rc_dir / "libs",
        rc_dir / "shared",
        rc_dir / "extra",
        Path("/shell/lib"),
    ]
    assert config.env["EXTRA_ROOT"] == f"{rc_dir}/extra"
    assert config.env["NESTED"] == f"{rc_dir}/extra/nested"
    assert config.env["OVERRIDE"] == f"{rc_dir}/rc_override"
