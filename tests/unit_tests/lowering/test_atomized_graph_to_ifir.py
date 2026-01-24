import pytest

pytest.importorskip("xdsl")

from asdl.core.atomized_graph import (
    AtomizedDeviceDef,
    AtomizedEndpoint,
    AtomizedInstance,
    AtomizedModuleGraph,
    AtomizedNet,
    AtomizedProgramGraph,
)
from asdl.diagnostics import format_code
from asdl.ir.ifir import DesignOp, DeviceOp, InstanceOp, ModuleOp, NetOp
from asdl.lowering import build_ifir_design


def test_build_ifir_design_happy_path() -> None:
    program = AtomizedProgramGraph()
    program.devices["d1"] = AtomizedDeviceDef(
        device_id="d1",
        name="nfet",
        file_id="design.asdl",
        ports=["D", "G", "S"],
        parameters={"W": 1},
    )

    module = AtomizedModuleGraph(
        module_id="m1",
        name="top",
        file_id="design.asdl",
        ports=["VIN", "VOUT"],
    )
    module.instances = {
        "i1": AtomizedInstance(
            inst_id="i1",
            name="M1",
            ref_kind="device",
            ref_id="d1",
            ref_raw="nfet",
            param_values={"m": 2},
        )
    }
    module.nets = {
        "n1": AtomizedNet(net_id="n1", name="VIN", endpoint_ids=["e1"]),
        "n2": AtomizedNet(net_id="n2", name="VOUT", endpoint_ids=["e2"]),
        "n3": AtomizedNet(net_id="n3", name="VSS", endpoint_ids=["e3"]),
    }
    module.endpoints = {
        "e1": AtomizedEndpoint(
            endpoint_id="e1", net_id="n1", inst_id="i1", port="G"
        ),
        "e2": AtomizedEndpoint(
            endpoint_id="e2", net_id="n2", inst_id="i1", port="D"
        ),
        "e3": AtomizedEndpoint(
            endpoint_id="e3", net_id="n3", inst_id="i1", port="S"
        ),
    }
    program.modules["m1"] = module

    design, diagnostics = build_ifir_design(program)

    assert diagnostics == []
    assert isinstance(design, DesignOp)
    assert design.top is not None
    assert design.top.data == "top"
    assert design.entry_file_id is not None
    assert design.entry_file_id.data == "design.asdl"

    ifir_module = next(
        op for op in design.body.block.ops if isinstance(op, ModuleOp)
    )
    assert ifir_module.sym_name.data == "top"
    assert [item.data for item in ifir_module.port_order.data] == ["VIN", "VOUT"]

    nets = [op for op in ifir_module.body.block.ops if isinstance(op, NetOp)]
    assert [net.name_attr.data for net in nets] == ["VIN", "VOUT", "VSS"]

    inst = next(op for op in ifir_module.body.block.ops if isinstance(op, InstanceOp))
    conns = [(conn.port.data, conn.net.data) for conn in inst.conns.data]
    assert conns == [("G", "VIN"), ("D", "VOUT"), ("S", "VSS")]
    assert inst.params is not None
    assert inst.params.data["m"].data == "2"

    ifir_device = next(
        op for op in design.body.block.ops if isinstance(op, DeviceOp)
    )
    assert ifir_device.sym_name.data == "nfet"
    assert [port.data for port in ifir_device.ports.data] == ["D", "G", "S"]
    assert ifir_device.params is not None
    assert ifir_device.params.data["W"].data == "1"


def test_build_ifir_design_missing_endpoint_sets_error() -> None:
    program = AtomizedProgramGraph()
    program.devices["d1"] = AtomizedDeviceDef(
        device_id="d1",
        name="nfet",
        file_id="design.asdl",
        ports=["D", "G", "S"],
    )

    module = AtomizedModuleGraph(
        module_id="m1",
        name="top",
        file_id="design.asdl",
    )
    module.instances = {
        "i1": AtomizedInstance(
            inst_id="i1",
            name="M1",
            ref_kind="device",
            ref_id="d1",
            ref_raw="nfet",
        )
    }
    module.nets = {
        "n1": AtomizedNet(net_id="n1", name="VIN", endpoint_ids=["e-missing"])
    }
    module.endpoints = {}
    program.modules["m1"] = module

    design, diagnostics = build_ifir_design(program)

    assert design is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == format_code("IR", 41)
    assert "missing endpoint" in diagnostics[0].message
