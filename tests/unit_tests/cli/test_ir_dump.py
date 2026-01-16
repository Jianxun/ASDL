from pathlib import Path

import pytest

pytest.importorskip("xdsl")

from click.testing import CliRunner

from asdl.cli import cli
from asdl.ir import dump_graphir, dump_ifir
from asdl.ir.pipeline import lower_import_graph_to_graphir, run_mvp_pipeline


def _pipeline_yaml() -> str:
    return "\n".join(
        [
            "top: top",
            "modules:",
            "  top:",
            "    instances:",
            "      R1: res a=1 b=2",
            "    nets:",
            "      OUT:",
            "        - R1.P",
            "      VSS:",
            "        - R1.N",
            "devices:",
            "  res:",
            "    ports: [P, N]",
            "    backends:",
            "      ngspice:",
            "        template: \"R{inst} {ports}\"",
        ]
    )


def test_cli_ir_dump_ifir_stdout(tmp_path: Path) -> None:
    input_path = tmp_path / "design.asdl"
    input_path.write_text(_pipeline_yaml(), encoding="utf-8")

    design, diagnostics = run_mvp_pipeline(entry_file=input_path, verify=True)

    assert diagnostics == []
    assert design is not None

    expected = dump_ifir(design)

    runner = CliRunner()
    result = runner.invoke(cli, ["ir-dump", str(input_path)])

    assert result.exit_code == 0
    assert result.output == expected


def test_cli_ir_dump_graphir_output_file(tmp_path: Path) -> None:
    input_path = tmp_path / "design.asdl"
    input_path.write_text(_pipeline_yaml(), encoding="utf-8")
    output_path = tmp_path / "design.graphir"

    program, diagnostics = lower_import_graph_to_graphir(
        entry_file=input_path,
        lib_roots=(),
    )

    assert diagnostics == []
    assert program is not None

    expected = dump_graphir(program)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "ir-dump",
            str(input_path),
            "--ir",
            "graphir",
            "-o",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert result.output == ""
    assert output_path.read_text(encoding="utf-8") == expected
