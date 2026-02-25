from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

import asdl.cli.query_runtime as query_runtime_module
from asdl.cli import cli
from asdl.cli.query_runtime import QueryRuntime, QueryStage, build_query_tree_payload
from asdl.emit.netlist_ir import (
    NetlistDesign,
    NetlistDevice,
    NetlistInstance,
    NetlistModule,
)
from asdl.views.instance_index import build_instance_index

VIEW_FIXTURE_DIR = Path(__file__).parent.parent / "views" / "fixtures"
VIEW_FIXTURE_ASDL = VIEW_FIXTURE_DIR / "view_binding_fixture.asdl"
VIEW_FIXTURE_CONFIG = VIEW_FIXTURE_DIR / "view_binding_fixture.config.yaml"


def _query_tree_payload(
    *args: str, expected_kind: str = "query.tree.compact"
) -> dict[str, object]:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["query", "tree", str(VIEW_FIXTURE_ASDL), "--json", *args],
    )
    assert result.exit_code == 0, result.output
    envelope = json.loads(result.output)
    assert envelope["schema_version"] == 1
    assert envelope["kind"] == expected_kind
    payload = envelope["payload"]
    assert isinstance(payload, dict)
    return payload


def _flatten_by_path(node: dict[str, object]) -> dict[str, dict[str, object]]:
    by_path: dict[str, dict[str, object]] = {}

    def _visit(current: dict[str, object]) -> None:
        path = current["path"]
        assert isinstance(path, str)
        by_path[path] = current
        children = current["children"]
        assert isinstance(children, dict)
        for child in children.values():
            assert isinstance(child, dict)
            _visit(child)

    _visit(node)
    return by_path


def test_query_tree_authored_shape_and_nullability() -> None:
    root = _query_tree_payload(
        "--verbose-view",
        "--stage",
        "authored",
        "--view-config",
        str(VIEW_FIXTURE_CONFIG),
        "--view-profile",
        "config_3",
        expected_kind="query.tree",
    )
    by_path = _flatten_by_path(root)

    assert root["path"] == "tb"
    assert root["parent_path"] is None
    assert root["instance"] is None
    assert root["authored_ref"] == "tb"
    assert root["resolved_ref"] is None
    assert root["emitted_name"] is None
    assert root["depth"] == 0
    assert set(root["children"].keys()) == {"dut"}
    assert set(by_path) == {
        "tb",
        "tb.dut",
        "tb.dut.SR_row",
        "tb.dut.SR_row.R1",
        "tb.dut.Tgate1",
        "tb.dut.Tgate1.R3",
        "tb.dut.Tgate2",
        "tb.dut.Tgate2.R3",
        "tb.dut.Tgate_dbg",
        "tb.dut.Tgate_dbg.R4",
    }
    assert by_path["tb.dut"]["parent_path"] == "tb"
    assert by_path["tb.dut"]["instance"] == "dut"
    assert by_path["tb.dut"]["authored_ref"] == "row"
    assert by_path["tb.dut"]["depth"] == 1
    assert by_path["tb.dut.SR_row.R1"]["authored_ref"] == "res"
    assert all(entry["resolved_ref"] is None for entry in by_path.values())
    assert all(entry["emitted_name"] is None for entry in by_path.values())


def test_query_tree_resolved_stage_refs_and_null_emitted_name() -> None:
    payload = _query_tree_payload(
        "--verbose-view",
        "--stage",
        "resolved",
        "--view-config",
        str(VIEW_FIXTURE_CONFIG),
        "--view-profile",
        "config_3",
        expected_kind="query.tree",
    )
    by_path = _flatten_by_path(payload)

    refs_by_path = {path: entry["resolved_ref"] for path, entry in by_path.items()}
    assert refs_by_path == {
        "tb": "tb",
        "tb.dut": "row",
        "tb.dut.SR_row": "shift_row",
        "tb.dut.SR_row.R1": "res",
        "tb.dut.Tgate1": "sw_tgate",
        "tb.dut.Tgate1.R3": "res",
        "tb.dut.Tgate2": "sw_tgate@behave",
        "tb.dut.Tgate2.R3": "res",
        "tb.dut.Tgate_dbg": "sw_tgate@behave",
        "tb.dut.Tgate_dbg.R4": "res",
    }
    assert all(entry["emitted_name"] is None for entry in by_path.values())


