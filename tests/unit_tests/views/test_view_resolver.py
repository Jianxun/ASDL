"""Unit tests for profile-based view binding resolution."""

from pathlib import Path

import pytest
import yaml

from asdl.emit.netlist_ir import NetlistDesign, NetlistInstance, NetlistModule
from asdl.lowering import run_netlist_ir_pipeline
from asdl.views.config import load_view_config
from asdl.views.models import ViewProfile
from asdl.views.resolver import resolve_view_bindings

FIXTURE_DIR = Path(__file__).parent / "fixtures"
VIEW_FIXTURE_ASDL = FIXTURE_DIR / "view_binding_fixture.asdl"
VIEW_FIXTURE_CONFIG = FIXTURE_DIR / "view_binding_fixture.config.yaml"
VIEW_FIXTURE_BINDING = FIXTURE_DIR / "view_binding_fixture.config_3.binding.yaml"


def _fixture_design() -> NetlistDesign:
    design, diagnostics = run_netlist_ir_pipeline(entry_file=VIEW_FIXTURE_ASDL, verify=True)
    assert diagnostics == []
    assert design is not None
    return design


def _fixture_profile(name: str) -> ViewProfile:
    config, diagnostics = load_view_config(VIEW_FIXTURE_CONFIG)
    assert diagnostics == []
    assert config is not None
    return config.profiles[name]


def _design_for_resolution() -> NetlistDesign:
    return NetlistDesign(
        modules=[
            NetlistModule(
                name="tb",
                file_id="file://tb",
                instances=[
                    NetlistInstance(name="dut", ref="TopCell", ref_file_id="file://tb"),
                    NetlistInstance(name="aux", ref="AuxCell", ref_file_id="file://tb"),
                ],
            ),
            NetlistModule(
                name="TopCell",
                file_id="file://tb",
                instances=[
                    NetlistInstance(
                        name="SR_row",
                        ref="ShiftReg_row_25",
                        ref_file_id="file://tb",
                    ),
                    NetlistInstance(
                        name="Tgate<25>",
                        ref="swmatrix_Tgate",
                        ref_file_id="file://tb",
                    ),
                    NetlistInstance(
                        name="Xauth",
                        ref="AuxCell@behave",
                        ref_file_id="file://tb",
                    ),
                ],
            ),
            NetlistModule(name="AuxCell", file_id="file://tb"),
            NetlistModule(name="AuxCell@behave", file_id="file://tb"),
            NetlistModule(name="ShiftReg_row_25", file_id="file://tb"),
            NetlistModule(name="ShiftReg_row_25@behave", file_id="file://tb"),
            NetlistModule(name="swmatrix_Tgate", file_id="file://tb"),
            NetlistModule(name="swmatrix_Tgate@behave", file_id="file://tb"),
            NetlistModule(name="swmatrix_Tgate@debug", file_id="file://tb"),
        ],
        top="tb",
    )


def test_resolve_view_bindings_applies_baseline_and_later_rule_precedence() -> None:
    """Resolver applies baseline view order then later matching rules override."""
    design = _design_for_resolution()
    profile = ViewProfile.model_validate(
        {
            "view_order": ["behave", "default"],
            "rules": [
                {
                    "id": "global_tgate",
                    "match": {"module": "swmatrix_Tgate"},
                    "bind": "swmatrix_Tgate@behave",
                },
                {
                    "id": "specific_tgate",
                    "match": {"path": "tb.dut", "instance": "Tgate<25>"},
                    "bind": "swmatrix_Tgate@debug",
                },
            ],
        }
    )

    result = resolve_view_bindings(design, profile)

    assert [(entry.path, entry.instance, entry.resolved, entry.rule_id) for entry in result] == [
        ("tb", "dut", "TopCell", None),
        ("tb.dut", "SR_row", "ShiftReg_row_25@behave", None),
        ("tb.dut", "Tgate<25>", "swmatrix_Tgate@debug", "specific_tgate"),
        ("tb.dut", "Xauth", "AuxCell@behave", None),
        ("tb", "aux", "AuxCell@behave", None),
    ]


def test_resolve_view_bindings_uses_assigned_default_rule_ids_in_sidecar() -> None:
    """Resolver sidecar records deterministic default rule IDs for matches."""
    design = _design_for_resolution()
    profile = ViewProfile.model_validate(
        {
            "view_order": ["default"],
            "rules": [
                {
                    "match": {"path": "tb.dut", "module": "swmatrix_Tgate"},
                    "bind": "swmatrix_Tgate@behave",
                }
            ],
        }
    )

    result = resolve_view_bindings(design, profile)

    tgate_entry = [entry for entry in result if entry.instance == "Tgate<25>"]
    assert len(tgate_entry) == 1
    assert tgate_entry[0].resolved == "swmatrix_Tgate@behave"
    assert tgate_entry[0].rule_id == "rule1"


def test_resolve_view_bindings_raises_when_baseline_candidate_missing() -> None:
    """Undecorated refs fail resolution when no view_order candidate exists."""
    design = NetlistDesign(
        modules=[
            NetlistModule(
                name="tb",
                file_id="file://tb",
                instances=[
                    NetlistInstance(name="x1", ref="OnlyDefault", ref_file_id="file://tb"),
                ],
            ),
            NetlistModule(name="OnlyDefault", file_id="file://tb"),
        ],
        top="tb",
    )
    profile = ViewProfile.model_validate({"view_order": ["behave"]})

    with pytest.raises(ValueError, match="Unable to resolve baseline view"):
        resolve_view_bindings(design, profile)


