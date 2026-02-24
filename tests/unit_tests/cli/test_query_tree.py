from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from asdl.cli import cli

VIEW_FIXTURE_DIR = Path(__file__).parent.parent / "views" / "fixtures"
VIEW_FIXTURE_ASDL = VIEW_FIXTURE_DIR / "view_binding_fixture.asdl"
VIEW_FIXTURE_CONFIG = VIEW_FIXTURE_DIR / "view_binding_fixture.config.yaml"


def _query_tree_payload(*args: str) -> list[dict[str, object]]:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["query", "tree", str(VIEW_FIXTURE_ASDL), "--json", *args],
    )
    assert result.exit_code == 0, result.output
    envelope = json.loads(result.output)
    assert envelope["schema_version"] == 1
    assert envelope["kind"] == "query.tree"
    payload = envelope["payload"]
    assert isinstance(payload, list)
    return payload


def test_query_tree_authored_shape_order_and_nullability() -> None:
    payload = _query_tree_payload(
        "--stage",
        "authored",
        "--view-config",
        str(VIEW_FIXTURE_CONFIG),
        "--view-profile",
        "config_3",
    )

    assert [entry["path"] for entry in payload] == [
        "tb",
        "tb.dut",
        "tb.dut.SR_row",
        "tb.dut.Tgate1",
        "tb.dut.Tgate2",
        "tb.dut.Tgate_dbg",
    ]
    assert payload[0] == {
        "path": "tb",
        "parent_path": None,
        "instance": None,
        "authored_ref": "tb",
        "resolved_ref": None,
        "emitted_name": None,
        "depth": 0,
    }
    assert payload[1]["parent_path"] == "tb"
    assert payload[1]["instance"] == "dut"
    assert payload[1]["authored_ref"] == "row"
    assert payload[1]["depth"] == 1
    assert all(entry["resolved_ref"] is None for entry in payload)
    assert all(entry["emitted_name"] is None for entry in payload)


def test_query_tree_resolved_stage_refs_and_null_emitted_name() -> None:
    payload = _query_tree_payload(
        "--stage",
        "resolved",
        "--view-config",
        str(VIEW_FIXTURE_CONFIG),
        "--view-profile",
        "config_3",
    )

    refs_by_path = {entry["path"]: entry["resolved_ref"] for entry in payload}
    assert refs_by_path == {
        "tb": "tb",
        "tb.dut": "row",
        "tb.dut.SR_row": "shift_row",
        "tb.dut.Tgate1": "sw_tgate",
        "tb.dut.Tgate2": "sw_tgate@behave",
        "tb.dut.Tgate_dbg": "sw_tgate@behave",
    }
    assert all(entry["emitted_name"] is None for entry in payload)


def test_query_tree_emitted_stage_uses_baseline_without_view_profile() -> None:
    payload = _query_tree_payload("--stage", "emitted")

    refs_by_path = {entry["path"]: entry["resolved_ref"] for entry in payload}
    emitted_names = {entry["path"]: entry["emitted_name"] for entry in payload}

    assert refs_by_path["tb.dut.Tgate2"] == "sw_tgate"
    assert refs_by_path["tb.dut.Tgate_dbg"] == "sw_tgate@behave"
    assert emitted_names == {
        "tb": "tb",
        "tb.dut": "row",
        "tb.dut.SR_row": "shift_row",
        "tb.dut.Tgate1": "sw_tgate",
        "tb.dut.Tgate2": "sw_tgate",
        "tb.dut.Tgate_dbg": "sw_tgate_behave",
    }
