import pytest

pytest.importorskip("xdsl")

from asdl.ir import convert_graphir_to_ifir
from asdl.ir.graphir import DeviceOp as GraphDeviceOp
from asdl.ir.graphir import EndpointOp as GraphEndpointOp
from asdl.ir.graphir import InstanceOp as GraphInstanceOp
from asdl.ir.graphir import ModuleOp as GraphModuleOp
from asdl.ir.graphir import NetOp as GraphNetOp
from asdl.ir.graphir import ProgramOp as GraphProgramOp
from asdl.ir.ifir import BackendOp as IfirBackendOp
from asdl.ir.ifir import DesignOp as IfirDesignOp
from asdl.ir.ifir import DeviceOp as IfirDeviceOp
from asdl.ir.ifir import InstanceOp as IfirInstanceOp
from asdl.ir.ifir import ModuleOp as IfirModuleOp
from asdl.ir.ifir import NetOp as IfirNetOp


def test_convert_graphir_program_to_ifir() -> None:
    instance = GraphInstanceOp(
        inst_id="i1",
        name="M1",
        module_ref=("device", "d1"),
        module_ref_raw="nfet",
    )
    net_vin = GraphNetOp(
        net_id="n1",
        name="VIN",
        region=[GraphEndpointOp(endpoint_id="e1", inst_id="i1", port_path="G")],
    )
    net_vss = GraphNetOp(
        net_id="n2",
        name="VSS",
        region=[GraphEndpointOp(endpoint_id="e2", inst_id="i1", port_path="S")],
    )
    module = GraphModuleOp(
        module_id="m1",
        name="top",
        file_id="entry.asdl",
        port_order=["VIN"],
        region=[net_vin, net_vss, instance],
    )
    device = GraphDeviceOp(
        device_id="d1",
        name="nfet",
        file_id="entry.asdl",
        ports=["D", "G", "S"],
        region=[IfirBackendOp(name="ngspice", template="M{inst} {D} {G} {S} {model}")],
    )
    program = GraphProgramOp(region=[module, device], entry="m1")

    ifir_design, diagnostics = convert_graphir_to_ifir(program)
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

    inst = next(
        op for op in ifir_module.body.block.ops if isinstance(op, IfirInstanceOp)
    )
    conns = [(conn.port.data, conn.net.data) for conn in inst.conns.data]
    assert conns == [("G", "VIN"), ("S", "VSS")]

    ifir_device = next(
        op for op in ifir_design.body.block.ops if isinstance(op, IfirDeviceOp)
    )
    backend = next(op for op in ifir_device.body.block.ops if isinstance(op, IfirBackendOp))
    assert ifir_device.sym_name.data == "nfet"
    assert backend.template.data == "M{inst} {D} {G} {S} {model}"


def test_convert_graphir_propagates_file_ids() -> None:
    instance = GraphInstanceOp(
        inst_id="i1",
        name="M1",
        module_ref=("device", "d1"),
        module_ref_raw="nfet",
    )
    module = GraphModuleOp(
        module_id="m1",
        name="top",
        file_id="entry.asdl",
        port_order=[],
        region=[
            GraphNetOp(net_id="n1", name="VIN", region=[]),
            instance,
        ],
    )
    device = GraphDeviceOp(
        device_id="d1",
        name="nfet",
        file_id="dep.asdl",
        ports=[],
        region=[],
    )
    program = GraphProgramOp(region=[module, device], entry="m1")

    ifir_design, diagnostics = convert_graphir_to_ifir(program)
    assert diagnostics == []
    assert ifir_design is not None
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
    assert ifir_device.file_id.data == "dep.asdl"

    inst = next(
        op for op in ifir_module.body.block.ops if isinstance(op, IfirInstanceOp)
    )
    assert inst.ref_file_id is not None
    assert inst.ref_file_id.data == "dep.asdl"
