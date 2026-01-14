import io

import pytest

pytest.importorskip("xdsl")

from xdsl.context import Context
from xdsl.dialects import builtin
from xdsl.parser import Parser
from xdsl.printer import Printer
from xdsl.utils.exceptions import VerifyException

from asdl.ir.graphir import ASDL_GRAPHIR, DeviceOp, ModuleOp, ProgramOp


def _print_op(op) -> str:
    stream = io.StringIO()
    printer = Printer(stream=stream)
    printer.print_op(op)
    return stream.getvalue()


def test_program_rejects_non_graphir_ops() -> None:
    module = ModuleOp(module_id="m1", name="top", file_id="a.asdl", region=[])
    program = ProgramOp(region=[module, builtin.ModuleOp([])])

    with pytest.raises(VerifyException):
        program.verify()


def test_program_requires_entry_module_id() -> None:
    module = ModuleOp(module_id="m1", name="top", file_id="a.asdl", region=[])
    program = ProgramOp(region=[module], entry="missing")

    with pytest.raises(VerifyException):
        program.verify()


def test_program_accepts_entry_module_id() -> None:
    module = ModuleOp(module_id="m1", name="top", file_id="a.asdl", region=[])
    program = ProgramOp(region=[module], entry="m1")

    program.verify()


def test_module_port_order_is_unique() -> None:
    module = ModuleOp(
        module_id="m1",
        name="top",
        file_id="a.asdl",
        port_order=["A", "A"],
        region=[],
    )

    with pytest.raises(VerifyException):
        module.verify()


def test_device_ports_must_be_unique() -> None:
    device = DeviceOp(
        device_id="d1",
        name="dev",
        file_id="a.asdl",
        ports=["P", "P"],
        region=[],
    )

    with pytest.raises(VerifyException):
        device.verify()


def test_program_roundtrip_print_parse() -> None:
    module = ModuleOp(
        module_id="m1",
        name="top",
        file_id="a.asdl",
        port_order=["A"],
        region=[],
    )
    device = DeviceOp(
        device_id="d1",
        name="dev",
        file_id="a.asdl",
        ports=["P"],
        region=[],
    )
    program = ProgramOp(region=[module, device], entry="m1")

    text = _print_op(program)
    ctx = Context()
    ctx.load_dialect(builtin.Builtin)
    ctx.load_dialect(ASDL_GRAPHIR)
    parsed_module = Parser(ctx, text).parse_module()
    parsed_program = next(
        op for op in parsed_module.body.block.ops if isinstance(op, ProgramOp)
    )

    assert _print_op(parsed_program) == text
