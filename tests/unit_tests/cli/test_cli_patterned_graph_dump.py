from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("xdsl")

from click.testing import CliRunner

from asdl.cli import cli
from asdl.core import dump_patterned_graph, patterned_graph_to_jsonable
from asdl.core.pipeline import run_patterned_graph_pipeline


def _patterned_yaml() -> str:
    return "\n".join(
        [
            "top: top",
            "modules:",
            "  top:",
            "    instances:",
            "      R1: res",
            "    nets:",
            "      $OUT:",
            "        - R1.P",
            "devices:",
            "  res:",
            "    ports: [P]",
            "    backends:",
            "      sim.ngspice:",
            "        template: \"R{inst} {ports}\"",
        ]
    )


def test_cli_patterned_graph_dump_stdout(tmp_path: Path) -> None:
    input_path = tmp_path / "design.asdl"
    input_path.write_text(_patterned_yaml(), encoding="utf-8")

    graph, diagnostics = run_patterned_graph_pipeline(entry_file=input_path)

    assert diagnostics == []
    assert graph is not None

    expected = dump_patterned_graph(graph)

    runner = CliRunner()
    result = runner.invoke(cli, ["patterned-graph-dump", str(input_path)])

    assert result.exit_code == 0
    assert result.output == expected


def test_cli_patterned_graph_dump_compact_output_file(tmp_path: Path) -> None:
    input_path = tmp_path / "design.asdl"
    input_path.write_text(_patterned_yaml(), encoding="utf-8")
    output_path = tmp_path / "design.json"

    graph, diagnostics = run_patterned_graph_pipeline(entry_file=input_path)

    assert diagnostics == []
    assert graph is not None

    expected = json.dumps(
        patterned_graph_to_jsonable(graph),
        separators=(",", ":"),
        sort_keys=True,
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "patterned-graph-dump",
            str(input_path),
            "--compact",
            "-o",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert result.output == ""
    assert output_path.read_text(encoding="utf-8") == expected


def test_cli_patterned_graph_dump_missing_input(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.asdl"

    runner = CliRunner()
    result = runner.invoke(cli, ["patterned-graph-dump", str(missing_path)])

    assert result.exit_code == 1
    stderr = getattr(result, "stderr", "")
    combined = f"{result.output}{stderr}"
    assert "PARSE-004" in combined
