from __future__ import annotations

import io
from pathlib import Path

import pytest

from asdl.docs.sphinx_domain import ASDL_DOMAIN_NAME, SPHINX_AVAILABLE

pytest.importorskip("sphinx")
from sphinx.application import Sphinx

pytestmark = pytest.mark.skipif(not SPHINX_AVAILABLE, reason="Sphinx not available")

ASDL_SAMPLE = """\
imports:
  lib: libs/example.asdl
modules:
  top:
    variables:
      VDD: 1.2
    patterns:
      P: <1|2>
    instances:
      m1: dev L=1u
    nets:
      $IN: [m1.A]
      OUT: [m1.B]
"""


def _write_sphinx_project(tmp_path: Path) -> Path:
    repo_root = Path(__file__).resolve().parents[3]
    srcdir = tmp_path / "src"
    srcdir.mkdir()

    conf_path = srcdir / "conf.py"
    conf_path.write_text(
        "\n".join(
            [
                "import sys",
                "from pathlib import Path",
                f"sys.path.insert(0, {repr(str(repo_root / 'src'))})",
                "project = 'ASDL Test'",
                "extensions = ['asdl.docs.sphinx_domain']",
                "root_doc = 'index'",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (srcdir / "index.rst").write_text(
        ".. asdl:document:: sample.asdl\n",
        encoding="utf-8",
    )
    (srcdir / "sample.asdl").write_text(ASDL_SAMPLE, encoding="utf-8")
    return srcdir


def test_sphinx_document_directive_registers_objects(tmp_path: Path) -> None:
    srcdir = _write_sphinx_project(tmp_path)
    outdir = tmp_path / "_build"
    doctreedir = tmp_path / "_doctrees"

    app = Sphinx(
        srcdir=str(srcdir),
        confdir=str(srcdir),
        outdir=str(outdir),
        doctreedir=str(doctreedir),
        buildername="html",
        status=io.StringIO(),
        warning=io.StringIO(),
        freshenv=True,
    )
    app.build(force_all=True)

    domain = app.env.get_domain(ASDL_DOMAIN_NAME)
    objects = domain.data.get("objects", {})
    expected = {
        ("doc", "sample_doc"),
        ("import", "sample::lib"),
        ("module", "top"),
        ("port", "top::$IN"),
        ("net", "top::$IN"),
        ("net", "top::OUT"),
        ("var", "top::VDD"),
        ("inst", "top::m1"),
        ("pattern", "top::P"),
    }
    missing = expected - set(objects.keys())
    assert not missing
