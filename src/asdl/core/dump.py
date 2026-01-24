"""PatternedGraph JSON serialization helpers."""

from __future__ import annotations

import json
from typing import Optional

from asdl.diagnostics import SourcePos, SourceSpan

from .graph import (
    DeviceDef,
    EndpointBundle,
    InstanceBundle,
    ModuleGraph,
    NetBundle,
    ProgramGraph,
)
from .registries import (
    AxisSpec,
    DeviceBackendTemplateIndex,
    GroupSlice,
    PatternExpr,
    PatternExprKindIndex,
    PatternOriginIndex,
    RegistrySet,
    SchematicHints,
    SourceSpanIndex,
)


def _pos_to_dict(pos: Optional[SourcePos]) -> Optional[dict]:
    """Convert a source position to a JSON-ready dict.

    Args:
        pos: Source position or None.

    Returns:
        Mapping payload for the position, or None.
    """
    if pos is None:
        return None
    return {"line": pos.line, "col": pos.col}


def _span_to_dict(span: Optional[SourceSpan]) -> Optional[dict]:
    """Convert a source span to the diagnostics JSON shape.

    Args:
        span: Source span or None.

    Returns:
        Mapping payload for the span, or None.
    """
    if span is None:
        return None
    return {
        "file": span.file,
        "start": _pos_to_dict(span.start),
        "end": _pos_to_dict(span.end),
        "byte_start": span.byte_start,
        "byte_end": span.byte_end,
    }


def _pattern_token_to_dict(token: object) -> dict:
    """Convert a pattern token into a JSON-ready dict.

    Args:
        token: Pattern token instance.

    Returns:
        Mapping payload for the token.

    Raises:
        TypeError: If the token does not match known token shapes.
    """
    if hasattr(token, "text"):
        return {
            "kind": "literal",
            "text": getattr(token, "text"),
            "span": _span_to_dict(getattr(token, "span", None)),
        }
    if hasattr(token, "labels") and hasattr(token, "kind"):
        return {
            "kind": "group",
            "group_kind": getattr(token, "kind"),
            "labels": list(getattr(token, "labels")),
            "axis_id": getattr(token, "axis_id", None),
            "span": _span_to_dict(getattr(token, "span", None)),
        }
    raise TypeError(f"Unsupported pattern token type: {type(token)!r}")


def _pattern_segment_to_dict(segment: object) -> dict:
    """Convert a pattern segment into a JSON-ready dict.

    Args:
        segment: Pattern segment instance.

    Returns:
        Mapping payload for the segment.
    """
    tokens = [_pattern_token_to_dict(token) for token in getattr(segment, "tokens")]
    return {"tokens": tokens, "span": _span_to_dict(getattr(segment, "span", None))}


def _axis_spec_to_dict(axis: AxisSpec) -> dict:
    """Convert axis metadata into a JSON-ready dict.

    Args:
        axis: Axis metadata.

    Returns:
        Mapping payload for the axis metadata.
    """
    return {
        "axis_id": axis.axis_id,
        "kind": axis.kind,
        "labels": list(axis.labels),
        "size": axis.size,
        "order": axis.order,
    }


def _pattern_expr_to_dict(expr: PatternExpr) -> dict:
    """Convert a pattern expression into a JSON-ready dict.

    Args:
        expr: Pattern expression to convert.

    Returns:
        Mapping payload for the pattern expression.
    """
    return {
        "raw": expr.raw,
        "segments": [_pattern_segment_to_dict(seg) for seg in expr.segments],
        "axes": [_axis_spec_to_dict(axis) for axis in expr.axes],
        "axis_order": list(expr.axis_order),
        "span": _span_to_dict(expr.span),
    }


def _group_slice_to_dict(group: GroupSlice) -> dict:
    """Convert a schematic group slice into a JSON-ready dict.

    Args:
        group: Group slice instance.

    Returns:
        Mapping payload for the group slice.
    """
    return {"start": group.start, "count": group.count, "label": group.label}


