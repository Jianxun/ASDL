from __future__ import annotations

import json
from pathlib import Path

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


def test_cli_depgraph_dump_schema(tmp_path: Path) -> None:
    input_path = tmp_path / "design.asdl"
    input_path.write_text(_multi_module_yaml(), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["depgraph-dump", str(input_path)])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == 1
    for key in ("files", "modules", "instances", "edges", "unresolved"):
        assert key in payload

    assert payload["modules"]
    for module in payload["modules"]:
        assert module.get("module_id")
        assert module.get("name")
        assert module.get("file_id")

    assert payload["instances"]
    for instance in payload["instances"]:
        assert instance.get("module_id")
        assert instance.get("instance_id")

    for edge in payload["edges"]:
        assert edge.get("from_module_id")
        assert edge.get("to_module_id")
        assert edge.get("instance_id")

    for unresolved in payload["unresolved"]:
        assert unresolved.get("module_id")
        assert unresolved.get("instance_id")
