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

    tb_module = [module for module in updated.modules if module.name == "tb"][0]
    dut_instance = [instance for instance in tb_module.instances if instance.name == "dut"][0]
    top_cell = [
        module
        for module in updated.modules
        if module.name == dut_instance.ref and module.file_id == dut_instance.ref_file_id
    ][0]
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


def test_apply_resolved_view_bindings_supports_non_uniform_shared_module_rewrites() -> None:
    """Apply pass specializes shared modules by file id when rewrites diverge by path."""
    design = NetlistDesign(
        modules=[
            NetlistModule(
                name="tb",
                file_id="file://tb",
                instances=[
                    NetlistInstance(name="A1", ref="branch", ref_file_id="file://tb"),
                    NetlistInstance(name="A2", ref="branch", ref_file_id="file://tb"),
                ],
            ),
            NetlistModule(
                name="branch",
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
    resolved = (
        ResolvedViewBindingEntry(path="tb", instance="A1", resolved="branch", rule_id=None),
        ResolvedViewBindingEntry(path="tb.A1", instance="core", resolved="leaf@alt", rule_id="r1"),
        ResolvedViewBindingEntry(path="tb", instance="A2", resolved="branch", rule_id=None),
        ResolvedViewBindingEntry(path="tb.A2", instance="core", resolved="leaf@dbg", rule_id="r2"),
    )

    updated = apply_resolved_view_bindings(design, resolved)

    tb_module = [module for module in updated.modules if module.name == "tb"][0]
    instance_refs = {
        instance.name: (instance.ref, instance.ref_file_id) for instance in tb_module.instances
    }
    a1_ref, a1_ref_file_id = instance_refs["A1"]
    a2_ref, a2_ref_file_id = instance_refs["A2"]

    assert a1_ref == "branch"
    assert a2_ref == "branch"
    assert a1_ref_file_id != a2_ref_file_id
    assert all("__occ_" not in module.name for module in updated.modules)

    a1_module = [
        module
        for module in updated.modules
        if module.name == a1_ref and module.file_id == a1_ref_file_id
    ][0]
    a2_module = [
        module
        for module in updated.modules
        if module.name == a2_ref and module.file_id == a2_ref_file_id
    ][0]
    assert [instance.ref for instance in a1_module.instances] == ["leaf@alt"]
    assert [instance.ref for instance in a2_module.instances] == ["leaf@dbg"]

    base_branch = [
        module
        for module in updated.modules
        if module.name == "branch" and module.file_id == "file://tb"
    ][0]
    assert [instance.ref for instance in base_branch.instances] == ["leaf"]
