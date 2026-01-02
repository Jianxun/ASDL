import pytest

pytest.importorskip("xdsl")

from asdl.ast import AsdlDocument, DeviceBackendDecl, DeviceDecl, ModuleDecl
from asdl.ir import convert_document
from asdl.ir.nfir import BackendOp, DesignOp, DeviceOp, InstanceOp, ModuleOp, NetOp


def test_convert_document_to_nfir() -> None:
    doc = AsdlDocument(
        top="top",
        modules={
            "top": ModuleDecl(
                instances={"M1": "nfet_3p3 m=2"},
                nets={
                    "$VIN": "M1.G",
                    "VSS": "M1.S",
                },
            )
        },
        devices={
            "nfet_3p3": DeviceDecl(
                ports=["D", "G", "S"],
                params={"w": "1u"},
                backends={
                    "ngspice": DeviceBackendDecl(
                        template="M{inst} {D} {G} {S} {model}",
                        params={"m": 1},
                        model="nfet",
                    )
                },
            )
        },
    )

    design = convert_document(doc)
    assert isinstance(design, DesignOp)
    assert design.top is not None
    assert design.top.data == "top"

    module = next(op for op in design.body.block.ops if isinstance(op, ModuleOp))
    nets = [op for op in module.body.block.ops if isinstance(op, NetOp)]
    instances = [op for op in module.body.block.ops if isinstance(op, InstanceOp)]
    assert [item.data for item in module.port_order.data] == ["VIN"]
    assert {net.name_attr.data for net in nets} == {"VIN", "VSS"}
    assert len(instances) == 1
    instance = instances[0]
    assert instance.ref.data == "nfet_3p3"
    assert instance.params is not None
    assert instance.params.data["m"].data == "2"

    device = next(op for op in design.body.block.ops if isinstance(op, DeviceOp))
    backend = next(op for op in device.body.block.ops if isinstance(op, BackendOp))
    assert device.sym_name.data == "nfet_3p3"
    assert backend.name_attr.data == "ngspice"
    assert backend.template.data == "M{inst} {D} {G} {S} {model}"
    assert backend.params is not None
    assert backend.params.data["m"].data == "1"
    assert backend.props is not None
    assert backend.props.data["model"].data == "nfet"
