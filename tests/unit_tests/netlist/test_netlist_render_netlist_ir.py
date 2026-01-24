import datetime
import hashlib

from asdl.emit.backend_config import BackendConfig, SystemDeviceTemplate
from asdl.emit.netlist.api import EmitOptions
from asdl.emit.netlist.render import _emit_design
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


def _hash(file_id: str) -> str:
    return hashlib.sha1(file_id.encode("utf-8")).hexdigest()[:8]


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

    assert diagnostics == []
    expected = "\n".join(
        [
            "* header TOP",
            f"XU1 CELL__{_hash('lib1.asdl')}",
            f".subckt CELL__{_hash('lib1.asdl')}",
            f".ends CELL__{_hash('lib1.asdl')}",
            f".subckt CELL__{_hash('lib2.asdl')}",
            f".ends CELL__{_hash('lib2.asdl')}",
            ".end",
        ]
    )
    assert netlist == expected
