"""Unit tests for shared deterministic hierarchy traversal."""

from asdl.emit.netlist_ir import NetlistDesign, NetlistDevice, NetlistInstance, NetlistModule

from asdl.core.hierarchy import HierarchyEntry, resolve_top_module, traverse_hierarchy


def test_traverse_hierarchy_excludes_devices_when_requested() -> None:
    """Traversal omits device leaves when `include_devices` is False."""
    design = NetlistDesign(
        modules=[
            NetlistModule(
                name="tb",
                file_id="file://tb",
                instances=[
                    NetlistInstance(name="dut", ref="TopCell", ref_file_id="file://tb"),
                    NetlistInstance(name="r_top", ref="res", ref_file_id="file://tb"),
                ],
            ),
            NetlistModule(
                name="TopCell",
                file_id="file://tb",
                instances=[
                    NetlistInstance(name="r_inner", ref="res", ref_file_id="file://tb"),
                ],
            ),
        ],
        devices=[NetlistDevice(name="res", file_id="file://tb")],
        top="tb",
    )

    entries = traverse_hierarchy(design, include_devices=False)

    assert entries == [
        HierarchyEntry(
            path="tb.dut",
            parent_path="tb",
            instance="dut",
            ref="TopCell",
            ref_file_id="file://tb",
            depth=1,
            is_device=False,
        )
    ]


def test_traverse_hierarchy_includes_devices_in_dfs_pre_order() -> None:
    """Traversal includes device leaves and preserves deterministic DFS preorder."""
    design = NetlistDesign(
        modules=[
            NetlistModule(
                name="tb",
                file_id="file://tb",
                instances=[
                    NetlistInstance(name="dut", ref="TopCell", ref_file_id="file://tb"),
                    NetlistInstance(name="r_top", ref="res", ref_file_id="file://tb"),
                ],
            ),
            NetlistModule(
                name="TopCell",
                file_id="file://tb",
                instances=[
                    NetlistInstance(name="r1", ref="res", ref_file_id="file://tb"),
                    NetlistInstance(name="leaf", ref="Leaf", ref_file_id="file://tb"),
                ],
            ),
            NetlistModule(
                name="Leaf",
                file_id="file://tb",
                instances=[
                    NetlistInstance(name="r2", ref="res", ref_file_id="file://tb"),
                ],
            ),
        ],
        devices=[NetlistDevice(name="res", file_id="file://tb")],
        top="tb",
    )

    entries = traverse_hierarchy(design, include_devices=True)

    assert [entry.path for entry in entries] == [
        "tb.dut",
        "tb.dut.r1",
        "tb.dut.leaf",
        "tb.dut.leaf.r2",
        "tb.r_top",
    ]
    assert [entry.is_device for entry in entries] == [False, True, False, True, True]


def test_traverse_hierarchy_uses_deterministic_module_selection_fallback() -> None:
    """Traversal resolves modules by exact file-id then deterministic name fallback."""
    design = NetlistDesign(
        modules=[
            NetlistModule(
                name="tb",
                file_id="file://tb",
                instances=[
                    NetlistInstance(name="a", ref="Dup", ref_file_id="file://lib_a"),
                    NetlistInstance(name="b", ref="Dup", ref_file_id=None),
                    NetlistInstance(name="c", ref="Only", ref_file_id=None),
                ],
            ),
            NetlistModule(
                name="Dup",
                file_id="file://lib_a",
                instances=[NetlistInstance(name="a_leaf", ref="res", ref_file_id="file://tb")],
            ),
            NetlistModule(
                name="Dup",
                file_id="file://lib_b",
                instances=[NetlistInstance(name="b_leaf", ref="res", ref_file_id="file://tb")],
            ),
            NetlistModule(
                name="Only",
                file_id="file://tb",
                instances=[NetlistInstance(name="c_leaf", ref="res", ref_file_id="file://tb")],
            ),
        ],
        devices=[NetlistDevice(name="res", file_id="file://tb")],
        top="tb",
    )

    entries = traverse_hierarchy(design, include_devices=True)

    assert [entry.path for entry in entries] == [
        "tb.a",
        "tb.a.a_leaf",
        "tb.b",
        "tb.b.b_leaf",
        "tb.c",
        "tb.c.c_leaf",
    ]


def test_traverse_hierarchy_stops_recursion_on_ancestry_cycles() -> None:
    """Traversal emits cycle edge entries but does not recurse through cycles."""
    design = NetlistDesign(
        modules=[
            NetlistModule(
                name="A",
                file_id="file://tb",
                instances=[NetlistInstance(name="to_b", ref="B", ref_file_id="file://tb")],
            ),
            NetlistModule(
                name="B",
                file_id="file://tb",
                instances=[NetlistInstance(name="to_a", ref="A", ref_file_id="file://tb")],
            ),
        ],
        top="A",
    )

    entries = traverse_hierarchy(design, include_devices=False)

    assert [entry.path for entry in entries] == ["A.to_b", "A.to_b.to_a"]


def test_resolve_top_module_permissive_falls_back_to_name_when_entry_misses_top() -> None:
    """Permissive top resolution falls back to name match outside the entry file."""
    top_module = NetlistModule(name="TOP", file_id="lib.asdl", instances=[])
    design = NetlistDesign(
        modules=[NetlistModule(name="ENTRY", file_id="entry.asdl"), top_module],
        devices=[],
        top="TOP",
        entry_file_id="entry.asdl",
    )

    resolved = resolve_top_module(design)

    assert resolved is top_module


def test_resolve_top_module_returns_none_when_entry_scope_is_ambiguous() -> None:
    """Permissive top resolution returns None for missing-top entry ambiguity."""
    design = NetlistDesign(
        modules=[
            NetlistModule(name="A", file_id="entry.asdl", instances=[]),
            NetlistModule(name="B", file_id="entry.asdl", instances=[]),
        ],
        devices=[],
        top=None,
        entry_file_id="entry.asdl",
    )

    assert resolve_top_module(design) is None
