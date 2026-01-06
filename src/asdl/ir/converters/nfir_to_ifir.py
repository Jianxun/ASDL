from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from xdsl.dialects.builtin import ArrayAttr, LocationAttr, SymbolRefAttr

from asdl.diagnostics import Diagnostic, Severity, format_code
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
from asdl.ir.location import location_attr_to_span
from asdl.patterns import expand_endpoint, expand_pattern

INVALID_NFIR_DESIGN = format_code("IR", 3)
INVALID_NFIR_DEVICE = format_code("IR", 4)
UNKNOWN_ENDPOINT_INSTANCE = format_code("IR", 5)
PATTERN_BINDING_MISMATCH = format_code("IR", 6)
NO_SPAN_NOTE = "No source span available."


def convert_design(
    design: NfirDesignOp,
) -> Tuple[Optional[DesignOp], List[Diagnostic]]:
    diagnostics: List[Diagnostic] = []
    had_error = False
    modules: List[ModuleOp] = []
    devices: List[DeviceOp] = []

    for op in design.body.block.ops:
        if isinstance(op, NfirModuleOp):
            module, module_diags, module_error = _convert_module(op)
            diagnostics.extend(module_diags)
            had_error = had_error or module_error
            modules.append(module)
            continue
        if isinstance(op, NfirDeviceOp):
            device, device_diags, device_error = _convert_device(op)
            diagnostics.extend(device_diags)
            had_error = had_error or device_error
            devices.append(device)
            continue
        diagnostics.append(
            _diagnostic(
                INVALID_NFIR_DESIGN,
                "asdl_nfir.design contains non-module/device ops",
                getattr(op, "src", None),
            )
        )
        had_error = True

    design_op = DesignOp(
        region=[*modules, *devices],
        top=design.top,
    )
    if had_error:
        return None, diagnostics
    return design_op, diagnostics


def _convert_module(
    module: NfirModuleOp,
) -> Tuple[ModuleOp, List[Diagnostic], bool]:
    diagnostics: List[Diagnostic] = []
    had_error = False
    nfir_nets: List[NfirNetOp] = []
    nfir_instances: List[NfirInstanceOp] = []

    for op in module.body.block.ops:
        if isinstance(op, NfirNetOp):
            nfir_nets.append(op)
            continue
        if isinstance(op, NfirInstanceOp):
            nfir_instances.append(op)
            continue
        diagnostics.append(
            _diagnostic(
                INVALID_NFIR_DESIGN,
                "asdl_nfir.module contains non-net/instance ops",
                getattr(op, "src", None) or module.src,
            )
        )
        had_error = True

    net_ops: List[NetOp] = []
    conn_map: Dict[str, List[ConnAttr]] = {
        inst.name_attr.data: [] for inst in nfir_instances
    }

    pattern_diags, pattern_error = _verify_pattern_bindings(module, nfir_nets)
    diagnostics.extend(pattern_diags)
    had_error = had_error or pattern_error

    for net in nfir_nets:
        net_name = net.name_attr.data
        net_ops.append(NetOp(name=net_name, src=net.src))
        for endpoint in net.endpoints.data:
            conn_list = conn_map.get(endpoint.inst.data)
            if conn_list is None:
                diagnostics.append(
                    _diagnostic(
                        UNKNOWN_ENDPOINT_INSTANCE,
                        f"Endpoint references unknown instance '{endpoint.inst.data}'",
                        net.src or module.src,
                    )
                )
                had_error = True
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

    return (
        ModuleOp(
        name=module.sym_name,
        port_order=module.port_order,
        region=[*net_ops, *inst_ops],
        doc=module.doc,
        src=module.src,
        ),
        diagnostics,
        had_error,
    )


def _convert_device(
    device: NfirDeviceOp,
) -> Tuple[DeviceOp, List[Diagnostic], bool]:
    diagnostics: List[Diagnostic] = []
    had_error = False
    backends: List[BackendOp] = []
    for backend in device.body.block.ops:
        if not isinstance(backend, NfirBackendOp):
            diagnostics.append(
                _diagnostic(
                    INVALID_NFIR_DEVICE,
                    "asdl_nfir.device contains non-backend ops",
                    getattr(backend, "src", None) or device.src,
                )
            )
            had_error = True
            continue
        backends.append(
            BackendOp(
                name=backend.name_attr,
                template=backend.template,
                params=backend.params,
                props=backend.props,
                src=backend.src,
            )
        )

    return (
        DeviceOp(
        name=device.sym_name,
        ports=device.ports,
        params=device.params,
        region=backends,
        doc=device.doc,
        src=device.src,
        ),
        diagnostics,
        had_error,
    )


def _diagnostic(
    code: str, message: str, loc: LocationAttr | None = None
) -> Diagnostic:
    span = location_attr_to_span(loc)
    notes = None if span is not None else [NO_SPAN_NOTE]
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        message=message,
        primary_span=span,
        notes=notes,
        source="ir",
    )


def _verify_pattern_bindings(
    module: NfirModuleOp,
    nets: List[NfirNetOp],
) -> Tuple[List[Diagnostic], bool]:
    diagnostics: List[Diagnostic] = []
    had_error = False

    for net in nets:
        net_token = net.name_attr.data
        net_expanded, net_diags = expand_pattern(net_token)
        diagnostics.extend(net_diags)
        if net_expanded is None:
            had_error = True
            continue
        net_len = len(net_expanded)

        for endpoint in net.endpoints.data:
            endpoint_token = f"{endpoint.inst.data}.{endpoint.pin.data}"
            endpoint_expanded, endpoint_diags = expand_endpoint(
                endpoint.inst.data,
                endpoint.pin.data,
            )
            diagnostics.extend(endpoint_diags)
            if endpoint_expanded is None:
                had_error = True
                continue
            endpoint_len = len(endpoint_expanded)
            if net_len > 1 and endpoint_len != net_len:
                diagnostics.append(
                    _diagnostic(
                        PATTERN_BINDING_MISMATCH,
                        (
                            f"Net '{net_token}' expands to {net_len} atoms but "
                            f"endpoint '{endpoint_token}' expands to {endpoint_len}"
                        ),
                        net.src or module.src,
                    )
                )
                had_error = True

    return diagnostics, had_error


__all__ = ["convert_design"]