def _schematic_hints_to_dict(hints: Optional[SchematicHints]) -> Optional[dict]:
    """Convert schematic hints into a JSON-ready dict.

    Args:
        hints: Schematic hints or None.

    Returns:
        Mapping payload for the schematic hints, or None.
    """
    if hints is None:
        return None
    net_groups = {
        net_id: [_group_slice_to_dict(group) for group in hints.net_groups[net_id]]
        for net_id in sorted(hints.net_groups.keys())
    }
    return {"net_groups": net_groups, "hub_group_index": hints.hub_group_index}


def _pattern_origins_to_dict(pattern_origins: Optional[PatternOriginIndex]) -> Optional[dict]:
    """Convert pattern origins to a JSON-ready dict.

    Args:
        pattern_origins: Pattern origin registry or None.

    Returns:
        Mapping payload for the registry, or None.
    """
    if pattern_origins is None:
        return None
    return {
        entity_id: {
            "expr_id": pattern_origins[entity_id][0],
            "segment_index": pattern_origins[entity_id][1],
            "token_index": pattern_origins[entity_id][2],
        }
        for entity_id in sorted(pattern_origins.keys())
    }


def _param_pattern_origins_to_list(
    param_origins: Optional[dict[tuple[str, str], tuple[str, int]]]
) -> Optional[list[dict]]:
    """Convert parameter pattern origins into a JSON-ready list.

    Args:
        param_origins: Parameter origin registry or None.

    Returns:
        List payload for the registry, or None.
    """
    if param_origins is None:
        return None
    payload: list[dict] = []
    for (inst_id, param_name), (expr_id, token_index) in sorted(
        param_origins.items(), key=lambda item: (item[0][0], item[0][1])
    ):
        payload.append(
            {
                "inst_id": inst_id,
                "param_name": param_name,
                "expr_id": expr_id,
                "token_index": token_index,
            }
        )
    return payload


def _source_spans_to_dict(source_spans: Optional[SourceSpanIndex]) -> Optional[dict]:
    """Convert source spans into a JSON-ready dict.

    Args:
        source_spans: Source span registry or None.

    Returns:
        Mapping payload for the registry, or None.
    """
    if source_spans is None:
        return None
    return {
        entity_id: _span_to_dict(source_spans[entity_id])
        for entity_id in sorted(source_spans.keys())
    }


def _pattern_expr_kinds_to_dict(
    kinds: Optional[PatternExprKindIndex],
) -> Optional[dict]:
    """Convert expression kinds to a JSON-ready dict.

    Args:
        kinds: Expression kind registry or None.

    Returns:
        Mapping payload for the registry, or None.
    """
    if kinds is None:
        return None
    return {expr_id: kinds[expr_id] for expr_id in sorted(kinds.keys())}


def _device_backend_templates_to_dict(
    templates: Optional[DeviceBackendTemplateIndex],
) -> Optional[dict]:
    """Convert backend templates into a JSON-ready dict.

    Args:
        templates: Backend template registry or None.

    Returns:
        Mapping payload for the registry, or None.
    """
    if templates is None:
        return None
    payload: dict[str, dict[str, str]] = {}
    for device_id in sorted(templates.keys()):
        backend_map = templates[device_id]
        payload[device_id] = {
            backend_name: backend_map[backend_name]
            for backend_name in sorted(backend_map.keys())
        }
    return payload


def _registry_set_to_dict(registries: RegistrySet) -> dict:
    """Convert registry data to a JSON-ready dict.

    Args:
        registries: Registry set to serialize.

    Returns:
        Mapping payload for the registry set.
    """
    pattern_expressions = None
    if registries.pattern_expressions is not None:
        pattern_expressions = {
            expr_id: _pattern_expr_to_dict(registries.pattern_expressions[expr_id])
            for expr_id in sorted(registries.pattern_expressions.keys())
        }
    annotations = None
    if registries.annotations is not None:
        annotations = {
            entity_id: registries.annotations[entity_id]
            for entity_id in sorted(registries.annotations.keys())
        }
    return {
        "pattern_expressions": pattern_expressions,
        "pattern_expr_kinds": _pattern_expr_kinds_to_dict(
            registries.pattern_expr_kinds
        ),
        "pattern_origins": _pattern_origins_to_dict(registries.pattern_origins),
        "param_pattern_origins": _param_pattern_origins_to_list(
            registries.param_pattern_origins
        ),
        "device_backend_templates": _device_backend_templates_to_dict(
            registries.device_backend_templates
        ),
        "source_spans": _source_spans_to_dict(registries.source_spans),
        "schematic_hints": _schematic_hints_to_dict(registries.schematic_hints),
        "annotations": annotations,
    }


