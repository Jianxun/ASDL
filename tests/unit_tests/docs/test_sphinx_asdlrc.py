from __future__ import annotations

import io
from pathlib import Path

import pytest

from asdl.docs.sphinx_domain import ASDL_DEPGRAPH_ENV_KEY, SPHINX_AVAILABLE

pytest.importorskip("sphinx")
from sphinx.application import Sphinx

pytestmark = pytest.mark.skipif(not SPHINX_AVAILABLE, reason="Sphinx not available")


def _write_sphinx_project(tmp_path: Path) -> Path:
    repo_root = Path(__file__).resolve().parents[3]
    srcdir = tmp_path / "src"
    srcdir.mkdir()

    libs_dir = tmp_path / "libs"
    libs_dir.mkdir()
    (libs_dir / "lib.asdl").write_text(
        "modules:\n  Child: {}\n",
        encoding="utf-8",
    )

    (srcdir / "entry.asdl").write_text(
        "imports:\n"
        "  lib: lib.asdl\n"
        "modules:\n"
        "  Top:\n"
        "    instances:\n"
        "      u1: \"lib.Child\"\n",
        encoding="utf-8",
    )

    (srcdir / "project.yaml").write_text(
        "entries:\n  - entry.asdl\n",
        encoding="utf-8",
    )

    (srcdir / ".asdlrc").write_text(
        "schema_version: 1\nlib_roots:\n  - ../libs\n",
        encoding="utf-8",
    )

    (srcdir / "conf.py").write_text(
        "\n".join(
            [
                "import sys",
                "from pathlib import Path",
                f"sys.path.insert(0, {repr(str(repo_root / 'src'))})",
                "project = 'ASDL Test'",
                "extensions = ['asdl.docs.sphinx_domain']",
                "root_doc = 'index'",
                "asdl_project_manifest = 'project.yaml'",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (srcdir / "index.rst").write_text(
        "ASDL Project\n============\n\n.. toctree::\n   :maxdepth: 1\n\n   _generated/project\n",
        encoding="utf-8",
    )

    return srcdir


def test_project_manifest_uses_asdlrc_lib_roots(tmp_path: Path) -> None:
    srcdir = _write_sphinx_project(tmp_path)
    outdir = tmp_path / "_build"
    doctreedir = tmp_path / "_doctrees"
    warning = io.StringIO()

    app = Sphinx(
        srcdir=str(srcdir),
        confdir=str(srcdir),
        outdir=str(outdir),
        doctreedir=str(doctreedir),
        buildername="html",
        status=io.StringIO(),
        warning=warning,
        freshenv=True,
    )
    app.build(force_all=True)

    assert "AST-010" not in warning.getvalue()

    graph = getattr(app.env, ASDL_DEPGRAPH_ENV_KEY, None)
    assert graph is not None
    lib_file_id = str((tmp_path / "libs" / "lib.asdl").resolve())
    assert lib_file_id in {item.file_id for item in graph.files}
