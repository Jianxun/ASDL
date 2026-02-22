"""Unit tests for applying resolved view bindings to NetlistIR designs."""

from asdl.emit.netlist_ir import NetlistDesign, NetlistInstance, NetlistModule
from asdl.views.api import apply_resolved_view_bindings
from asdl.views.resolver import ResolvedViewBindingEntry


def _design_for_apply() -> NetlistDesign:
    return NetlistDesign(
        modules=[
            NetlistModule(
                name="tb",
                file_id="file://tb",
                instances=[
                    NetlistInstance(name="dut", ref="TopCell", ref_file_id="file://tb"),
                ],
            ),
            NetlistModule(
                name="TopCell",
                file_id="file://tb",
                instances=[
                    NetlistInstance(
                        name="Tgate1",
                        ref="swmatrix_Tgate",
                        ref_file_id="file://tb",
                    ),
                    NetlistInstance(
                        name="Tgate2",
                        ref="swmatrix_Tgate",
                        ref_file_id="file://tb",
                    ),
                ],
            ),
            NetlistModule(name="swmatrix_Tgate", file_id="file://tb"),
            NetlistModule(name="swmatrix_Tgate@behave", file_id="file://tb"),
        ],
        top="tb",
    )


def test_apply_resolved_view_bindings_rewrites_emission_refs() -> None:
    """Apply pass rewrites instance refs according to resolved sidecar paths."""
    design = _design_for_apply()
    resolved = (
        ResolvedViewBindingEntry(
            path="tb",
            instance="dut",
            resolved="TopCell",
            rule_id=None,
        ),
        ResolvedViewBindingEntry(
            path="tb.dut",
            instance="Tgate1",
            resolved="swmatrix_Tgate@behave",
            rule_id="global_tgate",
        ),
        ResolvedViewBindingEntry(
            path="tb.dut",
            instance="Tgate2",
            resolved="swmatrix_Tgate",
            rule_id="scoped_tgate2_default",
        ),
    )

    updated = apply_resolved_view_bindings(design, resolved)

    top_cell = [module for module in updated.modules if module.name == "TopCell"][0]
    refs = {instance.name: instance.ref for instance in top_cell.instances}

    assert refs == {
        "Tgate1": "swmatrix_Tgate@behave",
        "Tgate2": "swmatrix_Tgate",
    }
    original_top_cell = [module for module in design.modules if module.name == "TopCell"][0]
    assert {instance.name: instance.ref for instance in original_top_cell.instances} == {
        "Tgate1": "swmatrix_Tgate",
        "Tgate2": "swmatrix_Tgate",
    }

