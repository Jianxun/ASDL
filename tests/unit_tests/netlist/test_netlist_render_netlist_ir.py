import datetime

from asdl.diagnostics import Severity, format_code
from asdl.emit.backend_config import BackendConfig, SystemDeviceTemplate
from asdl.emit.netlist.api import EmitOptions
from asdl.emit.netlist.render import _emit_design, build_emission_name_map
from asdl.emit.netlist_ir import (
    NetlistBackend,
    NetlistConn,
    NetlistDesign,
    NetlistDevice,
    NetlistInstance,
    NetlistModule,
    NetlistNet,
    PatternExpressionEntry,
    PatternOrigin,
)

BACKEND_NAME = "sim.ngspice"


def _backend_config(pattern_rendering: str = "{N}") -> BackendConfig:
    return BackendConfig(
        name=BACKEND_NAME,
        extension=".spice",
        comment_prefix="*",
        templates={
            "__subckt_header__": SystemDeviceTemplate(
                template=".subckt {name} {ports}"
            ),
            "__subckt_footer__": SystemDeviceTemplate(template=".ends {name}"),
            "__subckt_call__": SystemDeviceTemplate(
                template="X{name} {ports} {ref}"
            ),
            "__netlist_header__": SystemDeviceTemplate(
                template="* header {top}"
            ),
            "__netlist_footer__": SystemDeviceTemplate(template=".end"),
        },
        pattern_rendering=pattern_rendering,
    )


def _emit(design: NetlistDesign, config: BackendConfig) -> tuple[str | None, list]:
    options = EmitOptions(
        backend_name=BACKEND_NAME,
        backend_config=config,
        emit_timestamp=datetime.datetime(2026, 1, 1, 12, 0, 0),
    )
    return _emit_design(design, options)


def test_render_netlist_ir_device_params_and_pattern_ports() -> None:
    backend_config = _backend_config(pattern_rendering="[{N}]")

    device = NetlistDevice(
        name="RES",
        file_id="devices.asdl",
        ports=["p", "n"],
        params={"W": "1u"},
        variables={"temp": "25"},
        backends=[
            NetlistBackend(
                name=BACKEND_NAME,
                template="R{name} {ports} {params} {model} {temp}",
                params={"L": "2u"},
                props={"model": "RMOD"},
            )
        ],
    )

    module = NetlistModule(
        name="TOP",
        file_id="top.asdl",
        ports=["BUS1", "OUT"],
        nets=[
            NetlistNet(
                name="BUS1",
                pattern_origin=PatternOrigin(
                    expression_id="expr1",
                    segment_index=0,
                    base_name="BUS",
                    pattern_parts=[1],
                ),
            ),
            NetlistNet(name="OUT"),
        ],
        instances=[
            NetlistInstance(
                name="1",
                ref="RES",
                ref_file_id="devices.asdl",
                params={"W": "3u"},
                conns=[
                    NetlistConn(port="p", net="BUS1"),
                    NetlistConn(port="n", net="OUT"),
                ],
            )
        ],
        pattern_expression_table={
            "expr1": PatternExpressionEntry(expression="BUS<1>", kind="net")
        },
    )

    design = NetlistDesign(
        modules=[module],
        devices=[device],
        top="TOP",
        entry_file_id="top.asdl",
    )

    netlist, diagnostics = _emit(design, backend_config)

    assert diagnostics == []
    assert (
        netlist
        == "\n".join(
            [
                "* header TOP",
                "R1 BUS[1] OUT W=3u L=2u RMOD 25",
                ".end",
            ]
        )
    )


def test_render_netlist_ir_module_reference_uses_file_id() -> None:
    backend_config = _backend_config()

    top = NetlistModule(
        name="TOP",
        file_id="top.asdl",
        ports=[],
        nets=[],
        instances=[
            NetlistInstance(
                name="U1",
                ref="CELL",
                ref_file_id="lib1.asdl",
                conns=[],
            )
        ],
    )
    cell_one = NetlistModule(
        name="CELL",
        file_id="lib1.asdl",
        ports=[],
        nets=[],
        instances=[],
    )
    cell_two = NetlistModule(
        name="CELL",
        file_id="lib2.asdl",
        ports=[],
        nets=[],
        instances=[],
    )

    design = NetlistDesign(
        modules=[top, cell_one, cell_two],
        devices=[],
        top="TOP",
        entry_file_id="top.asdl",
    )

    netlist, diagnostics = _emit(design, backend_config)

    assert len(diagnostics) == 1
    assert diagnostics[0].severity is Severity.WARNING
    assert diagnostics[0].code == format_code("EMIT", 14)
    expected = "\n".join(
        [
            "* header TOP",
            "XU1 CELL",
            ".subckt CELL",
            ".ends CELL",
            ".subckt CELL__2",
            ".ends CELL__2",
            ".end",
        ]
    )
    assert netlist == expected


