import pytest

pytest.importorskip("xdsl")

from xdsl.dialects.builtin import DictionaryAttr, FileLineColLoc, IntAttr, StringAttr

from asdl.diagnostics import Severity, format_code
from asdl.emit.netlist import emit_netlist
from asdl.ir.ifir import (
    BackendOp,
    ConnAttr,
    DesignOp,
    DeviceOp,
    InstanceOp,
    ModuleOp,
    NetOp,
)

BACKEND_NAME = "sim.ngspice"


def _dict_attr(values: dict[str, str]) -> DictionaryAttr:
    return DictionaryAttr({key: StringAttr(value) for key, value in values.items()})


def _loc(line: int, col: int) -> FileLineColLoc:
    return FileLineColLoc(StringAttr("design.asdl"), IntAttr(line), IntAttr(col))


def test_emit_netlist_device_params_and_top_default() -> None:
    backend = BackendOp(
        name=BACKEND_NAME,
        template="{name} {ports} {model} {params}",
        params=_dict_attr({"l": "120n", "m": "2"}),
        props=_dict_attr({"model": "nfet"}),
    )
    device = DeviceOp(
        name="nfet",
        ports=["D", "G", "S"],
        params=_dict_attr({"w": "1u", "l": "100n"}),
        region=[backend],
    )
    instance = InstanceOp(
        name="M1",
        ref="nfet",
        conns=[
            ConnAttr(StringAttr("G"), StringAttr("VIN")),
            ConnAttr(StringAttr("S"), StringAttr("VSS")),
            ConnAttr(StringAttr("D"), StringAttr("VOUT")),
        ],
        params=_dict_attr({"m": "4", "nf": "2"}),
        src=_loc(12, 3),
    )
    module = ModuleOp(
        name="top",
        port_order=["VIN", "VOUT", "VSS"],
        region=[
            NetOp(name="VIN"),
            NetOp(name="VOUT"),
            NetOp(name="VSS"),
            instance,
        ],
    )
    design = DesignOp(region=[module, device], top="top")

    netlist, diagnostics = emit_netlist(design)

    expected = "\n".join(
        [
            "M1 VOUT VIN VSS nfet w=1u l=120n m=4",
            ".end",
        ]
    )
    assert netlist == expected
    assert len(diagnostics) == 1
    assert diagnostics[0].severity is Severity.WARNING
    assert diagnostics[0].code == format_code("EMIT", 2)
    assert diagnostics[0].primary_span is not None
    assert diagnostics[0].primary_span.start.line == 12
    assert diagnostics[0].primary_span.start.col == 3


def test_emit_netlist_top_as_subckt_option() -> None:
    module = ModuleOp(
        name="top",
        port_order=["IN"],
        region=[NetOp(name="IN")],
    )
    design = DesignOp(region=[module])

    netlist, diagnostics = emit_netlist(design, top_as_subckt=True)

    assert diagnostics == []
    assert netlist is not None
    lines = netlist.splitlines()
    assert lines[0] == ".subckt top IN"
    assert lines[1] == ".ends top"
    assert lines[2] == ".end"


def test_emit_netlist_allows_portless_device() -> None:
    backend = BackendOp(
        name=BACKEND_NAME,
        template="X{name} {params}",
    )
    device = DeviceOp(name="probe", ports=[], region=[backend])
    instance = InstanceOp(name="P1", ref="probe", conns=[])
    module = ModuleOp(name="top", port_order=[], region=[instance])
    design = DesignOp(region=[module, device], top="top")

    netlist, diagnostics = emit_netlist(design)

    assert diagnostics == []
    assert netlist == "\n".join(["XP1", ".end"])


def test_emit_netlist_requires_top_when_multiple_modules() -> None:
    module_a = ModuleOp(name="a", port_order=[], region=[])
    module_b = ModuleOp(name="b", port_order=[], region=[])
    design = DesignOp(region=[module_a, module_b])

    netlist, diagnostics = emit_netlist(design)

    assert netlist is None
    assert len(diagnostics) == 1
    assert diagnostics[0].severity is Severity.ERROR
    assert diagnostics[0].code == format_code("EMIT", 1)


def test_emit_netlist_requires_template_placeholders() -> None:
    backend = BackendOp(
        name=BACKEND_NAME,
        template="{ports} {model}",
        props=_dict_attr({"model": "nfet"}),
        src=_loc(7, 1),
    )
    device = DeviceOp(name="nfet", ports=["D"], region=[backend])
    instance = InstanceOp(
        name="M1",
        ref="nfet",
        conns=[ConnAttr(StringAttr("D"), StringAttr("VOUT"))],
    )
    module = ModuleOp(
        name="top",
        port_order=["VOUT"],
        region=[NetOp(name="VOUT"), instance],
    )
    design = DesignOp(region=[module, device], top="top")

    netlist, diagnostics = emit_netlist(design)

    assert netlist is None
    assert len(diagnostics) == 1
    assert diagnostics[0].severity is Severity.ERROR
    assert diagnostics[0].code == format_code("EMIT", 7)
    assert diagnostics[0].primary_span is not None
    assert diagnostics[0].primary_span.start.line == 7
    assert diagnostics[0].primary_span.start.col == 1


def test_emit_netlist_reports_malformed_template() -> None:
    backend = BackendOp(
        name=BACKEND_NAME,
        template="{name} {ports",
    )
    device = DeviceOp(name="nfet", ports=["D"], region=[backend])
    instance = InstanceOp(
        name="M1",
        ref="nfet",
        conns=[ConnAttr(StringAttr("D"), StringAttr("VOUT"))],
    )
    module = ModuleOp(
        name="top",
        port_order=["VOUT"],
        region=[NetOp(name="VOUT"), instance],
    )
    design = DesignOp(region=[module, device], top="top")

    netlist, diagnostics = emit_netlist(design)

    assert netlist is None
    assert len(diagnostics) == 1
    assert diagnostics[0].severity is Severity.ERROR
    assert diagnostics[0].code == format_code("EMIT", 8)


def test_emit_netlist_allows_prop_override() -> None:
    backend = BackendOp(
        name=BACKEND_NAME,
        template="R{name} {ports} {params}",
        props=_dict_attr({"name": "OVERRIDE"}),
    )
    device = DeviceOp(name="res", ports=["P"], region=[backend])
    instance = InstanceOp(
        name="R1",
        ref="res",
        conns=[ConnAttr(StringAttr("P"), StringAttr("VOUT"))],
    )
    module = ModuleOp(
        name="top",
        port_order=["VOUT"],
        region=[NetOp(name="VOUT"), instance],
    )
    design = DesignOp(region=[module, device], top="top")

    netlist, diagnostics = emit_netlist(design)

    assert netlist is not None
    assert "ROVERRIDE VOUT" in netlist
    assert netlist.endswith(".end")
    assert diagnostics == []