def test_query_tree_emitted_stage_uses_baseline_without_view_profile() -> None:
    payload = _query_tree_payload(
        "--verbose-view", "--stage", "emitted", expected_kind="query.tree"
    )
    by_path = _flatten_by_path(payload)

    refs_by_path = {path: entry["resolved_ref"] for path, entry in by_path.items()}
    emitted_names = {path: entry["emitted_name"] for path, entry in by_path.items()}

    assert refs_by_path["tb.dut.Tgate2"] == "sw_tgate"
    assert refs_by_path["tb.dut.Tgate_dbg"] == "sw_tgate@behave"
    assert refs_by_path["tb.dut.Tgate1.R3"] == "res"
    assert refs_by_path["tb.dut.Tgate2.R3"] == "res"
    assert refs_by_path["tb.dut.Tgate_dbg.R4"] == "res"
    assert emitted_names == {
        "tb": "tb",
        "tb.dut": "row",
        "tb.dut.SR_row": "shift_row",
        "tb.dut.SR_row.R1": None,
        "tb.dut.Tgate1": "sw_tgate",
        "tb.dut.Tgate1.R3": None,
        "tb.dut.Tgate2": "sw_tgate",
        "tb.dut.Tgate2.R3": None,
        "tb.dut.Tgate_dbg": "sw_tgate_behave",
        "tb.dut.Tgate_dbg.R4": None,
    }


def test_query_tree_compact_view_payload_shape() -> None:
    payload = _query_tree_payload(expected_kind="query.tree.compact")
    assert payload == {
        "tb:tb": {
            "dut:row": {
                "SR_row:shift_row": {"R1:res": {}},
                "Tgate1:sw_tgate": {"R3:res": {}},
                "Tgate2:sw_tgate": {"R3:res": {}},
                "Tgate_dbg:sw_tgate@behave": {"R4:res": {}},
            }
        }
    }


def test_query_tree_non_json_defaults_to_ascii_tree() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["query", "tree", str(VIEW_FIXTURE_ASDL)],
    )
    assert result.exit_code == 0, result.output
    assert result.output == (
        "tb:tb\n"
        "└── dut:row\n"
        "    ├── SR_row:shift_row\n"
        "    │   └── R1:res\n"
        "    ├── Tgate1:sw_tgate\n"
        "    │   └── R3:res\n"
        "    ├── Tgate2:sw_tgate\n"
        "    │   └── R3:res\n"
        "    └── Tgate_dbg:sw_tgate@behave\n"
        "        └── R4:res"
    )


def test_query_tree_includes_devices_while_views_index_remains_module_only() -> None:
    """Shared traversal policy diverges by consumer include-devices setting."""
    design = NetlistDesign(
        modules=[
            NetlistModule(
                name="tb",
                file_id="file://tb",
                instances=[
                    NetlistInstance(name="xmod", ref="LeafMod", ref_file_id="file://tb"),
                    NetlistInstance(name="xdev_top", ref="nmos", ref_file_id="file://tb"),
                ],
            ),
            NetlistModule(
                name="LeafMod",
                file_id="file://tb",
                instances=[
                    NetlistInstance(name="xdev_leaf", ref="nmos", ref_file_id="file://tb"),
                ],
            ),
        ],
        devices=[NetlistDevice(name="nmos", file_id="file://tb")],
        top="tb",
    )
    runtime = QueryRuntime(
        stage=QueryStage.AUTHORED,
        authored_design=design,
        resolved_design=design,
        stage_design=design,
        resolved_bindings=(),
    )

    tree_payload = build_query_tree_payload(runtime)
    views_index = build_instance_index(design)

    query_children = tree_payload["children"]
    assert isinstance(query_children, dict)
    assert set(query_children.keys()) == {"xmod", "xdev_top"}
    leaf_children = query_children["xmod"]["children"]
    assert isinstance(leaf_children, dict)
    assert set(leaf_children.keys()) == {"xdev_leaf"}

    assert [(entry.path, entry.instance, entry.ref) for entry in views_index.entries] == [
        ("tb", "xmod", "LeafMod")
    ]


def test_query_runtime_has_no_local_top_resolution_helper() -> None:
    """Query runtime must rely on shared hierarchy top-resolution logic."""
    assert not hasattr(query_runtime_module, "_resolve_top_module")