def test_render_netlist_ir_collision_allocator_skips_preexisting_suffixes() -> None:
    backend_config = _backend_config()

    top = NetlistModule(
        name="TOP",
        file_id="top.asdl",
        ports=[],
        nets=[],
        instances=[
            NetlistInstance(
                name="U1",
                ref="CELL",
                ref_file_id="lib_dup.asdl",
                conns=[],
            )
        ],
    )
    cell_base = NetlistModule(
        name="CELL",
        file_id="lib_base.asdl",
        ports=[],
        nets=[],
        instances=[],
    )
    cell_literal_suffixed = NetlistModule(
        name="CELL__2",
        file_id="lib_literal.asdl",
        ports=[],
        nets=[],
        instances=[],
    )
    cell_duplicate = NetlistModule(
        name="CELL",
        file_id="lib_dup.asdl",
        ports=[],
        nets=[],
        instances=[],
    )

    design = NetlistDesign(
        modules=[top, cell_base, cell_literal_suffixed, cell_duplicate],
        devices=[],
        top="TOP",
        entry_file_id="top.asdl",
    )

    netlist, diagnostics = _emit(design, backend_config)

    assert len(diagnostics) == 1
    assert diagnostics[0].severity is Severity.WARNING
    assert diagnostics[0].code == format_code("EMIT", 14)
    expected = "\n".join(
        [
            "* header TOP",
            "XU1 CELL__3",
            ".subckt CELL",
            ".ends CELL",
            ".subckt CELL__2",
            ".ends CELL__2",
            ".subckt CELL__3",
            ".ends CELL__3",
            ".end",
        ]
    )
    assert netlist == expected


def test_build_emission_name_map_reports_logical_base_and_emitted_names() -> None:
    top = NetlistModule(
        name="TOP",
        file_id="top.asdl",
        ports=[],
        nets=[],
        instances=[],
    )
    literal = NetlistModule(
        name="CELL_behave",
        file_id="literal.asdl",
        ports=[],
        nets=[],
        instances=[],
    )
    decorated = NetlistModule(
        name="CELL@behave",
        file_id="decorated.asdl",
        ports=[],
        nets=[],
        instances=[],
    )
    design = NetlistDesign(
        modules=[top, literal, decorated],
        devices=[],
        top="TOP",
        entry_file_id="top.asdl",
    )

    name_map = build_emission_name_map(design)

    assert [(entry.symbol, entry.base_name, entry.emitted_name) for entry in name_map] == [
        ("TOP", "TOP", "TOP"),
        ("CELL_behave", "CELL_behave", "CELL_behave"),
        ("CELL@behave", "CELL_behave", "CELL_behave__2"),
    ]
    assert [entry.renamed for entry in name_map] == [False, False, True]


def test_render_netlist_ir_realizes_view_decorated_modules() -> None:
    backend_config = _backend_config()

    top = NetlistModule(
        name="TOP",
        file_id="top.asdl",
        ports=[],
        nets=[],
        instances=[
            NetlistInstance(
                name="U0",
                ref="LEAF",
                ref_file_id="lib_default.asdl",
                conns=[],
            ),
            NetlistInstance(
                name="U1",
                ref="LEAF@behave",
                ref_file_id="lib_behave.asdl",
                conns=[],
            ),
            NetlistInstance(
                name="U2",
                ref="LEAF@sim-fast",
                ref_file_id="lib_fast.asdl",
                conns=[],
            ),
        ],
    )
    leaf_default = NetlistModule(
        name="LEAF",
        file_id="lib_default.asdl",
        ports=[],
        nets=[],
        instances=[],
    )
    leaf_behave = NetlistModule(
        name="LEAF@behave",
        file_id="lib_behave.asdl",
        ports=[],
        nets=[],
        instances=[],
    )
    leaf_fast = NetlistModule(
        name="LEAF@sim-fast",
        file_id="lib_fast.asdl",
        ports=[],
        nets=[],
        instances=[],
    )

    design = NetlistDesign(
        modules=[top, leaf_default, leaf_behave, leaf_fast],
        devices=[],
        top="TOP",
        entry_file_id="top.asdl",
    )

    netlist, diagnostics = _emit(design, backend_config)

    assert diagnostics == []
    expected = "\n".join(
        [
            "* header TOP",
            "XU0 LEAF",
            "XU1 LEAF_behave",
            "XU2 LEAF_sim_fast",
            ".subckt LEAF",
            ".ends LEAF",
            ".subckt LEAF_behave",
            ".ends LEAF_behave",
            ".subckt LEAF_sim_fast",
            ".ends LEAF_sim_fast",
            ".end",
        ]
    )
    assert netlist == expected