def test_resolve_view_bindings_raises_for_missing_rule_bind_symbol() -> None:
    """Rules must bind to symbols that exist in loaded design modules."""
    design = _design_for_resolution()
    profile = ViewProfile.model_validate(
        {
            "view_order": ["default"],
            "rules": [
                {
                    "id": "bad_bind",
                    "match": {"path": "tb.dut", "instance": "Tgate<25>"},
                    "bind": "swmatrix_Tgate@nonexistent",
                }
            ],
        }
    )

    with pytest.raises(ValueError, match="Resolved symbol 'swmatrix_Tgate@nonexistent'"):
        resolve_view_bindings(design, profile)


def test_resolve_view_bindings_raises_for_unknown_match_path() -> None:
    """Rules must fail when `match.path` does not resolve to a hierarchy node."""
    design = _design_for_resolution()
    profile = ViewProfile.model_validate(
        {
            "view_order": ["default"],
            "rules": [
                {
                    "id": "bad_path",
                    "match": {"path": "tb.missing", "instance": "x"},
                    "bind": "TopCell",
                }
            ],
        }
    )

    with pytest.raises(ValueError, match="match.path 'tb.missing'"):
        resolve_view_bindings(design, profile)


def test_resolve_view_bindings_fixture_baseline_selection() -> None:
    """Fixture profile config_1 selects behave variants via baseline view order."""
    resolved = resolve_view_bindings(_fixture_design(), _fixture_profile("config_1"))

    assert [(entry.path, entry.instance, entry.resolved) for entry in resolved] == [
        ("tb", "dut", "row"),
        ("tb.dut", "SR_row", "shift_row@behave"),
        ("tb.dut", "Tgate1", "sw_tgate@behave"),
        ("tb.dut", "Tgate2", "sw_tgate@behave"),
        ("tb.dut", "Tgate_dbg", "sw_tgate@behave"),
    ]


def test_resolve_view_bindings_fixture_scoped_path_override() -> None:
    """Fixture profile config_2 rewrites only SR_row under tb.dut."""
    resolved = resolve_view_bindings(_fixture_design(), _fixture_profile("config_2"))

    assert [(entry.path, entry.instance, entry.resolved) for entry in resolved] == [
        ("tb", "dut", "row"),
        ("tb.dut", "SR_row", "shift_row@behave"),
        ("tb.dut", "Tgate1", "sw_tgate"),
        ("tb.dut", "Tgate2", "sw_tgate"),
        ("tb.dut", "Tgate_dbg", "sw_tgate@behave"),
    ]


def test_resolve_view_bindings_fixture_later_rule_precedence_matches_fixture() -> None:
    """Fixture profile config_3 proves later rule precedence via checked-in sidecar."""
    resolved = resolve_view_bindings(_fixture_design(), _fixture_profile("config_3"))
    expected = yaml.safe_load(VIEW_FIXTURE_BINDING.read_text(encoding="utf-8"))

    assert [(entry.path, entry.instance, entry.resolved) for entry in resolved] == [
        (record["path"], record["instance"], record["resolved"]) for record in expected
    ]


def test_resolve_view_bindings_keeps_deterministic_order_for_divergent_paths() -> None:
    """Resolver preserves stable DFS order for path-scoped divergent rewrites."""
    design = NetlistDesign(
        modules=[
            NetlistModule(
                name="tb",
                file_id="file://tb",
                instances=[
                    NetlistInstance(name="L", ref="left", ref_file_id="file://tb"),
                    NetlistInstance(name="R", ref="right", ref_file_id="file://tb"),
                ],
            ),
            NetlistModule(
                name="left",
                file_id="file://tb",
                instances=[
                    NetlistInstance(name="U", ref="stage", ref_file_id="file://tb"),
                ],
            ),
            NetlistModule(
                name="right",
                file_id="file://tb",
                instances=[
                    NetlistInstance(name="U", ref="stage", ref_file_id="file://tb"),
                ],
            ),
            NetlistModule(
                name="stage",
                file_id="file://tb",
                instances=[
                    NetlistInstance(name="core", ref="leaf", ref_file_id="file://tb"),
                ],
            ),
            NetlistModule(name="leaf", file_id="file://tb"),
            NetlistModule(name="leaf@alt", file_id="file://tb"),
            NetlistModule(name="leaf@dbg", file_id="file://tb"),
        ],
        top="tb",
    )
    profile = ViewProfile.model_validate(
        {
            "view_order": ["default"],
            "rules": [
                {
                    "id": "left_alt",
                    "match": {"path": "tb.L.U", "instance": "core"},
                    "bind": "leaf@alt",
                },
                {
                    "id": "right_dbg",
                    "match": {"path": "tb.R.U", "instance": "core"},
                    "bind": "leaf@dbg",
                },
            ],
        }
    )

    result = resolve_view_bindings(design, profile)

    assert [(entry.path, entry.instance, entry.resolved, entry.rule_id) for entry in result] == [
        ("tb", "L", "left", None),
        ("tb.L", "U", "stage", None),
        ("tb.L.U", "core", "leaf@alt", "left_alt"),
        ("tb", "R", "right", None),
        ("tb.R", "U", "stage", None),
        ("tb.R.U", "core", "leaf@dbg", "right_dbg"),
    ]