def _net_bundle_to_dict(net: NetBundle) -> dict:
    """Convert a net bundle into a JSON-ready dict.

    Args:
        net: Net bundle to serialize.

    Returns:
        Mapping payload for the net bundle.
    """
    return {
        "net_id": net.net_id,
        "name_expr_id": net.name_expr_id,
        "endpoint_ids": list(net.endpoint_ids),
        "attrs": net.attrs,
    }


def _instance_bundle_to_dict(instance: InstanceBundle) -> dict:
    """Convert an instance bundle into a JSON-ready dict.

    Args:
        instance: Instance bundle to serialize.

    Returns:
        Mapping payload for the instance bundle.
    """
    return {
        "inst_id": instance.inst_id,
        "name_expr_id": instance.name_expr_id,
        "ref_kind": instance.ref_kind,
        "ref_id": instance.ref_id,
        "ref_raw": instance.ref_raw,
        "param_expr_ids": instance.param_expr_ids,
        "attrs": instance.attrs,
    }


def _endpoint_bundle_to_dict(endpoint: EndpointBundle) -> dict:
    """Convert an endpoint bundle into a JSON-ready dict.

    Args:
        endpoint: Endpoint bundle to serialize.

    Returns:
        Mapping payload for the endpoint bundle.
    """
    return {
        "endpoint_id": endpoint.endpoint_id,
        "net_id": endpoint.net_id,
        "port_expr_id": endpoint.port_expr_id,
        "attrs": endpoint.attrs,
    }


def _module_graph_to_dict(module: ModuleGraph) -> dict:
    """Convert a module graph into a JSON-ready dict.

    Args:
        module: Module graph to serialize.

    Returns:
        Mapping payload for the module graph.
    """
    nets = [
        _net_bundle_to_dict(module.nets[net_id])
        for net_id in sorted(module.nets.keys())
    ]
    instances = [
        _instance_bundle_to_dict(module.instances[inst_id])
        for inst_id in sorted(module.instances.keys())
    ]
    endpoints = [
        _endpoint_bundle_to_dict(module.endpoints[endpoint_id])
        for endpoint_id in sorted(module.endpoints.keys())
    ]
    return {
        "module_id": module.module_id,
        "name": module.name,
        "file_id": module.file_id,
        "ports": list(module.ports),
        "nets": nets,
        "instances": instances,
        "endpoints": endpoints,
    }


def _device_def_to_dict(device: DeviceDef) -> dict:
    """Convert a device definition into a JSON-ready dict.

    Args:
        device: Device definition to serialize.

    Returns:
        Mapping payload for the device definition.
    """
    return {
        "device_id": device.device_id,
        "name": device.name,
        "file_id": device.file_id,
        "ports": list(device.ports),
        "parameters": device.parameters,
        "variables": device.variables,
        "attrs": device.attrs,
    }


def patterned_graph_to_jsonable(graph: ProgramGraph) -> dict:
    """Convert a ProgramGraph into a JSON-serializable payload.

    Args:
        graph: Program graph to serialize.

    Returns:
        JSON-ready mapping containing modules and registries.
    """
    modules = [
        _module_graph_to_dict(graph.modules[module_id])
        for module_id in sorted(graph.modules.keys())
    ]
    devices = [
        _device_def_to_dict(graph.devices[device_id])
        for device_id in sorted(graph.devices.keys())
    ]
    return {
        "modules": modules,
        "devices": devices,
        "registries": _registry_set_to_dict(graph.registries),
    }


def dump_patterned_graph(graph: ProgramGraph, *, indent: int = 2) -> str:
    """Render a deterministic JSON dump of a PatternedGraph.

    Args:
        graph: Program graph to serialize.
        indent: JSON indentation level.

    Returns:
        Deterministic JSON string for the graph.
    """
    return json.dumps(patterned_graph_to_jsonable(graph), indent=indent, sort_keys=True)


__all__ = ["dump_patterned_graph", "patterned_graph_to_jsonable"]
