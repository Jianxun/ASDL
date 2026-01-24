"""Lower AtomizedGraph programs into IFIR design ops."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from xdsl.dialects.builtin import DictionaryAttr, StringAttr

from asdl.core.atomized_graph import (
    AtomizedDeviceDef,
    AtomizedEndpoint,
    AtomizedInstance,
    AtomizedModuleGraph,
    AtomizedNet,
    AtomizedProgramGraph,
)
from asdl.diagnostics import Diagnostic, Severity, format_code
from asdl.ir.ifir import ConnAttr, DesignOp, DeviceOp, InstanceOp, ModuleOp, NetOp

NO_SPAN_NOTE = "No source span available."

UNKNOWN_ATOMIZED_REFERENCE = format_code("IR", 40)
UNKNOWN_ATOMIZED_ENDPOINT = format_code("IR", 41)


def build_ifir_design(
    program: AtomizedProgramGraph,
    *,
    top_module_id: Optional[str] = None,
) -> Tuple[Optional[DesignOp], List[Diagnostic]]:
    """Lower an AtomizedGraph program into an IFIR design op.

    Args:
        program: Atomized program graph to lower.
        top_module_id: Optional module ID to use as the design top.

    Returns:
        Tuple of (IFIR design or None, diagnostics).
    """
    diagnostics: List[Diagnostic] = []
    had_error = False

    top_module = None
    if top_module_id is not None:
        top_module = program.modules.get(top_module_id)
        if top_module is None:
            diagnostics.append(
                _diagnostic(
                    UNKNOWN_ATOMIZED_REFERENCE,
                    f"Top module id '{top_module_id}' is not defined.",
                )
            )
            had_error = True
    elif len(program.modules) == 1:
        top_module = next(iter(program.modules.values()))

    module_ops: List[ModuleOp] = []
    for module in program.modules.values():
        module_op, module_error = _convert_module(module, program, diagnostics)
        module_ops.append(module_op)
        had_error = had_error or module_error

    device_ops = [_convert_device(device) for device in program.devices.values()]

    top_name = top_module.name if top_module is not None else None
    entry_file_id = top_module.file_id if top_module is not None else None
    design = DesignOp(
        region=[*module_ops, *device_ops],
        top=top_name,
        entry_file_id=entry_file_id,
    )
    if had_error:
        return None, diagnostics
    return design, diagnostics


def _convert_module(
    module: AtomizedModuleGraph,
    program: AtomizedProgramGraph,
    diagnostics: List[Diagnostic],
) -> Tuple[ModuleOp, bool]:
    """Convert an atomized module into an IFIR module op."""
    had_error = False
    conn_map: Dict[str, List[ConnAttr]] = {
        inst_id: [] for inst_id in module.instances
    }
    net_ops: List[NetOp] = []

    for net in module.nets.values():
        net_ops.append(NetOp(name=net.name))
        endpoints, endpoint_error = _collect_net_endpoints(
            module, net, diagnostics
        )
        had_error = had_error or endpoint_error
        for endpoint in endpoints:
            conns = conn_map.get(endpoint.inst_id)
            if conns is None:
                diagnostics.append(
                    _diagnostic(
                        UNKNOWN_ATOMIZED_ENDPOINT,
                        (
                            f"Endpoint '{endpoint.endpoint_id}' in module "
                            f"'{module.name}' references unknown instance "
                            f"'{endpoint.inst_id}'."
                        ),
                    )
                )
                had_error = True
                continue
            conns.append(
                ConnAttr(StringAttr(endpoint.port), StringAttr(net.name))
            )

    inst_ops: List[InstanceOp] = []
    for inst_id, instance in module.instances.items():
        ref_name, ref_file_id, ref_error = _resolve_ref(
            instance, program, diagnostics
        )
        had_error = had_error or ref_error
        if ref_name is None:
            continue
        inst_ops.append(
            InstanceOp(
                name=instance.name,
                ref=ref_name,
                ref_file_id=ref_file_id,
                params=_to_string_dict_attr(instance.param_values),
                conns=conn_map.get(inst_id, []),
            )
        )

    return (
        ModuleOp(
            name=module.name,
            port_order=module.ports or [],
            region=[*net_ops, *inst_ops],
            file_id=module.file_id,
        ),
        had_error,
    )


def _collect_net_endpoints(
    module: AtomizedModuleGraph,
    net: AtomizedNet,
    diagnostics: List[Diagnostic],
) -> Tuple[List[AtomizedEndpoint], bool]:
    """Collect endpoints for a net, emitting diagnostics for missing entries."""
    had_error = False
    endpoints: List[AtomizedEndpoint] = []
    for endpoint_id in net.endpoint_ids:
        endpoint = module.endpoints.get(endpoint_id)
        if endpoint is None:
            diagnostics.append(
                _diagnostic(
                    UNKNOWN_ATOMIZED_ENDPOINT,
                    (
                        f"Net '{net.name}' in module '{module.name}' references "
                        f"missing endpoint '{endpoint_id}'."
                    ),
                )
            )
            had_error = True
            continue
        endpoints.append(endpoint)
    return endpoints, had_error


def _convert_device(device: AtomizedDeviceDef) -> DeviceOp:
    """Convert an atomized device definition into an IFIR device op."""
    return DeviceOp(
        name=device.name,
        ports=device.ports or [],
        file_id=device.file_id,
        params=_to_string_dict_attr(device.parameters),
        variables=_to_string_dict_attr(device.variables),
        region=[],
    )


def _resolve_ref(
    instance: AtomizedInstance,
    program: AtomizedProgramGraph,
    diagnostics: List[Diagnostic],
) -> Tuple[Optional[str], Optional[str], bool]:
    """Resolve instance references into IFIR symbol data."""
    if instance.ref_kind == "module":
        module = program.modules.get(instance.ref_id)
        if module is None:
            diagnostics.append(
                _diagnostic(
                    UNKNOWN_ATOMIZED_REFERENCE,
                    (
                        f"Instance '{instance.name}' references unknown module "
                        f"id '{instance.ref_id}'."
                    ),
                )
            )
            return None, None, True
        return module.name, module.file_id, False
    if instance.ref_kind == "device":
        device = program.devices.get(instance.ref_id)
        if device is None:
            diagnostics.append(
                _diagnostic(
                    UNKNOWN_ATOMIZED_REFERENCE,
                    (
                        f"Instance '{instance.name}' references unknown device "
                        f"id '{instance.ref_id}'."
                    ),
                )
            )
            return None, None, True
        return device.name, device.file_id, False

    diagnostics.append(
        _diagnostic(
            UNKNOWN_ATOMIZED_REFERENCE,
            (
                f"Instance '{instance.name}' has unsupported ref kind "
                f"'{instance.ref_kind}'."
            ),
        )
    )
    return None, None, True


def _to_string_dict_attr(
    values: Optional[Dict[str, object]],
) -> Optional[DictionaryAttr]:
    """Convert a dictionary to a DictionaryAttr of string values."""
    if not values:
        return None
    payload = {key: StringAttr(_format_param_value(value)) for key, value in values.items()}
    return DictionaryAttr(payload)


def _format_param_value(value: object) -> str:
    """Format parameter values as strings."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _diagnostic(code: str, message: str) -> Diagnostic:
    """Create an error diagnostic without a source span."""
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        message=message,
        primary_span=None,
        notes=[NO_SPAN_NOTE],
        source="ir",
    )


__all__ = ["build_ifir_design"]
