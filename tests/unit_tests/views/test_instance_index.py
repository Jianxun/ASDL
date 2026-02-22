"""Unit tests for deterministic hierarchical view-binding instance indexing."""

from asdl.emit.netlist_ir import NetlistDesign, NetlistInstance, NetlistModule
from asdl.views.instance_index import build_instance_index, match_index_entries
from asdl.views.models import ViewMatch


def test_build_instance_index_is_deterministic_preorder() -> None:
    """Indexer emits deterministic preorder entries with parent-path context."""
    design = NetlistDesign(
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
                ],
            ),
            NetlistModule(name="AuxCell", file_id="file://tb"),
            NetlistModule(name="ShiftReg_row_25", file_id="file://tb"),
            NetlistModule(name="swmatrix_Tgate", file_id="file://tb"),
        ],
        top="tb",
    )

    index = build_instance_index(design)

    assert [(entry.path, entry.instance, entry.module) for entry in index.entries] == [
        ("tb", "dut", "TopCell"),
        ("tb.dut", "SR_row", "ShiftReg_row_25"),
        ("tb.dut", "Tgate<25>", "swmatrix_Tgate"),
        ("tb", "aux", "AuxCell"),
    ]


def test_match_index_entries_omitted_path_matches_root_scope_only() -> None:
    """Rules without path only see top-level instances."""
    design = NetlistDesign(
        modules=[
            NetlistModule(
                name="tb",
                file_id="file://tb",
                instances=[
                    NetlistInstance(name="Xbuf", ref="Buffer", ref_file_id="file://tb"),
                ],
            ),
            NetlistModule(
                name="Buffer",
                file_id="file://tb",
                instances=[
                    NetlistInstance(name="Xbuf", ref="Leaf", ref_file_id="file://tb"),
                ],
            ),
            NetlistModule(name="Leaf", file_id="file://tb"),
        ],
        top="tb",
    )
    index = build_instance_index(design)

    matches = match_index_entries(index, ViewMatch(instance="Xbuf"))

    assert [(entry.path, entry.instance) for entry in matches] == [("tb", "Xbuf")]


def test_match_index_entries_path_scopes_to_subtree() -> None:
    """Path predicate scopes matching to the requested hierarchy subtree."""
    design = NetlistDesign(
        modules=[
            NetlistModule(
                name="tb",
                file_id="file://tb",
                instances=[
                    NetlistInstance(name="dut", ref="TopCell", ref_file_id="file://tb"),
                    NetlistInstance(name="other", ref="TopCell", ref_file_id="file://tb"),
                ],
            ),
            NetlistModule(
                name="TopCell",
                file_id="file://tb",
                instances=[
                    NetlistInstance(
                        name="Tgate<25>",
                        ref="swmatrix_Tgate",
                        ref_file_id="file://tb",
                    ),
                ],
            ),
            NetlistModule(name="swmatrix_Tgate", file_id="file://tb"),
        ],
        top="tb",
    )
    index = build_instance_index(design)

    matches = match_index_entries(
        index, ViewMatch(path="tb.dut", module="swmatrix_Tgate")
    )

    assert [(entry.path, entry.instance, entry.module) for entry in matches] == [
        ("tb.dut", "Tgate<25>", "swmatrix_Tgate")
    ]


def test_build_instance_index_normalizes_decorated_module_symbols() -> None:
    """Entries store logical module predicates using undecorated cell names."""
    design = NetlistDesign(
        modules=[
            NetlistModule(
                name="tb",
                file_id="file://tb",
                instances=[
                    NetlistInstance(
                        name="x_behav",
                        ref="swmatrix_Tgate@behave",
                        ref_file_id="file://tb",
                    ),
                ],
            ),
            NetlistModule(name="swmatrix_Tgate@behave", file_id="file://tb"),
        ],
        top="tb",
    )

    index = build_instance_index(design)

    assert len(index.entries) == 1
    assert index.entries[0].module == "swmatrix_Tgate"
