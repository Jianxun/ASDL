from pathlib import Path

import pytest

pytest.importorskip("xdsl")

from click.testing import CliRunner

from asdl.cli import cli


def _pipeline_yaml() -> str:
    return "\n".join(
        [
            "top: top",
            "modules:",
            "  top:",
            "    instances:",
            "      U1: leaf",
            "    nets:",
            "      $IN:",
            "        - U1.IN",
            "      $OUT:",
            "        - U1.OUT",
            "  leaf:",
            "    instances:",
            "      R1: res r=2k",
            "    nets:",
            "      $IN:",
            "        - R1.P",
            "      $OUT:",
            "        - R1.N",
            "devices:",
            "  res:",
            "    ports: [P, N]",
            "    params:",
            "      r: 1k",
            "    backends:",
            "      sim.ngspice:",
            "        template: \"{name} {ports} {params}\"",
        ]
    )


def _expected_netlist(top_as_subckt: bool) -> str:
    lines = []
    if top_as_subckt:
        lines.append(".subckt top IN OUT")
    lines.append("XU1 IN OUT leaf")
    if top_as_subckt:
        lines.append(".ends top")
    lines.extend(
        [
            ".subckt leaf IN OUT",
            "R1 IN OUT r=2k",
            ".ends leaf",
            ".end",
        ]
    )
    return "\n".join(lines)


def test_cli_netlist_default_output(tmp_path: Path) -> None:
    input_path = tmp_path / "design.asdl"
    input_path.write_text(_pipeline_yaml(), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["netlist", str(input_path)])

    assert result.exit_code == 0
    output_path = tmp_path / "design.spice"
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == _expected_netlist(False)


def test_cli_netlist_top_as_subckt_with_output_flag(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "design.asdl"
    input_path.write_text(_pipeline_yaml(), encoding="utf-8")
    output_path = tmp_path / "custom.spice"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "netlist",
            str(input_path),
            "--backend",
            "sim.ngspice",
            "--top-as-subckt",
            "-o",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == _expected_netlist(True)


def test_cli_netlist_missing_input_file(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.asdl"

    runner = CliRunner()
    result = runner.invoke(cli, ["netlist", str(missing_path)])

    assert result.exit_code == 1
    stderr = getattr(result, "stderr", "")
    combined = f"{result.output}{stderr}"
    assert "PARSE-004" in combined


def test_cli_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    output = result.output
    assert "Commands:" in output
    assert "netlist" in output
    assert "schema" in output
    assert "Generate a netlist from ASDL." in output
    assert "Generate ASDL schema artifacts." in output
