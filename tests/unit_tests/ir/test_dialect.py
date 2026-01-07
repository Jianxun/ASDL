import io

import pytest

pytest.importorskip("xdsl")

from xdsl.context import Context
from xdsl.dialects import builtin
from xdsl.dialects.builtin import DictionaryAttr, StringAttr
from xdsl.parser import Parser
from xdsl.printer import Printer
from xdsl.utils.exceptions import VerifyException

from asdl.ir.nfir import (
    ASDL_NFIR,
    BackendOp,
    DesignOp,
    DeviceOp,
    EndpointAttr,
    InstanceOp,
    ModuleOp,
    NetOp,
)


def _print_op(op) -> str:
    stream = io.StringIO()
    printer = Printer(stream=stream)
    printer.print_op(op)
    return stream.getvalue()


def test_module_port_order_requires_net() -> None:
    module = ModuleOp(
        name="m",
        port_order=["a"],
        region=[NetOp(name="b", endpoints=[])],
    )

    with pytest.raises(VerifyException):
        module.verify()


def test_endpoint_requires_instance() -> None:
    module = ModuleOp(
        name="m",
        port_order=["a"],
        region=[
            NetOp(
                name="a",
                endpoints=[EndpointAttr(StringAttr("u1"), StringAttr("P"))],
            )
        ],
    )

    with pytest.raises(VerifyException):
        module.verify()


def test_endpoint_unique_across_nets() -> None:
    module = ModuleOp(
        name="m",
        port_order=["a", "b"],
        region=[
            NetOp(
                name="a",
                endpoints=[EndpointAttr(StringAttr("u1"), StringAttr("P"))],
            ),
            NetOp(
                name="b",
                endpoints=[EndpointAttr(StringAttr("u1"), StringAttr("P"))],
            ),
            InstanceOp(name="u1", ref="leaf"),
        ],
    )

    with pytest.raises(VerifyException):
        module.verify()


def test_device_requires_unique_backends() -> None:
    device = DeviceOp(
        name="d",
        ports=["P"],
        region=[
            BackendOp(name="ngspice", template="T"),
            BackendOp(name="ngspice", template="T2"),
        ],
    )

    with pytest.raises(VerifyException):
        device.verify()


def test_design_roundtrip_print_parse() -> None:
    module = ModuleOp(
        name="top",
        port_order=["VIN"],
        region=[
            NetOp(
                name="VIN",
                endpoints=[EndpointAttr(StringAttr("M1"), StringAttr("G"))],
            ),
            InstanceOp(
                name="M1",
                ref="nfet",
                params=DictionaryAttr({"m": StringAttr("2")}),
            ),
        ],
    )
    device = DeviceOp(
        name="nfet",
        ports=["D", "G", "S"],
        region=[
            BackendOp(name="ngspice", template="M{inst} {D} {G} {S} {model}")
        ],
    )
    design = DesignOp(region=[module, device], top="top")

    text = _print_op(design)
    ctx = Context()
    ctx.load_dialect(builtin.Builtin)
    ctx.load_dialect(ASDL_NFIR)
    parsed_module = Parser(ctx, text).parse_module()
    parsed_design = next(
        op for op in parsed_module.body.block.ops if isinstance(op, DesignOp)
    )
    assert _print_op(parsed_design) == text


def test_design_allows_duplicate_names_across_files() -> None:
    module_a = ModuleOp(
        name="top",
        port_order=[],
        region=[],
        file_id="a.asdl",
    )
    module_b = ModuleOp(
        name="top",
        port_order=[],
        region=[],
        file_id="b.asdl",
    )
    device_a = DeviceOp(
        name="dev",
        ports=[],
        region=[],
        file_id="a.asdl",
    )
    device_b = DeviceOp(
        name="dev",
        ports=[],
        region=[],
        file_id="b.asdl",
    )
    design = DesignOp(region=[module_a, module_b, device_a, device_b])

    design.verify()


def test_design_rejects_duplicate_names_in_same_file() -> None:
    module_a = ModuleOp(
        name="top",
        port_order=[],
        region=[],
        file_id="a.asdl",
    )
    module_b = ModuleOp(
        name="top",
        port_order=[],
        region=[],
        file_id="a.asdl",
    )
    design = DesignOp(region=[module_a, module_b])

    with pytest.raises(VerifyException):
        design.verify()


def test_design_top_requires_entry_file() -> None:
    module_dep = ModuleOp(
        name="top",
        port_order=[],
        region=[],
        file_id="dep.asdl",
    )
    design = DesignOp(region=[module_dep], top="top", entry_file_id="entry.asdl")

    with pytest.raises(VerifyException):
        design.verify()


def test_design_top_resolves_entry_file() -> None:
    module_entry = ModuleOp(
        name="top",
        port_order=[],
        region=[],
        file_id="entry.asdl",
    )
    module_dep = ModuleOp(
        name="top",
        port_order=[],
        region=[],
        file_id="dep.asdl",
    )
    design = DesignOp(
        region=[module_entry, module_dep],
        top="top",
        entry_file_id="entry.asdl",
    )

    design.verify()


def test_design_rejects_missing_top_module() -> None:
    module = ModuleOp(
        name="m",
        port_order=[],
        region=[],
    )
    design = DesignOp(region=[module], top="missing")

    with pytest.raises(VerifyException):
        design.verify()
