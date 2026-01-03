from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from xdsl.dialects.builtin import DictionaryAttr, FileLineColLoc, IntAttr, LocationAttr, StringAttr

from asdl.ast import AsdlDocument, DeviceBackendDecl, DeviceDecl, ModuleDecl
from asdl.ast.location import Locatable
from asdl.diagnostics import Diagnostic, Severity, format_code
from asdl.ir.nfir import (
    BackendOp,
    DesignOp,
    DeviceOp,
    EndpointAttr,
    InstanceOp,
    ModuleOp,
    NetOp,
)

INVALID_INSTANCE_EXPR = format_code("IR", 1)
INVALID_ENDPOINT_EXPR = format_code("IR", 2)
NO_SPAN_NOTE = "No source span available."


def convert_document(document: AsdlDocument) -> Tuple[Optional[DesignOp], List[Diagnostic]]:
    diagnostics: List[Diagnostic] = []
    had_error = False
    modules: List[ModuleOp] = []
    devices: List[DeviceOp] = []

    if document.modules:
        for name, module in document.modules.items():
            module_op, module_diags, module_error = _convert_module(name, module)
            diagnostics.extend(module_diags)
            had_error = had_error or module_error
            modules.append(module_op)

    if document.devices:
        for name, device in document.devices.items():
            devices.append(_convert_device(name, device))

    design = DesignOp(
        region=modules + devices,
        top=document.top,
    )
    if had_error:
        return None, diagnostics
    return design, diagnostics


def _convert_module(
    name: str, module: ModuleDecl
) -> Tuple[ModuleOp, List[Diagnostic], bool]:
    diagnostics: List[Diagnostic] = []
    had_error = False
    nets: List[NetOp] = []
    instances: List[InstanceOp] = []
    port_order: List[str] = []

    if module.nets:
        for net_name, endpoint_expr in module.nets.items():
            is_port = net_name.startswith("$")
            if is_port:
                stripped_name = net_name[1:]
                port_order.append(stripped_name)
                net_name = stripped_name
            endpoints, endpoint_error = _parse_endpoints(endpoint_expr)
            if endpoint_error is not None:
                diagnostics.append(
                    _diagnostic(
                        INVALID_ENDPOINT_EXPR,
                        f"{endpoint_error} in module '{name}'",
                        module._loc,
                    )
                )
                had_error = True
                continue
            nets.append(NetOp(name=net_name, endpoints=endpoints))

    if module.instances:
        for inst_name, expr in module.instances.items():
            ref, params, instance_error = _parse_instance_expr(expr)
            if instance_error is not None:
                diagnostics.append(
                    _diagnostic(
                        INVALID_INSTANCE_EXPR,
                        f"{instance_error} in module '{name}'",
                        module._loc,
                    )
                )
                had_error = True
                continue
            instances.append(
                InstanceOp(
                    name=inst_name,
                    ref=ref,
                    params=_to_string_dict_attr(params),
                )
            )

    ops: List[object] = []
    ops.extend(nets)
    ops.extend(instances)
    return (
        ModuleOp(
            name=name,
            port_order=port_order,
            region=ops,
            src=_loc_attr(module._loc),
        ),
        diagnostics,
        had_error,
    )


def _convert_device(name: str, device: DeviceDecl) -> DeviceOp:
    backends: List[BackendOp] = []
    for backend_name, backend in device.backends.items():
        backends.append(_convert_backend(backend_name, backend))

    ports = device.ports or []
    return DeviceOp(
        name=name,
        ports=ports,
        params=_to_string_dict_attr(device.params),
        region=backends,
        src=_loc_attr(device._loc),
    )


def _convert_backend(name: str, backend: DeviceBackendDecl) -> BackendOp:
    props = backend.model_extra or None
    return BackendOp(
        name=name,
        template=backend.template,
        params=_to_string_dict_attr(backend.params),
        props=_to_string_dict_attr(props),
        src=_loc_attr(backend._loc),
    )


def _parse_instance_expr(expr: str) -> Tuple[Optional[str], Dict[str, str], Optional[str]]:
    tokens = expr.split()
    if not tokens:
        return None, {}, "Instance expression must start with a model name"
    ref = tokens[0]
    params: Dict[str, str] = {}
    for token in tokens[1:]:
        if "=" not in token:
            return None, {}, f"Invalid instance param token '{token}'; expected key=value"
        key, value = token.split("=", 1)
        if not key or not value:
            return None, {}, f"Invalid instance param token '{token}'; expected key=value"
        params[key] = value
    return ref, params, None


def _parse_endpoints(expr: List[str]) -> Tuple[List[EndpointAttr], Optional[str]]:
    endpoints: List[EndpointAttr] = []
    if isinstance(expr, str):
        return [], "Endpoint lists must be YAML lists of '<instance>.<pin>' strings"
    for token in expr:
        if token.count(".") != 1:
            return [], f"Invalid endpoint token '{token}'; expected inst.pin"
        inst, pin = token.split(".", 1)
        if not inst or not pin:
            return [], f"Invalid endpoint token '{token}'; expected inst.pin"
        endpoints.append(EndpointAttr(StringAttr(inst), StringAttr(pin)))
    return endpoints, None


def _to_string_dict_attr(
    values: Optional[Dict[str, object]],
) -> Optional[DictionaryAttr]:
    if not values:
        return None
    items = {key: StringAttr(_format_param_value(value)) for key, value in values.items()}
    return DictionaryAttr(items)


def _format_param_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _loc_attr(loc: Optional[Locatable]) -> Optional[LocationAttr]:
    if loc is None or loc.start_line is None or loc.start_col is None:
        return None
    return FileLineColLoc(StringAttr(loc.file), IntAttr(loc.start_line), IntAttr(loc.start_col))


def _diagnostic(code: str, message: str, loc: Optional[Locatable]) -> Diagnostic:
    span = loc.to_source_span() if loc is not None else None
    notes = None if span is not None else [NO_SPAN_NOTE]
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        message=message,
        primary_span=span,
        notes=notes,
        source="ir",
    )


__all__ = ["convert_document"]
