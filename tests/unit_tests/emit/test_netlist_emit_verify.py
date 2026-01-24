from __future__ import annotations

from asdl.emit.backend_config import BackendConfig, SystemDeviceTemplate
from asdl.emit.netlist.diagnostics import (
    INSTANCE_VARIABLE_OVERRIDE,
    MISSING_BACKEND,
    UNKNOWN_REFERENCE,
    VARIABLE_KEY_COLLISION,
)
from asdl.emit.netlist.verify import _run_netlist_verification
from asdl.emit.netlist_ir import (
    NetlistBackend,
    NetlistConn,
    NetlistDesign,
    NetlistDevice,
    NetlistInstance,
    NetlistModule,
    NetlistNet,
)
from asdl.emit.verify_netlist_ir import INVALID_LITERAL_NAME


def _backend_config(name: str = "sim.ngspice") -> BackendConfig:
    templates = {
        "__subckt_header__": SystemDeviceTemplate(template="{name}"),
        "__subckt_footer__": SystemDeviceTemplate(template=""),
        "__subckt_call__": SystemDeviceTemplate(template="{name} {ports} {ref}"),
        "__netlist_header__": SystemDeviceTemplate(template=""),
        "__netlist_footer__": SystemDeviceTemplate(template=""),
    }
    return BackendConfig(
        name=name,
        extension=".cir",
        comment_prefix="*",
        templates=templates,
    )


def _design(module: NetlistModule, device: NetlistDevice | None = None) -> NetlistDesign:
    devices = [] if device is None else [device]
    return NetlistDesign(modules=[module], devices=devices)


def test_emit_netlist_verify_runs_netlist_ir_checks() -> None:
    module = NetlistModule(
        name="top",
        file_id="design.asdl",
        nets=[NetlistNet(name="N<A>")],
    )

    diagnostics = _run_netlist_verification(
        _design(module),
        backend_name="sim.ngspice",
        backend_config=_backend_config(),
    )

    assert any(diag.code == INVALID_LITERAL_NAME for diag in diagnostics)


def test_emit_netlist_verify_reports_missing_backend() -> None:
    device = NetlistDevice(
        name="cell",
        file_id="design.asdl",
        ports=["P"],
        backends=[],
    )
    module = NetlistModule(
        name="top",
        file_id="design.asdl",
        nets=[NetlistNet(name="N0")],
        instances=[
            NetlistInstance(
                name="U0",
                ref="cell",
                ref_file_id="design.asdl",
                conns=[NetlistConn(port="P", net="N0")],
            )
        ],
    )

    diagnostics = _run_netlist_verification(
        _design(module, device),
        backend_name="sim.ngspice",
        backend_config=_backend_config(),
    )

    assert any(diag.code == MISSING_BACKEND for diag in diagnostics)


def test_emit_netlist_verify_reports_unknown_placeholder() -> None:
    device = NetlistDevice(
        name="cell",
        file_id="design.asdl",
        ports=["P"],
        backends=[NetlistBackend(name="sim.ngspice", template="X {mystery}")],
    )
    module = NetlistModule(
        name="top",
        file_id="design.asdl",
        nets=[NetlistNet(name="N0")],
        instances=[
            NetlistInstance(
                name="U0",
                ref="cell",
                ref_file_id="design.asdl",
                conns=[NetlistConn(port="P", net="N0")],
            )
        ],
    )

    diagnostics = _run_netlist_verification(
        _design(module, device),
        backend_name="sim.ngspice",
        backend_config=_backend_config(),
    )

    assert any(diag.code == UNKNOWN_REFERENCE for diag in diagnostics)


def test_emit_netlist_verify_reports_variable_merge_errors() -> None:
    device = NetlistDevice(
        name="cell",
        file_id="design.asdl",
        ports=["P"],
        params={"R": "1"},
        variables={"R": "2", "V": "3"},
        backends=[NetlistBackend(name="sim.ngspice", template="X {ports} {name}")],
    )
    module = NetlistModule(
        name="top",
        file_id="design.asdl",
        nets=[NetlistNet(name="N0")],
        instances=[
            NetlistInstance(
                name="U0",
                ref="cell",
                ref_file_id="design.asdl",
                params={"V": "9"},
                conns=[NetlistConn(port="P", net="N0")],
            )
        ],
    )

    diagnostics = _run_netlist_verification(
        _design(module, device),
        backend_name="sim.ngspice",
        backend_config=_backend_config(),
    )

    codes = {diag.code for diag in diagnostics}
    assert VARIABLE_KEY_COLLISION in codes
    assert INSTANCE_VARIABLE_OVERRIDE in codes
