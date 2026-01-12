import pytest

pytest.importorskip("xdsl")

from xdsl.dialects.builtin import FileLineColLoc, IntAttr, StringAttr

from asdl.diagnostics import Severity
from asdl.ir import convert_nfir_to_ifir
from asdl.ir.ifir import BackendOp as IfirBackendOp
from asdl.ir.ifir import DesignOp as IfirDesignOp
from asdl.ir.ifir import DeviceOp as IfirDeviceOp
from asdl.ir.ifir import InstanceOp as IfirInstanceOp
from asdl.ir.ifir import ModuleOp as IfirModuleOp
from asdl.ir.ifir import NetOp as IfirNetOp
from asdl.ir.nfir import BackendOp, DesignOp, DeviceOp, EndpointAttr, InstanceOp, ModuleOp, NetOp
from asdl.patterns import PATTERN_EMPTY_ENUM, PATTERN_UNEXPANDED


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


def test_convert_nfir_propagates_file_ids() -> None:
    module = ModuleOp(
        name="top",
        port_order=[],
        region=[
            NetOp(name="VIN", endpoints=[]),
            InstanceOp(name="M1", ref="nfet", ref_file_id="dep.asdl"),
        ],
        file_id="entry.asdl",
    )
    device = DeviceOp(
        name="nfet",
        ports=[],
        region=[],
        file_id="entry.asdl",
    )
    design = DesignOp(region=[module, device], top="top", entry_file_id="entry.asdl")

    ifir_design, diagnostics = convert_nfir_to_ifir(design)
    assert diagnostics == []
    assert isinstance(ifir_design, IfirDesignOp)
    assert ifir_design.entry_file_id is not None
    assert ifir_design.entry_file_id.data == "entry.asdl"

    ifir_module = next(
        op for op in ifir_design.body.block.ops if isinstance(op, IfirModuleOp)
    )
    assert ifir_module.file_id is not None
    assert ifir_module.file_id.data == "entry.asdl"

    ifir_device = next(
        op for op in ifir_design.body.block.ops if isinstance(op, IfirDeviceOp)
    )
    assert ifir_device.file_id is not None
    assert ifir_device.file_id.data == "entry.asdl"

    instance = next(
        op for op in ifir_module.body.block.ops if isinstance(op, IfirInstanceOp)
    )
    assert instance.ref_file_id is not None
    assert instance.ref_file_id.data == "dep.asdl"


def test_convert_nfir_preserves_pattern_tokens() -> None:
    module = ModuleOp(
        name="top",
        port_order=["OUT<P|N>"],
        region=[
            NetOp(
                name="OUT<P|N>",
                endpoints=[EndpointAttr(StringAttr("MN<1|2>"), StringAttr("D"))],
            ),
            NetOp(
                name="BUS[3:0];BUS<4|5>",
                endpoints=[EndpointAttr(StringAttr("MN<1|2>"), StringAttr("S<0|1|2>"))],
            ),
            InstanceOp(name="MN<1|2>", ref="nfet"),
        ],
    )
    design = DesignOp(region=[module])

    ifir_design, diagnostics = convert_nfir_to_ifir(design)
    assert diagnostics == []
    assert isinstance(ifir_design, IfirDesignOp)

    ifir_module = next(
        op for op in ifir_design.body.block.ops if isinstance(op, IfirModuleOp)
    )
    nets = [op for op in ifir_module.body.block.ops if isinstance(op, IfirNetOp)]
    assert {net.name_attr.data for net in nets} == {"OUT<P|N>", "BUS[3:0];BUS<4|5>"}

    instance = next(
        op for op in ifir_module.body.block.ops if isinstance(op, IfirInstanceOp)
    )
    assert instance.name_attr.data == "MN<1|2>"
    conns = [(conn.port.data, conn.net.data) for conn in instance.conns.data]
    assert conns == [
        ("D", "OUT<P|N>"),
        ("S<0|1|2>", "BUS[3:0];BUS<4|5>"),
    ]


