from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from asdl.cli import cli
from asdl.cli.query_runtime import (
    QueryStage,
    build_query_runtime,
    query_exit_code,
    query_json_envelope,
    render_query_json,
)
from asdl.views.instance_index import build_instance_index

VIEW_FIXTURE_DIR = Path(__file__).parent.parent / "views" / "fixtures"
VIEW_FIXTURE_ASDL = VIEW_FIXTURE_DIR / "view_binding_fixture.asdl"
VIEW_FIXTURE_CONFIG = VIEW_FIXTURE_DIR / "view_binding_fixture.config.yaml"


def _ref_by_path(design_path: str, *, stage_design: object) -> str:
    index = build_instance_index(stage_design)
    by_full_path = {entry.full_path: entry.ref for entry in index.entries}
    return by_full_path[design_path]


def test_query_tree_rejects_view_profile_without_view_config() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["query", "tree", str(VIEW_FIXTURE_ASDL), "--view-profile", "config_3"],
    )

    assert result.exit_code == 1
    assert "--view-profile requires --view-config." in result.output


def test_query_tree_rejects_view_config_without_view_profile() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["query", "tree", str(VIEW_FIXTURE_ASDL), "--view-config", str(VIEW_FIXTURE_CONFIG)],
    )

    assert result.exit_code == 1
    assert "--view-config requires --view-profile." in result.output


def test_query_tree_json_envelope_stable() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["query", "tree", str(VIEW_FIXTURE_ASDL), "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == 1
    assert payload["kind"] == "query.tree"
    assert payload["payload"] == []


def test_runtime_builds_authored_resolved_and_emitted_stages() -> None:
    authored_runtime, authored_diags = build_query_runtime(
        entry_file=VIEW_FIXTURE_ASDL,
        config_path=None,
        lib_roots=(),
        view_config_path=VIEW_FIXTURE_CONFIG,
        view_profile="config_3",
        stage=QueryStage.AUTHORED,
    )
    assert authored_diags == []
    assert authored_runtime is not None
    assert _ref_by_path("tb.dut.Tgate1", stage_design=authored_runtime.stage_design) == "sw_tgate"

    resolved_runtime, resolved_diags = build_query_runtime(
        entry_file=VIEW_FIXTURE_ASDL,
        config_path=None,
        lib_roots=(),
        view_config_path=VIEW_FIXTURE_CONFIG,
        view_profile="config_3",
        stage=QueryStage.RESOLVED,
    )
    assert resolved_diags == []
    assert resolved_runtime is not None
    assert _ref_by_path("tb.dut.Tgate1", stage_design=resolved_runtime.stage_design) == "sw_tgate"
    assert _ref_by_path("tb.dut.Tgate2", stage_design=resolved_runtime.stage_design) == "sw_tgate@behave"

    emitted_runtime, emitted_diags = build_query_runtime(
        entry_file=VIEW_FIXTURE_ASDL,
        config_path=None,
        lib_roots=(),
        view_config_path=VIEW_FIXTURE_CONFIG,
        view_profile="config_3",
        stage=QueryStage.EMITTED,
    )
    assert emitted_diags == []
    assert emitted_runtime is not None
    assert emitted_runtime.stage_design == resolved_runtime.stage_design


def test_query_runtime_envelope_and_exit_helpers() -> None:
    envelope = query_json_envelope(kind="query.tree", payload=[])
    assert envelope == {"schema_version": 1, "kind": "query.tree", "payload": []}
    assert render_query_json(kind="query.tree", payload=[]) == (
        '{"kind":"query.tree","payload":[],"schema_version":1}'
    )
    assert query_exit_code((), missing_anchor=False) == 0
    assert query_exit_code((), missing_anchor=True) == 1
