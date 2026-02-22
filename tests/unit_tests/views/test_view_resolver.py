"""Unit tests for profile-based view binding resolution."""

from pathlib import Path

import pytest
import yaml

from asdl.emit.netlist_ir import NetlistDesign, NetlistInstance, NetlistModule
from asdl.lowering import run_netlist_ir_pipeline
from asdl.views.config import load_view_config
from asdl.views.models import ViewProfile
from asdl.views.resolver import resolve_view_bindings

SWMATRIX_ASDL = Path("examples/libs/tb/tb_swmatrix/tb_swmatrix_row.asdl")
SWMATRIX_CONFIG = Path("examples/libs/tb/tb_swmatrix/tb_swmatrix_row.config.yaml")
SWMATRIX_BINDING = Path("examples/libs/tb/tb_swmatrix/tb_swmatrix_row.binding.yaml")


def _swmatrix_design() -> NetlistDesign:
    design, diagnostics = run_netlist_ir_pipeline(entry_file=SWMATRIX_ASDL, verify=True)
    assert diagnostics == []
    assert design is not None
    return design


def _swmatrix_profile(name: str) -> ViewProfile:
    config, diagnostics = load_view_config(SWMATRIX_CONFIG)
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


def test_resolve_view_bindings_swmatrix_global_module_substitution() -> None:
    """Global module match rewrites all root-scoped swmatrix_Tgate instances."""
    resolved = resolve_view_bindings(_swmatrix_design(), _swmatrix_profile("config_1"))

    assert [(entry.path, entry.instance, entry.resolved) for entry in resolved] == [
        ("tb", "dut", "swmatrix_row_25_w_clkbuf"),
        ("tb.dut", "SR_row", "ShiftReg_row_25"),
        ("tb.dut", "Tgate2", "swmatrix_Tgate@behave"),
        ("tb.dut", "Tgate1", "swmatrix_Tgate@behave"),
        ("tb.dut", "Tgate_dbg", "swmatrix_Tgate@behave"),
    ]


def test_resolve_view_bindings_swmatrix_scoped_path_override() -> None:
    """Scoped path+instance override rewrites only SR_row under tb.dut."""
    resolved = resolve_view_bindings(_swmatrix_design(), _swmatrix_profile("config_2"))

    assert [(entry.path, entry.instance, entry.resolved) for entry in resolved] == [
        ("tb", "dut", "swmatrix_row_25_w_clkbuf"),
        ("tb.dut", "SR_row", "ShiftReg_row_25@behave"),
        ("tb.dut", "Tgate2", "swmatrix_Tgate"),
        ("tb.dut", "Tgate1", "swmatrix_Tgate"),
        ("tb.dut", "Tgate_dbg", "swmatrix_Tgate@behave"),
    ]


def test_resolve_view_bindings_swmatrix_later_rule_precedence_matches_fixture() -> None:
    """Later rules override earlier ones and match checked-in binding expectations."""
    resolved = resolve_view_bindings(_swmatrix_design(), _swmatrix_profile("config_3"))
    expected = yaml.safe_load(SWMATRIX_BINDING.read_text(encoding="utf-8"))

    assert [(entry.path, entry.instance, entry.resolved) for entry in resolved] == [
        (record["path"], record["instance"], record["resolved"]) for record in expected
    ]