def test_convert_nfir_allows_subset_endpoint_instance_tokens() -> None:
    module = ModuleOp(
        name="top",
        port_order=["OUT"],
        region=[
            NetOp(
                name="OUT",
                endpoints=[EndpointAttr(StringAttr("M1"), StringAttr("D"))],
            ),
            InstanceOp(name="M<1|2>", ref="nfet"),
        ],
    )
    design = DesignOp(region=[module])

    ifir_design, diagnostics = convert_nfir_to_ifir(design)
    assert diagnostics == []
    assert isinstance(ifir_design, IfirDesignOp)

    ifir_module = next(
        op for op in ifir_design.body.block.ops if isinstance(op, IfirModuleOp)
    )
    instance = next(
        op for op in ifir_module.body.block.ops if isinstance(op, IfirInstanceOp)
    )
    conns = [(conn.port.data, conn.net.data) for conn in instance.conns.data]
    assert conns == [("D", "OUT")]


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


def test_convert_nfir_allows_scalar_net_broadcast() -> None:
    module = ModuleOp(
        name="top",
        port_order=[],
        region=[
            NetOp(
                name="VIN",
                endpoints=[EndpointAttr(StringAttr("M<1|2>"), StringAttr("D<0|1>"))],
            ),
            InstanceOp(name="M<1|2>", ref="nfet"),
        ],
    )
    design = DesignOp(region=[module])

    ifir_design, diagnostics = convert_nfir_to_ifir(design)
    assert diagnostics == []
    assert isinstance(ifir_design, IfirDesignOp)


def test_convert_nfir_allows_spliced_instance_pattern() -> None:
    module = ModuleOp(
        name="top",
        port_order=[],
        region=[
            NetOp(
                name="VIN",
                endpoints=[EndpointAttr(StringAttr("M<1|2>;M<3|4>"), StringAttr("D"))],
            ),
            InstanceOp(name="M<1|2>;M<3|4>", ref="nfet"),
        ],
    )
    design = DesignOp(region=[module])

    ifir_design, diagnostics = convert_nfir_to_ifir(design)
    assert diagnostics == []
    assert isinstance(ifir_design, IfirDesignOp)


def test_convert_nfir_reports_pattern_binding_mismatch() -> None:
    module = ModuleOp(
        name="top",
        port_order=[],
        region=[
            NetOp(
                name="BUS<0|1>",
                endpoints=[EndpointAttr(StringAttr("M<1|2|3>"), StringAttr("D"))],
            ),
            InstanceOp(name="M<1|2|3>", ref="nfet"),
        ],
    )
    design = DesignOp(region=[module])

    ifir_design, diagnostics = convert_nfir_to_ifir(design)
    assert ifir_design is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "IR-006"
    assert diagnostics[0].severity is Severity.ERROR


def test_convert_nfir_reports_malformed_endpoint_pattern() -> None:
    module = ModuleOp(
        name="top",
        port_order=[],
        region=[
            NetOp(
                name="VIN",
                endpoints=[EndpointAttr(StringAttr("M1"), StringAttr("D<|>"))],
            ),
            InstanceOp(name="M1", ref="nfet"),
        ],
    )
    design = DesignOp(region=[module])

    ifir_design, diagnostics = convert_nfir_to_ifir(design)
    assert ifir_design is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == PATTERN_EMPTY_ENUM
    assert diagnostics[0].severity is Severity.ERROR


def test_convert_nfir_reports_comma_enum_delimiter() -> None:
    module = ModuleOp(
        name="top",
        port_order=[],
        region=[
            NetOp(
                name="VIN<P,N>",
                endpoints=[EndpointAttr(StringAttr("M1"), StringAttr("D"))],
            ),
            InstanceOp(name="M1", ref="nfet"),
        ],
    )
    design = DesignOp(region=[module])

    ifir_design, diagnostics = convert_nfir_to_ifir(design)
    assert ifir_design is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == PATTERN_UNEXPANDED
    assert diagnostics[0].severity is Severity.ERROR
