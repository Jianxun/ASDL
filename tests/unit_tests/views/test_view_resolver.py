"""Unit tests for profile-based view binding resolution."""

import pytest

from asdl.emit.netlist_ir import NetlistDesign, NetlistInstance, NetlistModule
from asdl.views.models import ViewProfile
from asdl.views.resolver import resolve_view_bindings


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
