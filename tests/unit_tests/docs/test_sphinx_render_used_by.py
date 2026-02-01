from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from docutils import nodes

from asdl.ast.parser import parse_file
from asdl.docs.depgraph import build_dependency_graph, module_identifier
from asdl.docs.docstrings import extract_docstrings_from_file
from asdl.docs.sphinx_domain import SPHINX_AVAILABLE, make_asdl_target_id
from asdl.docs.sphinx_render import render_docutils

pytest.importorskip("sphinx")
from sphinx import addnodes

pytestmark = pytest.mark.skipif(not SPHINX_AVAILABLE, reason="Sphinx not available")


def _render_docutils(path: Path, env: object) -> nodes.section:
    document, diagnostics = parse_file(str(path))
    assert diagnostics == []
    assert document is not None
    docstrings = extract_docstrings_from_file(path)
    return render_docutils(document, docstrings, file_path=path, sphinx_env=env)


def _find_section(root: nodes.Node, title: str) -> nodes.section | None:
    for section in root.findall(nodes.section):
        if not section:
            continue
        if isinstance(section[0], nodes.title) and section[0].astext() == title:
            return section
    return None


def test_sphinx_render_links_used_by_and_disambiguation(tmp_path: Path) -> None:
    lib1_path = tmp_path / "lib1.asdl"
    lib2_path = tmp_path / "lib2.asdl"
    entry_path = tmp_path / "entry.asdl"

    lib1_path.write_text(
        "top: Child\n"
        "modules:\n"
        "  Child: {}\n"
        "  Dup: {}\n",
        encoding="utf-8",
    )
    lib2_path.write_text("modules:\n  Dup: {}\n", encoding="utf-8")
    entry_path.write_text(
        "imports:\n"
        "  lib1: ./lib1.asdl\n"
        "  lib2: ./lib2.asdl\n"
        "top: Top\n"
        "modules:\n"
        "  Top:\n"
        "    instances:\n"
        "      u_child: \"lib1.Child\"\n"
        "      u_child2: \"lib1.Child\"\n"
        "      u_dup1: \"lib1.Dup\"\n"
        "      u_dup2: \"lib2.Dup\"\n"
        "      u_local: \"Local\"\n"
        "  Local: {}\n",
        encoding="utf-8",
    )

    graph, diagnostics = build_dependency_graph([entry_path])
    assert diagnostics == []
    assert graph is not None

    env = SimpleNamespace(asdl_dependency_graph=graph, srcdir=str(tmp_path))

    rendered_entry = _render_docutils(entry_path, env)
    entry_id = str(entry_path.resolve())
    lib1_id = str(lib1_path.resolve())
    lib2_id = str(lib2_path.resolve())

    top_id = module_identifier("Top", entry_id)
    child_id = module_identifier("Child", lib1_id)
    dup1_id = module_identifier("Dup", lib1_id)
    dup2_id = module_identifier("Dup", lib2_id)

    target_ids = {target["ids"][0] for target in rendered_entry.findall(nodes.target)}
    assert make_asdl_target_id("module", top_id) in target_ids

    xrefs = list(rendered_entry.findall(addnodes.pending_xref))
    dup_refs = [node for node in xrefs if node.get("reftarget") in {dup1_id, dup2_id}]
    assert {node.astext() for node in dup_refs} == {
        "Dup (lib1.asdl)",
        "Dup (lib2.asdl)",
    }
    child_refs = [node for node in xrefs if node.get("reftarget") == child_id]
    assert child_refs
    assert child_refs[0].astext() == "Child"

    rendered_lib1 = _render_docutils(lib1_path, env)
    module_section = _find_section(rendered_lib1, "Module `Child`")
    assert module_section is not None
    used_by_section = _find_section(module_section, "Used by")
    assert used_by_section is not None

    used_by_refs = list(used_by_section.findall(addnodes.pending_xref))
    assert used_by_refs
    assert len(used_by_refs) == 1
    assert used_by_refs[0].get("reftarget") == top_id
    assert used_by_refs[0].astext() == "Top"
