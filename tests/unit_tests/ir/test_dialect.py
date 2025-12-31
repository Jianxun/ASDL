import pytest

pytest.importorskip("xdsl")

from xdsl.dialects.builtin import DictionaryAttr, StringAttr
from xdsl.ir import Block, Region
from xdsl.utils.exceptions import VerifyException

from asdl.ir.xdsl_dialect import (
    ConnAttr,
    DesignOp,
    ImportOp,
    InstanceOp,
    ModuleOp,
    PortOp,
    SubcktRefOp,
    ViewOp,
)


def test_design_rejects_duplicate_import_alias() -> None:
    design = DesignOp(
        region=Region(
            Block(
                [
                    ImportOp(as_name="lib", from_="a"),
                    ImportOp(as_name="lib", from_="b"),
                ]
            )
        )
    )

    with pytest.raises(VerifyException):
        design.verify()


def test_module_port_order_requires_permutation() -> None:
    module = ModuleOp(
        "m",
        ["a"],
        region=Region(
            Block(
                [
                    PortOp(name="a", dir="in", type_="signal"),
                    PortOp(name="b", dir="out", type_="signal"),
                ]
            )
        ),
    )

    with pytest.raises(VerifyException):
        module.verify()


def test_view_primitive_requires_template() -> None:
    view = ViewOp("nominal", "primitive", region=Region(Block()))

    with pytest.raises(VerifyException):
        view.verify()


def test_view_dummy_name_coupling() -> None:
    wrong_name = ViewOp("nominal", "dummy", region=Region(Block()))
    wrong_kind = ViewOp("dummy", "subckt", region=Region(Block()))

    with pytest.raises(VerifyException):
        wrong_name.verify()
    with pytest.raises(VerifyException):
        wrong_kind.verify()


def test_instance_conn_ports_unique() -> None:
    instance = InstanceOp(
        name="u1",
        ref="m",
        conns=[ConnAttr("a", "n1"), ConnAttr("a", "n2")],
    )

    with pytest.raises(VerifyException):
        instance.verify()


def test_subckt_ref_pin_map_matches_ports() -> None:
    subckt_ref = SubcktRefOp(
        cell="X",
        pin_map=DictionaryAttr({"a": StringAttr("1")}),
    )
    view = ViewOp("nominal", "subckt_ref", region=Region(Block([subckt_ref])))
    module = ModuleOp(
        "m",
        ["a", "b"],
        region=Region(
            Block(
                [
                    PortOp(name="a", dir="in", type_="signal"),
                    PortOp(name="b", dir="out", type_="signal"),
                    view,
                ]
            )
        ),
    )
    design = DesignOp(region=Region(Block([module])))

    with pytest.raises(VerifyException):
        design.verify()


def test_primitive_rejects_instances() -> None:
    instance = InstanceOp(
        name="u1",
        ref="m",
        conns=[ConnAttr("a", "n1")],
    )
    view = ViewOp("nominal", "primitive", region=Region(Block([instance])))

    with pytest.raises(VerifyException):
        view.verify()


def test_subckt_ref_requires_single_op() -> None:
    subckt_ref_a = SubcktRefOp(cell="X")
    subckt_ref_b = SubcktRefOp(cell="Y")
    view = ViewOp(
        "nominal",
        "subckt_ref",
        region=Region(Block([subckt_ref_a, subckt_ref_b])),
    )

    with pytest.raises(VerifyException):
        view.verify()


def test_behav_requires_model() -> None:
    view = ViewOp("nominal", "behav", region=Region(Block()))

    with pytest.raises(VerifyException):
        view.verify()
