import pytest

pytest.importorskip("xdsl")

from xdsl.dialects.builtin import FileLineColLoc, IntAttr, StringAttr

from asdl.ir import convert_nfir_to_ifir
from asdl.ir.ifir import BackendOp as IfirBackendOp
from asdl.ir.ifir import DesignOp as IfirDesignOp
from asdl.ir.ifir import DeviceOp as IfirDeviceOp
from asdl.ir.ifir import InstanceOp as IfirInstanceOp
from asdl.ir.ifir import ModuleOp as IfirModuleOp
from asdl.ir.ifir import NetOp as IfirNetOp
from asdl.ir.nfir import BackendOp, DesignOp, DeviceOp, EndpointAttr, InstanceOp, ModuleOp, NetOp


def _loc(line: int, col: int) -> FileLineColLoc:
    return FileLineColLoc(StringAttr("design.asdl"), IntAttr(line), IntAttr(col))


def test_convert_nfir_design_to_ifir() -> None:
    module = ModuleOp(
        name="top",
        port_order=["VIN"],
        region=[
            NetOp(
                name="VIN",
                endpoints=[EndpointAttr(StringAttr("M1"), StringAttr("G"))],
            ),
            NetOp(
                name="VSS",
                endpoints=[EndpointAttr(StringAttr("M1"), StringAttr("S"))],
            ),
            InstanceOp(name="M1", ref="nfet"),
        ],
    )
    device = DeviceOp(
        name="nfet",
        ports=["D", "G", "S"],
        region=[BackendOp(name="ngspice", template="M{inst} {D} {G} {S} {model}")],
    )
    design = DesignOp(region=[module, device], top="top")

    ifir_design, diagnostics = convert_nfir_to_ifir(design)
    assert diagnostics == []
    assert isinstance(ifir_design, IfirDesignOp)
    assert ifir_design.top is not None
    assert ifir_design.top.data == "top"

    ifir_module = next(
        op for op in ifir_design.body.block.ops if isinstance(op, IfirModuleOp)
    )
    assert [item.data for item in ifir_module.port_order.data] == ["VIN"]
    nets = [op for op in ifir_module.body.block.ops if isinstance(op, IfirNetOp)]
    assert [net.name_attr.data for net in nets] == ["VIN", "VSS"]

    instance = next(
        op for op in ifir_module.body.block.ops if isinstance(op, IfirInstanceOp)
    )
    conns = [(conn.port.data, conn.net.data) for conn in instance.conns.data]
    assert conns == [("G", "VIN"), ("S", "VSS")]

    ifir_device = next(
        op for op in ifir_design.body.block.ops if isinstance(op, IfirDeviceOp)
    )
    backend = next(op for op in ifir_device.body.block.ops if isinstance(op, IfirBackendOp))
    assert ifir_device.sym_name.data == "nfet"
    assert backend.template.data == "M{inst} {D} {G} {S} {model}"


def test_convert_nfir_rejects_unknown_instance_endpoint() -> None:
    module = ModuleOp(
        name="top",
        port_order=[],
        region=[
            NetOp(
                name="VIN",
                endpoints=[EndpointAttr(StringAttr("M1"), StringAttr("G"))],
                src=_loc(3, 4),
            ),
        ],
        src=_loc(1, 1),
    )
    design = DesignOp(region=[module])

    ifir_design, diagnostics = convert_nfir_to_ifir(design)
    assert ifir_design is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "IR-005"
    assert diagnostics[0].primary_span is not None
    assert diagnostics[0].primary_span.file == "design.asdl"
    assert diagnostics[0].primary_span.start.line == 3
    assert diagnostics[0].primary_span.start.col == 4


def test_convert_nfir_reports_invalid_module_span() -> None:
    bad_op = DeviceOp(
        name="nfet",
        ports=[],
        region=[],
        src=_loc(5, 2),
    )
    module = ModuleOp(
        name="top",
        port_order=[],
        region=[bad_op],
        src=_loc(1, 1),
    )
    design = DesignOp(region=[module])

    ifir_design, diagnostics = convert_nfir_to_ifir(design)
    assert ifir_design is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "IR-003"
    assert diagnostics[0].primary_span is not None
    assert diagnostics[0].primary_span.start.line == 5
    assert diagnostics[0].primary_span.start.col == 2


def test_convert_nfir_reports_invalid_device_span() -> None:
    bad_backend = NetOp(
        name="VOUT",
        endpoints=[],
        src=_loc(8, 7),
    )
    device = DeviceOp(
        name="nfet",
        ports=["D"],
        region=[bad_backend],
        src=_loc(1, 1),
    )
    design = DesignOp(region=[device])

    ifir_design, diagnostics = convert_nfir_to_ifir(design)
    assert ifir_design is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "IR-004"
    assert diagnostics[0].primary_span is not None
    assert diagnostics[0].primary_span.start.line == 8
    assert diagnostics[0].primary_span.start.col == 7
