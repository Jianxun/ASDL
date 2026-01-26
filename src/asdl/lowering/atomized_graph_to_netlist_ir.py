"""Lower AtomizedGraph programs into NetlistIR designs."""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Tuple

from asdl.core.atomized_graph import (
    AtomizedDeviceDef,
    AtomizedEndpoint,
    AtomizedInstance,
    AtomizedModuleGraph,
    AtomizedNet,
    AtomizedPatternOrigin,
    AtomizedProgramGraph,
)
from asdl.core.registries import RegistrySet
from asdl.emit.netlist_ir import (
    NetlistBackend,
    NetlistConn,
    NetlistDesign,
    NetlistDevice,
    NetlistInstance,
    NetlistModule,
    NetlistNet,
    PatternExpressionEntry,
    PatternExpressionTable,
    PatternOrigin,
)


def _to_netlist_pattern_origin(
    origin: Optional[AtomizedPatternOrigin],
) -> Optional[PatternOrigin]:
    """Convert an AtomizedPatternOrigin into a NetlistIR PatternOrigin."""
    if origin is None:
        return None
    return PatternOrigin(
        expression_id=origin.expression_id,
        segment_index=origin.segment_index,
        base_name=origin.base_name,
        pattern_parts=list(origin.pattern_parts),
    )


def _collect_pattern_expr_ids(module: AtomizedModuleGraph) -> list[str]:
    """Collect ordered expression IDs referenced by atomized origins."""
    expr_ids: list[str] = []
    seen: set[str] = set()

    def _add_origin(origin: Optional[AtomizedPatternOrigin]) -> None:
        if origin is None:
            return
        expr_id = origin.expression_id
        if expr_id in seen:
            return
        seen.add(expr_id)
        expr_ids.append(expr_id)

    for net in module.nets.values():
        _add_origin(net.pattern_origin)
    for instance in module.instances.values():
        _add_origin(instance.pattern_origin)
    for endpoint in module.endpoints.values():
        _add_origin(endpoint.pattern_origin)
    return expr_ids


def _build_pattern_expression_table(
    registries: RegistrySet, expr_ids: Iterable[str]
) -> Optional[PatternExpressionTable]:
    """Build a module-local pattern expression table when possible."""
    expr_registry = registries.pattern_expressions
    expr_kinds = registries.pattern_expr_kinds
    if expr_registry is None or expr_kinds is None:
        return None
    entries: Dict[str, PatternExpressionEntry] = {}
    for expr_id in expr_ids:
        expr = expr_registry.get(expr_id)
        kind = expr_kinds.get(expr_id)
        if expr is None or kind is None:
            continue
        entries[expr_id] = PatternExpressionEntry(
            expression=expr.raw,
            kind=kind,
            span=expr.span,
        )
    return entries or None


def build_netlist_ir_design(
    program: AtomizedProgramGraph,
    *,
    top_module_id: Optional[str] = None,
) -> NetlistDesign:
    """Lower an AtomizedGraph program into a NetlistIR design.

    Args:
        program: Atomized program graph to lower.
        top_module_id: Optional module ID to use as the design top.

    Returns:
        NetlistIR design for the atomized program.
    """
    top_module = None
    if top_module_id is not None:
        top_module = program.modules.get(top_module_id)
    elif len(program.modules) == 1:
        top_module = next(iter(program.modules.values()))

    modules = [
        _convert_module(module, program)
        for module in program.modules.values()
    ]
    devices = [
        _convert_device(device, program.registries)
        for device in program.devices.values()
    ]

    return NetlistDesign(
        modules=modules,
        devices=devices,
        top=top_module.name if top_module is not None else None,
        entry_file_id=top_module.file_id if top_module is not None else None,
    )


def _convert_module(
    module: AtomizedModuleGraph,
    program: AtomizedProgramGraph,
) -> NetlistModule:
    """Convert an atomized module into a NetlistIR module."""
    conn_map: Dict[str, List[NetlistConn]] = {
        inst_id: [] for inst_id in module.instances
    }
    netlist_nets: List[NetlistNet] = []

    for net in module.nets.values():
        netlist_nets.append(
            NetlistNet(
                name=net.name,
                pattern_origin=_to_netlist_pattern_origin(net.pattern_origin),
            )
        )
        for endpoint in _collect_net_endpoints(module, net):
            conn_map[endpoint.inst_id].append(
                NetlistConn(port=endpoint.port, net=net.name)
            )

    netlist_instances: List[NetlistInstance] = []
    for inst_id, instance in module.instances.items():
        ref_name, ref_file_id = _resolve_ref(instance, program)
        netlist_instances.append(
            NetlistInstance(
                name=instance.name,
                ref=ref_name,
                ref_file_id=ref_file_id,
                params=_to_string_dict(instance.param_values),
                conns=conn_map.get(inst_id, []),
                pattern_origin=_to_netlist_pattern_origin(instance.pattern_origin),
            )
        )

    expr_ids = _collect_pattern_expr_ids(module)
    pattern_expression_table = _build_pattern_expression_table(
        program.registries, expr_ids
    )

    return NetlistModule(
        name=module.name,
        file_id=module.file_id,
        ports=list(module.ports or []),
        nets=netlist_nets,
        instances=netlist_instances,
        pattern_expression_table=pattern_expression_table,
    )


def _collect_net_endpoints(
    module: AtomizedModuleGraph,
    net: AtomizedNet,
) -> List[AtomizedEndpoint]:
    """Collect endpoints for a net in their declared order."""
    endpoints: List[AtomizedEndpoint] = []
    for endpoint_id in net.endpoint_ids:
        endpoint = module.endpoints.get(endpoint_id)
        if endpoint is not None:
            endpoints.append(endpoint)
    return endpoints


def _convert_device(
    device: AtomizedDeviceDef,
    registries: RegistrySet,
) -> NetlistDevice:
    """Convert an atomized device definition into a NetlistIR device."""
    backends: List[NetlistBackend] = []
    backend_defs = (
        registries.device_backends.get(device.device_id)
        if registries.device_backends
        else None
    )
    if backend_defs:
        for backend_name, backend_def in backend_defs.items():
            backends.append(
                NetlistBackend(
                    name=backend_name,
                    template=backend_def.template,
                    params=_to_string_dict(backend_def.parameters),
                    variables=_to_string_dict(backend_def.variables),
                    props=_to_string_dict(backend_def.props),
                )
            )
    else:
        templates = (
            registries.device_backend_templates.get(device.device_id)
            if registries.device_backend_templates
            else None
        )
        if templates:
            for backend_name, template in templates.items():
                backends.append(
                    NetlistBackend(
                        name=backend_name,
                        template=template,
                    )
                )
    return NetlistDevice(
        name=device.name,
        file_id=device.file_id,
        ports=list(device.ports or []),
        params=_to_string_dict(device.parameters),
        variables=_to_string_dict(device.variables),
        backends=backends,
    )


def _resolve_ref(
    instance: AtomizedInstance,
    program: AtomizedProgramGraph,
) -> Tuple[str, str]:
    """Resolve instance references into NetlistIR symbol data."""
    if instance.ref_kind == "module":
        module = program.modules[instance.ref_id]
        return module.name, module.file_id
    device = program.devices[instance.ref_id]
    return device.name, device.file_id


def _to_string_dict(values: Optional[Dict[str, object]]) -> Optional[Dict[str, str]]:
    """Convert a dictionary to string values for NetlistIR."""
    if not values:
        return None
    return {key: _format_param_value(value) for key, value in values.items()}


def _format_param_value(value: object) -> str:
    """Format parameter values as strings."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


__all__ = ["build_netlist_ir_design"]
