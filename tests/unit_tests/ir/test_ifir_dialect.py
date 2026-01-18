import io

import pytest

pytest.importorskip("xdsl")

from xdsl.context import Context
from xdsl.dialects import builtin
from xdsl.dialects.builtin import StringAttr, SymbolRefAttr
from xdsl.parser import Parser
from xdsl.printer import Printer
from xdsl.utils.exceptions import VerifyException

from asdl.ir.graphir import ASDL_GRAPHIR
from asdl.ir.ifir import (
    ASDL_IFIR,
    BackendOp,
    ConnAttr,
    DesignOp,
    DeviceOp,
    InstanceOp,
    ModuleOp,
    NetOp,
)
from asdl.ir.graphir import GraphPatternOriginAttr
from asdl.ir.patterns import encode_pattern_expression_table, register_pattern_expression


def _print_op(op) -> str:
    stream = io.StringIO()
    printer = Printer(stream=stream)
    printer.print_op(op)
    return stream.getvalue()


def test_module_port_order_requires_net() -> None:
    module = ModuleOp(
        name="m",
        port_order=["a"],
        region=[NetOp(name="b")],
    )

    with pytest.raises(VerifyException):
        module.verify()


def test_instance_requires_known_net() -> None:
    module = ModuleOp(
        name="m",
        port_order=["a"],
        region=[
            NetOp(name="a"),
            InstanceOp(
                name="u1",
                ref="leaf",
                conns=[ConnAttr(StringAttr("P"), StringAttr("missing"))],
            ),
        ],
    )

    with pytest.raises(VerifyException):
        module.verify()


def test_instance_unique_ports() -> None:
    module = ModuleOp(
        name="m",
        port_order=["a", "b"],
        region=[
            NetOp(name="a"),
            NetOp(name="b"),
            InstanceOp(
                name="u1",
                ref="leaf",
                conns=[
                    ConnAttr(StringAttr("P"), StringAttr("a")),
                    ConnAttr(StringAttr("P"), StringAttr("b")),
                ],
            ),
        ],
    )

    with pytest.raises(VerifyException):
        module.verify()


def test_module_rejects_pattern_delimiters_in_net_name() -> None:
    module = ModuleOp(
        name="m",
        port_order=[],
        region=[NetOp(name="BUS<0>")],
    )

    with pytest.raises(VerifyException):
        module.verify()


def test_module_rejects_pattern_delimiters_in_instance_name() -> None:
    module = ModuleOp(
        name="m",
        port_order=["a"],
        region=[
            NetOp(name="a"),
            InstanceOp(
                name="M<0:1>",
                ref="leaf",
                conns=[ConnAttr(StringAttr("P"), StringAttr("a"))],
            ),
        ],
    )

    with pytest.raises(VerifyException):
        module.verify()


def test_module_rejects_pattern_delimiters_in_port_name() -> None:
    module = ModuleOp(
        name="m",
        port_order=["a"],
        region=[
            NetOp(name="a"),
            InstanceOp(
                name="u1",
                ref="leaf",
                conns=[ConnAttr(StringAttr("P;Q"), StringAttr("a"))],
            ),
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
            NetOp(name="VIN"),
            InstanceOp(
                name="M1",
                ref="nfet",
                conns=[ConnAttr(StringAttr("G"), StringAttr("VIN"))],
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
    ctx.load_dialect(ASDL_GRAPHIR)
    ctx.load_dialect(ASDL_IFIR)
    parsed_module = Parser(ctx, text).parse_module()
    parsed_design = next(
        op for op in parsed_module.body.block.ops if isinstance(op, DesignOp)
    )
    assert _print_op(parsed_design) == text


def test_design_roundtrip_pattern_origin() -> None:
    table = {}
    net_expr_id = register_pattern_expression(
        table,
        expression="BUS<2:0>",
        kind="net",
    )
    inst_expr_id = register_pattern_expression(
        table,
        expression="MN_<P|N>",
        kind="inst",
    )
    pattern_table_attr = encode_pattern_expression_table(table)
    module = ModuleOp(
        name="top",
        port_order=["BUS2"],
        pattern_expression_table=pattern_table_attr,
        region=[
            NetOp(name="BUS2", pattern_origin=(net_expr_id, 0, "BUS", [2])),
            InstanceOp(
                name="MN_P",
                ref="nfet",
                conns=[ConnAttr(StringAttr("G"), StringAttr("BUS2"))],
                pattern_origin=(inst_expr_id, 0, "MN_", ["P"]),
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
    ctx.load_dialect(ASDL_GRAPHIR)
    ctx.load_dialect(ASDL_IFIR)
    parsed_module = Parser(ctx, text).parse_module()
    parsed_design = next(
        op for op in parsed_module.body.block.ops if isinstance(op, DesignOp)
    )
    parsed_module_op = next(
        op for op in parsed_design.body.block.ops if isinstance(op, ModuleOp)
    )
    parsed_net = next(
        op for op in parsed_module_op.body.block.ops if isinstance(op, NetOp)
    )
    parsed_instance = next(
        op for op in parsed_module_op.body.block.ops if isinstance(op, InstanceOp)
    )

    assert parsed_net.pattern_origin is not None
    assert isinstance(parsed_net.pattern_origin, GraphPatternOriginAttr)
    assert parsed_net.pattern_origin.expression_id.data == net_expr_id
    assert parsed_net.pattern_origin.base_name.data == "BUS"
    assert [part.data for part in parsed_net.pattern_origin.pattern_parts.data] == [2]
    assert parsed_instance.pattern_origin is not None
    assert isinstance(parsed_instance.pattern_origin, GraphPatternOriginAttr)
    assert parsed_instance.pattern_origin.expression_id.data == inst_expr_id
    assert parsed_instance.pattern_origin.base_name.data == "MN_"
    assert [part.data for part in parsed_instance.pattern_origin.pattern_parts.data] == [
        "P"
    ]
    assert parsed_module_op.pattern_expression_table is not None
    assert parsed_module_op.pattern_expression_table.data == pattern_table_attr.data
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


def test_instance_requires_flat_symbol_ref() -> None:
    instance = InstanceOp(
        name="u1",
        ref=SymbolRefAttr("leaf", ["nested"]),
        conns=[],
    )

    with pytest.raises(VerifyException):
        instance.verify()
