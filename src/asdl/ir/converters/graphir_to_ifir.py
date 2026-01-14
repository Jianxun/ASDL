"""GraphIR to IFIR projection helpers."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from xdsl.dialects.builtin import StringAttr

from asdl.diagnostics import Diagnostic, Severity, format_code
from asdl.ir.graphir import BundleOp, DeviceOp as GraphDeviceOp, EndpointOp
from asdl.ir.graphir import InstanceOp as GraphInstanceOp
from asdl.ir.graphir import ModuleOp as GraphModuleOp
from asdl.ir.graphir import NetOp as GraphNetOp
from asdl.ir.graphir import PatternExprOp, ProgramOp
from asdl.ir.ifir import (
    BackendOp,
    ConnAttr,
    DesignOp,
    DeviceOp,
    InstanceOp,
    ModuleOp,
    NetOp,
)

NO_SPAN_NOTE = "No source span available."
INVALID_GRAPHIR_PROGRAM = format_code("IR", 20)
INVALID_GRAPHIR_MODULE = format_code("IR", 21)
INVALID_GRAPHIR_DEVICE = format_code("IR", 22)
UNKNOWN_GRAPHIR_REFERENCE = format_code("IR", 23)
UNKNOWN_ENDPOINT_INSTANCE = format_code("IR", 24)


def convert_program(
    program: ProgramOp,
) -> Tuple[Optional[DesignOp], List[Diagnostic]]:
    """Project a GraphIR program op into an IFIR design op.

    Args:
        program: GraphIR program op to convert.

    Returns:
        Tuple of (IFIR design or None, diagnostics).
    """
    diagnostics: List[Diagnostic] = []
    had_error = False
    module_index: Dict[str, GraphModuleOp] = {}
    device_index: Dict[str, GraphDeviceOp] = {}

    ordered_ops = list(program.body.block.ops)
    for op in ordered_ops:
        if isinstance(op, GraphModuleOp):
            module_index[op.module_id.value.data] = op
            continue
        if isinstance(op, GraphDeviceOp):
            device_index[op.device_id.value.data] = op
            continue
        diagnostics.append(
            _diagnostic(
                INVALID_GRAPHIR_PROGRAM,
                "graphir.program contains non-module/device ops",
            )
        )
        had_error = True

    top_name: str | None = None
    entry_file_id: StringAttr | None = None
    if program.entry is not None:
        entry_id = program.entry.value.data
        entry_module = module_index.get(entry_id)
        if entry_module is None:
            diagnostics.append(
                _diagnostic(
                    UNKNOWN_GRAPHIR_REFERENCE,
                    f"Entry module_id '{entry_id}' is not defined",
                )
            )
            had_error = True
        else:
            top_name = entry_module.name_attr.data
            entry_file_id = entry_module.file_id

    converted_ops = []
    for op in ordered_ops:
        if isinstance(op, GraphModuleOp):
            module, module_diags, module_error = _convert_module(
                op,
                module_index=module_index,
                device_index=device_index,
            )
            diagnostics.extend(module_diags)
            had_error = had_error or module_error
            converted_ops.append(module)
            continue
        if isinstance(op, GraphDeviceOp):
            device, device_diags, device_error = _convert_device(op)
            diagnostics.extend(device_diags)
            had_error = had_error or device_error
            converted_ops.append(device)

    design = DesignOp(
        region=converted_ops,
        top=top_name,
        entry_file_id=entry_file_id,
    )
    if had_error:
        return None, diagnostics
    return design, diagnostics


def _convert_module(
    module: GraphModuleOp,
    *,
    module_index: Dict[str, GraphModuleOp],
    device_index: Dict[str, GraphDeviceOp],
) -> Tuple[ModuleOp, List[Diagnostic], bool]:
    diagnostics: List[Diagnostic] = []
    had_error = False
    nets: List[GraphNetOp] = []
    instances: List[GraphInstanceOp] = []

    for op in module.body.block.ops:
        if isinstance(op, GraphNetOp):
            nets.append(op)
            continue
        if isinstance(op, GraphInstanceOp):
            instances.append(op)
            continue
        if isinstance(op, (BundleOp, PatternExprOp)):
            continue
        diagnostics.append(
            _diagnostic(
                INVALID_GRAPHIR_MODULE,
                "graphir.module contains non-net/instance ops",
            )
        )
        had_error = True

    inst_by_id: Dict[str, GraphInstanceOp] = {
        inst.inst_id.value.data: inst for inst in instances
    }
    conn_map: Dict[str, List[ConnAttr]] = {inst_id: [] for inst_id in inst_by_id}
    net_ops: List[NetOp] = []

    for net in nets:
        net_name = net.name_attr.data
        net_ops.append(NetOp(name=net.name_attr))
        for endpoint in net.body.block.ops:
            if not isinstance(endpoint, EndpointOp):
                diagnostics.append(
                    _diagnostic(
                        INVALID_GRAPHIR_MODULE,
                        "graphir.net contains non-endpoint ops",
                    )
                )
                had_error = True
                continue
            inst_id = endpoint.inst_id.value.data
            conns = conn_map.get(inst_id)
            if conns is None:
                diagnostics.append(
                    _diagnostic(
                        UNKNOWN_ENDPOINT_INSTANCE,
                        (
                            "Endpoint references unknown instance "
                            f"'{inst_id}' in module '{module.name_attr.data}'"
                        ),
                    )
                )
                had_error = True
                continue
            conns.append(
                ConnAttr(StringAttr(endpoint.port_path.data), StringAttr(net_name))
            )

    inst_ops: List[InstanceOp] = []
    for inst_id, inst in inst_by_id.items():
        ref_name, ref_file_id, ref_error = _resolve_ref(
            inst,
            module_index=module_index,
            device_index=device_index,
            diagnostics=diagnostics,
        )
        had_error = had_error or ref_error
        if ref_name is None:
            continue
        conns = conn_map.get(inst_id, [])
        inst_ops.append(
            InstanceOp(
                name=inst.name_attr,
                ref=ref_name,
                ref_file_id=ref_file_id,
                params=inst.props,
                conns=conns,
            )
        )

    port_order = module.port_order or []
    return (
        ModuleOp(
            name=module.name_attr,
            port_order=port_order,
            region=[*net_ops, *inst_ops],
            file_id=module.file_id,
        ),
        diagnostics,
        had_error,
    )


def _convert_device(
    device: GraphDeviceOp,
) -> Tuple[DeviceOp, List[Diagnostic], bool]:
    diagnostics: List[Diagnostic] = []
    had_error = False
    backends: List[BackendOp] = []

    for backend in device.body.block.ops:
        if not isinstance(backend, BackendOp):
            diagnostics.append(
                _diagnostic(
                    INVALID_GRAPHIR_DEVICE,
                    "graphir.device contains non-backend ops",
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
            name=device.name_attr,
            ports=device.ports,
            file_id=device.file_id,
            params=device.params,
            region=backends,
        ),
        diagnostics,
        had_error,
    )


def _resolve_ref(
    instance: GraphInstanceOp,
    *,
    module_index: Dict[str, GraphModuleOp],
    device_index: Dict[str, GraphDeviceOp],
    diagnostics: List[Diagnostic],
) -> Tuple[Optional[str], Optional[StringAttr], bool]:
    ref = instance.module_ref
    kind = ref.kind.data
    sym_id = ref.sym_id.value.data
    if kind == "module":
        module = module_index.get(sym_id)
        if module is None:
            diagnostics.append(
                _diagnostic(
                    UNKNOWN_GRAPHIR_REFERENCE,
                    (
                        f"Instance '{instance.name_attr.data}' references "
                        f"unknown module_id '{sym_id}'"
                    ),
                )
            )
            return None, None, True
        return module.name_attr.data, module.file_id, False
    if kind == "device":
        device = device_index.get(sym_id)
        if device is None:
            diagnostics.append(
                _diagnostic(
                    UNKNOWN_GRAPHIR_REFERENCE,
                    (
                        f"Instance '{instance.name_attr.data}' references "
                        f"unknown device_id '{sym_id}'"
                    ),
                )
            )
            return None, None, True
        return device.name_attr.data, device.file_id, False

    diagnostics.append(
        _diagnostic(
            UNKNOWN_GRAPHIR_REFERENCE,
            (
                f"Instance '{instance.name_attr.data}' has unsupported "
                f"module_ref kind '{kind}'"
            ),
        )
    )
    return None, None, True


def _diagnostic(code: str, message: str) -> Diagnostic:
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        message=message,
        primary_span=None,
        notes=[NO_SPAN_NOTE],
        source="ir",
    )


__all__ = ["convert_program"]
