import pytest

pytest.importorskip("xdsl")

from asdl.ast import (
    AsdlDocument,
    InstanceDecl,
    ModuleDecl,
    PortDecl,
    SubcktViewDecl,
)
from asdl.ir import convert_document
from asdl.ir.xdsl_dialect import InstanceOp, ModuleOp, ViewOp


def test_converter_normalizes_nominal() -> None:
    doc = AsdlDocument(
        modules={
            "m": ModuleDecl(
                ports={"a": PortDecl(dir="in")},
                port_order=["a"],
                views={
                    "nom": SubcktViewDecl(
                        kind="subckt",
                        instances={
                            "u1": InstanceDecl(
                                model="leaf",
                                view="nom",
                                conns={"a": "n1"},
                            )
                        },
                    )
                },
            )
        }
    )

    design = convert_document(doc)
    module = next(op for op in design.body.block.ops if isinstance(op, ModuleOp))
    view = next(op for op in module.body.block.ops if isinstance(op, ViewOp))
    instance = next(op for op in view.body.block.ops if isinstance(op, InstanceOp))

    assert view.sym_name.data == "nominal"
    assert instance.view is not None
    assert instance.view.data == "nominal"
