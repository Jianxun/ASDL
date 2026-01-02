from __future__ import annotations

from typing import Dict, List

from xdsl.dialects.builtin import ArrayAttr, SymbolRefAttr

from asdl.ir.ifir import (
    BackendOp,
    ConnAttr,
    DesignOp,
    DeviceOp,
    InstanceOp,
    ModuleOp,
    NetOp,
)
from asdl.ir.nfir import (
    BackendOp as NfirBackendOp,
    DesignOp as NfirDesignOp,
    DeviceOp as NfirDeviceOp,
    InstanceOp as NfirInstanceOp,
    ModuleOp as NfirModuleOp,
    NetOp as NfirNetOp,
)


def convert_design(design: NfirDesignOp) -> DesignOp:
    modules: List[ModuleOp] = []
    devices: List[DeviceOp] = []

    for op in design.body.block.ops:
        if isinstance(op, NfirModuleOp):
            modules.append(_convert_module(op))
            continue
        if isinstance(op, NfirDeviceOp):
            devices.append(_convert_device(op))
            continue
        raise ValueError("asdl_nfir.design contains non-module/device ops")

    return DesignOp(
        region=[*modules, *devices],
        top=design.top,
    )


def _convert_module(module: NfirModuleOp) -> ModuleOp:
    nfir_nets = [op for op in module.body.block.ops if isinstance(op, NfirNetOp)]
    nfir_instances = [
        op for op in module.body.block.ops if isinstance(op, NfirInstanceOp)
    ]

    net_ops: List[NetOp] = []
    conn_map: Dict[str, List[ConnAttr]] = {
        inst.name_attr.data: [] for inst in nfir_instances
    }

    for net in nfir_nets:
        net_name = net.name_attr.data
        net_ops.append(NetOp(name=net_name, src=net.src))
        for endpoint in net.endpoints.data:
            conn_list = conn_map.get(endpoint.inst.data)
            if conn_list is None:
                continue
            conn_list.append(
                ConnAttr(endpoint.pin, net.name_attr)
            )

    inst_ops: List[InstanceOp] = []
    for inst in nfir_instances:
        conns = conn_map.get(inst.name_attr.data, [])
        inst_ops.append(
            InstanceOp(
                name=inst.name_attr,
                ref=SymbolRefAttr(inst.ref.data),
                conns=ArrayAttr(conns),
                params=inst.params,
                doc=inst.doc,
                src=inst.src,
            )
        )

    return ModuleOp(
        name=module.sym_name,
        port_order=module.port_order,
        region=[*net_ops, *inst_ops],
        doc=module.doc,
        src=module.src,
    )


def _convert_device(device: NfirDeviceOp) -> DeviceOp:
    backends: List[BackendOp] = []
    for backend in device.body.block.ops:
        if not isinstance(backend, NfirBackendOp):
            raise ValueError("asdl_nfir.device contains non-backend ops")
        backends.append(
            BackendOp(
                name=backend.name_attr,
                template=backend.template,
                params=backend.params,
                props=backend.props,
                src=backend.src,
            )
        )

    return DeviceOp(
        name=device.sym_name,
        ports=device.ports,
        params=device.params,
        region=backends,
        doc=device.doc,
        src=device.src,
    )


__all__ = ["convert_design"]
