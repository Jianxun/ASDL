from pathlib import Path

import pytest

pytest.importorskip("xdsl")

from asdl.diagnostics import Severity
from asdl.imports.resolver import resolve_import_graph
from asdl.ir.converters.ast_to_graphir import convert_import_graph
from asdl.ir.graphir import InstanceOp, ModuleOp, ProgramOp
from asdl.ir.pipeline import lower_import_graph_to_graphir


def _write_text(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_convert_import_graph_multi_file_resolution(tmp_path: Path) -> None:
    entry_file = tmp_path / "entry.asdl"
    dep_file = tmp_path / "dep.asdl"
    _write_text(
        entry_file,
        [
            "top: top",
            "imports:",
            "  lib: ./dep.asdl",
            "modules:",
            "  top:",
            "    instances:",
            "      U1: \"lib.child\"",
            "    nets:",
            "      OUT:",
            "        - U1.P",
        ],
    )
    _write_text(
        dep_file,
        [
            "modules:",
            "  child: {}",
        ],
    )

    graph, diagnostics = resolve_import_graph(entry_file)

    assert diagnostics == []
    assert graph is not None

    program, diagnostics = convert_import_graph(graph)

    assert diagnostics == []
    assert isinstance(program, ProgramOp)
    assert program.file_order is not None

    file_order = [item.data for item in program.file_order.data]
    assert file_order == [str(entry_file.resolve()), str(dep_file.resolve())]

    modules = [op for op in program.body.block.ops if isinstance(op, ModuleOp)]
    assert [module.name_attr.data for module in modules] == ["top", "child"]

    top_module = modules[0]
    child_module = modules[1]
    assert top_module.file_id.data == str(entry_file.resolve())
    assert child_module.file_id.data == str(dep_file.resolve())
    assert program.entry is not None
    assert program.entry.value.data == top_module.module_id.value.data

    instance = next(
        op for op in top_module.body.block.ops if isinstance(op, InstanceOp)
    )
    assert instance.module_ref.kind.data == "module"
    assert instance.module_ref.sym_id.value.data == child_module.module_id.value.data


def test_convert_import_graph_unresolved_import_emits_error(
    tmp_path: Path,
) -> None:
    entry_file = tmp_path / "entry.asdl"
    _write_text(
        entry_file,
        [
            "imports:",
            "  lib: missing.asdl",
            "modules:",
            "  top: {}",
        ],
    )

    program, diagnostics = lower_import_graph_to_graphir(entry_file)

    assert program is None
    assert any(
        diag.code == "AST-010" and diag.severity is Severity.ERROR
        for diag in diagnostics
    )