def test_render_netlist_ir_infers_top_from_entry_file_scope() -> None:
    backend_config = _backend_config()

    entry = NetlistModule(
        name="ENTRY_TOP",
        file_id="entry.asdl",
        ports=[],
        nets=[],
        instances=[],
    )
    imported = NetlistModule(
        name="LIB_TOP",
        file_id="lib.asdl",
        ports=[],
        nets=[],
        instances=[],
    )
    design = NetlistDesign(
        modules=[entry, imported],
        devices=[],
        top=None,
        entry_file_id="entry.asdl",
    )

    netlist, diagnostics = _emit(design, backend_config)

    assert diagnostics == []
    assert netlist is not None
    assert netlist.splitlines()[0] == "* header ENTRY_TOP"


def test_render_netlist_ir_requires_explicit_top_without_unique_entry_module() -> None:
    backend_config = _backend_config()

    imported = NetlistModule(
        name="LIB_TOP",
        file_id="lib.asdl",
        ports=[],
        nets=[],
        instances=[],
    )
    design = NetlistDesign(
        modules=[imported],
        devices=[],
        top=None,
        entry_file_id="entry.asdl",
    )

    netlist, diagnostics = _emit(design, backend_config)

    assert netlist is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "EMIT-001"


def test_render_netlist_ir_warns_on_missing_provenance_and_keeps_file_id_placeholders() -> None:
    backend_config = BackendConfig(
        name=BACKEND_NAME,
        extension=".spice",
        comment_prefix="*",
        templates={
            "__subckt_header__": SystemDeviceTemplate(
                template=".subckt {name} {ports} ; file={file_id}"
            ),
            "__subckt_footer__": SystemDeviceTemplate(template=".ends {name}"),
            "__subckt_call__": SystemDeviceTemplate(
                template="X{name} {ports} {ref} ; file={file_id}"
            ),
            "__netlist_header__": SystemDeviceTemplate(
                template="* header {top} file={file_id}"
            ),
            "__netlist_footer__": SystemDeviceTemplate(template=".end"),
        },
        pattern_rendering="{N}",
    )

    top = NetlistModule(
        name="TOP",
        file_id=None,
        ports=[],
        nets=[],
        instances=[
            NetlistInstance(
                name="U1",
                ref="CELL",
                ref_file_id=None,
                conns=[],
            )
        ],
    )
    cell_missing = NetlistModule(
        name="CELL",
        file_id=None,
        ports=[],
        nets=[],
        instances=[],
    )
    cell_known = NetlistModule(
        name="CELL",
        file_id="lib_known.asdl",
        ports=[],
        nets=[],
        instances=[],
    )
    design = NetlistDesign(
        modules=[top, cell_missing, cell_known],
        devices=[],
        top="TOP",
        entry_file_id=None,
    )

    netlist, diagnostics = _emit(design, backend_config)

    assert netlist == "\n".join(
        [
            "* header TOP file=",
            "XU1 CELL__2 ; file=lib_known.asdl",
            ".subckt CELL ; file=",
            ".ends CELL",
            ".subckt CELL__2 ; file=lib_known.asdl",
            ".ends CELL__2",
            ".end",
        ]
    )

    warning_codes = [diag.code for diag in diagnostics if diag.severity is Severity.WARNING]
    assert warning_codes.count(format_code("EMIT", 15)) >= 3
    assert format_code("EMIT", 14) in warning_codes
    warning_messages = [diag.message for diag in diagnostics if diag.severity is Severity.WARNING]
    assert any("entry_file_id is missing" in message for message in warning_messages)
    assert any("missing file_id provenance" in message for message in warning_messages)
    assert any("name-only fallback is ambiguous" in message for message in warning_messages)
