from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("xdsl")

from click.testing import CliRunner

from asdl.cli import cli


def _multi_module_yaml() -> str:
    return "\n".join(
        [
            "top: top",
            "modules:",
            "  top:",
            "    instances:",
            "      X1: child",
            "    nets:",
            "      $OUT:",
            "        - X1.IN",
            "  child:",
            "    instances:",
            "      R1: res",
            "    nets:",
            "      $IN:",
            "        - R1.P",
            "devices:",
            "  res:",
            "    ports: [P]",
            "    backends:",
            "      sim.ngspice:",
            "        template: \"R{inst} {ports}\"",
        ]
    )


def _single_module_yaml() -> str:
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


def test_cli_visualizer_dump_list_modules(tmp_path: Path) -> None:
    input_path = tmp_path / "design.asdl"
    input_path.write_text(_multi_module_yaml(), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["visualizer-dump", str(input_path), "--list-modules"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == 0
    module_names = {module["name"] for module in payload["modules"]}
    assert module_names == {"top", "child"}


def test_cli_visualizer_dump_module_output(tmp_path: Path) -> None:
    input_path = tmp_path / "design.asdl"
    input_path.write_text(_single_module_yaml(), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["visualizer-dump", str(input_path), "--module", "top"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == 0
    assert payload["module"]["name"] == "top"
    assert payload["module"]["ports"] == ["OUT"]
    assert len(payload["instances"]) == 1
    assert payload["instances"][0]["ref_kind"] == "device"
    assert payload["instances"][0]["ref_raw"] == "res"
    assert payload["refs"]["devices"][0]["name"] == "res"
