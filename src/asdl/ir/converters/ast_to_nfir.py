from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from xdsl.dialects.builtin import DictionaryAttr, FileLineColLoc, IntAttr, LocationAttr, StringAttr

from asdl.ast import AsdlDocument, DeviceBackendDecl, DeviceDecl, ModuleDecl
from asdl.ast.location import Locatable
from asdl.ir.nfir import (
    BackendOp,
    DesignOp,
    DeviceOp,
    EndpointAttr,
    InstanceOp,
    ModuleOp,
    NetOp,
)


def convert_document(document: AsdlDocument) -> DesignOp:
    modules: List[ModuleOp] = []
    devices: List[DeviceOp] = []

    if document.modules:
        for name, module in document.modules.items():
            modules.append(_convert_module(name, module))

    if document.devices:
        for name, device in document.devices.items():
            devices.append(_convert_device(name, device))

    design = DesignOp(
        region=modules + devices,
        top=document.top,
    )
    return design


def _convert_module(name: str, module: ModuleDecl) -> ModuleOp:
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
            endpoints = _parse_endpoints(endpoint_expr)
            nets.append(NetOp(name=net_name, endpoints=endpoints))

    if module.instances:
        for inst_name, expr in module.instances.items():
            ref, params = _parse_instance_expr(expr)
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
    return ModuleOp(
        name=name,
        port_order=port_order,
        region=ops,
        src=_loc_attr(module._loc),
    )


def _convert_device(name: str, device: DeviceDecl) -> DeviceOp:
    backends: List[BackendOp] = []
    for backend_name, backend in device.backends.items():
        backends.append(_convert_backend(backend_name, backend))

    return DeviceOp(
        name=name,
        ports=device.ports,
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


def _parse_instance_expr(expr: str) -> Tuple[str, Dict[str, str]]:
    tokens = expr.split()
    if not tokens:
        raise ValueError("Instance expression must start with a model name")
    ref = tokens[0]
    params: Dict[str, str] = {}
    for token in tokens[1:]:
        if "=" not in token:
            raise ValueError(f"Invalid instance param token '{token}'; expected key=value")
        key, value = token.split("=", 1)
        if not key or not value:
            raise ValueError(f"Invalid instance param token '{token}'; expected key=value")
        params[key] = value
    return ref, params


def _parse_endpoints(expr: str) -> List[EndpointAttr]:
    endpoints: List[EndpointAttr] = []
    for token in expr.split():
        if token.count(".") != 1:
            raise ValueError(f"Invalid endpoint token '{token}'; expected inst.pin")
        inst, pin = token.split(".", 1)
        if not inst or not pin:
            raise ValueError(f"Invalid endpoint token '{token}'; expected inst.pin")
        endpoints.append(EndpointAttr(StringAttr(inst), StringAttr(pin)))
    return endpoints


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


__all__ = ["convert_document"]
