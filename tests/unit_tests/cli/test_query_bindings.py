from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from asdl.cli import cli

VIEW_FIXTURE_DIR = Path(__file__).parent.parent / "views" / "fixtures"
VIEW_FIXTURE_ASDL = VIEW_FIXTURE_DIR / "view_binding_fixture.asdl"
VIEW_FIXTURE_CONFIG = VIEW_FIXTURE_DIR / "view_binding_fixture.config.yaml"


def _query_bindings_payload(*args: str) -> list[dict[str, object]]:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["query", "bindings", str(VIEW_FIXTURE_ASDL), "--json", *args],
    )
    assert result.exit_code == 0, result.output
    envelope = json.loads(result.output)
    assert envelope["schema_version"] == 1
    assert envelope["kind"] == "query.bindings"
    payload = envelope["payload"]
    assert isinstance(payload, list)
    return payload


def test_query_bindings_requires_view_binding_options() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["query", "bindings", str(VIEW_FIXTURE_ASDL), "--json"],
    )

    assert result.exit_code == 1
    assert "query bindings requires --view-config and --view-profile." in result.output


def test_query_bindings_payload_shape_and_ordering() -> None:
    payload = _query_bindings_payload(
        "--view-config",
        str(VIEW_FIXTURE_CONFIG),
        "--view-profile",
        "config_3",
    )

    assert payload == [
        {
            "path": "tb",
            "instance": "dut",
            "authored_ref": "row",
            "resolved": "row",
            "rule_id": None,
        },
        {
            "path": "tb.dut",
            "instance": "SR_row",
            "authored_ref": "shift_row",
            "resolved": "shift_row",
            "rule_id": None,
        },
        {
            "path": "tb.dut",
            "instance": "Tgate1",
            "authored_ref": "sw_tgate",
            "resolved": "sw_tgate",
            "rule_id": "tgate1_default",
        },
        {
            "path": "tb.dut",
            "instance": "Tgate2",
            "authored_ref": "sw_tgate",
            "resolved": "sw_tgate@behave",
            "rule_id": "tgate2_behave",
        },
        {
            "path": "tb.dut",
            "instance": "Tgate_dbg",
            "authored_ref": "sw_tgate@behave",
            "resolved": "sw_tgate@behave",
            "rule_id": None,
        },
    ]
    assert [tuple((entry["path"], entry["instance"])) for entry in payload] == sorted(
        (entry["path"], entry["instance"]) for entry in payload
    )

