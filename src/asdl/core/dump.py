"""PatternedGraph and AtomizedGraph JSON serialization helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable, Optional

from asdl.diagnostics import Diagnostic, Severity, SourcePos, SourceSpan, format_code
from asdl.patterns import VisualizerPatternAtom, expand_literal_enums_for_visualizer

from .atomized_graph import (
    AtomizedDeviceDef,
    AtomizedEndpoint,
    AtomizedInstance,
    AtomizedModuleGraph,
    AtomizedNet,
    AtomizedPatternOrigin,
    AtomizedProgramGraph,
)
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
    DeviceBackendIndex,
    DeviceBackendInfo,
    DeviceBackendTemplateIndex,
    GroupSlice,
    PatternExpr,
    PatternExprKindIndex,
    PatternOriginIndex,
    RegistrySet,
    SchematicHints,
    SourceSpanIndex,
)

VISUALIZER_SCHEMA_VERSION = 0
VISUALIZER_NET_EXPANSION_MISMATCH = format_code("TOOL", 10)
VISUALIZER_NO_SPAN_NOTE = "No source span available."


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


def _atomized_pattern_origin_to_dict(
    origin: Optional[AtomizedPatternOrigin],
) -> Optional[dict]:
    """Convert an atomized pattern origin into a JSON-ready dict.

    Args:
        origin: Atomized pattern origin or None.

    Returns:
        Mapping payload for the origin, or None.
    """
    if origin is None:
        return None
    return {
        "expression_id": origin.expression_id,
        "segment_index": origin.segment_index,
        "atom_index": origin.atom_index,
        "base_name": origin.base_name,
        "pattern_parts": list(origin.pattern_parts),
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


def _device_backends_to_dict(
    backends: Optional[DeviceBackendIndex],
) -> Optional[dict]:
    """Convert backend metadata into a JSON-ready dict.

    Args:
        backends: Backend registry or None.

    Returns:
        Mapping payload for the registry, or None.
    """
    if backends is None:
        return None
    payload: dict[str, dict[str, dict[str, object]]] = {}
    for device_id in sorted(backends.keys()):
        backend_map = backends[device_id]
        payload[device_id] = {
            backend_name: _device_backend_info_to_dict(backend_map[backend_name])
            for backend_name in sorted(backend_map.keys())
        }
    return payload


def _device_backend_info_to_dict(info: DeviceBackendInfo) -> dict[str, object]:
    """Convert a backend info entry into a JSON-ready dict."""
    return {
        "template": info.template,
        "parameters": info.parameters,
        "variables": info.variables,
        "props": info.props,
    }


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
        "device_backends": _device_backends_to_dict(registries.device_backends),
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


def _atomized_net_to_dict(net: AtomizedNet) -> dict:
    """Convert an atomized net into a JSON-ready dict.

    Args:
        net: Atomized net to serialize.

    Returns:
        Mapping payload for the atomized net.
    """
    return {
        "net_id": net.net_id,
        "name": net.name,
        "endpoint_ids": list(net.endpoint_ids),
        "pattern_origin": _atomized_pattern_origin_to_dict(net.pattern_origin),
        "patterned_net_id": net.patterned_net_id,
        "attrs": net.attrs,
    }


def _atomized_instance_to_dict(instance: AtomizedInstance) -> dict:
    """Convert an atomized instance into a JSON-ready dict.

    Args:
        instance: Atomized instance to serialize.

    Returns:
        Mapping payload for the atomized instance.
    """
    return {
        "inst_id": instance.inst_id,
        "name": instance.name,
        "ref_kind": instance.ref_kind,
        "ref_id": instance.ref_id,
        "ref_raw": instance.ref_raw,
        "param_values": instance.param_values,
        "pattern_origin": _atomized_pattern_origin_to_dict(instance.pattern_origin),
        "patterned_inst_id": instance.patterned_inst_id,
        "attrs": instance.attrs,
    }


def _atomized_endpoint_to_dict(endpoint: AtomizedEndpoint) -> dict:
    """Convert an atomized endpoint into a JSON-ready dict.

    Args:
        endpoint: Atomized endpoint to serialize.

    Returns:
        Mapping payload for the atomized endpoint.
    """
    return {
        "endpoint_id": endpoint.endpoint_id,
        "net_id": endpoint.net_id,
        "inst_id": endpoint.inst_id,
        "port": endpoint.port,
        "pattern_origin": _atomized_pattern_origin_to_dict(endpoint.pattern_origin),
        "patterned_endpoint_id": endpoint.patterned_endpoint_id,
        "attrs": endpoint.attrs,
    }


def _atomized_module_graph_to_dict(module: AtomizedModuleGraph) -> dict:
    """Convert an atomized module graph into a JSON-ready dict.

    Args:
        module: Atomized module graph to serialize.

    Returns:
        Mapping payload for the atomized module graph.
    """
    nets = [
        _atomized_net_to_dict(module.nets[net_id])
        for net_id in sorted(module.nets.keys())
    ]
    instances = [
        _atomized_instance_to_dict(module.instances[inst_id])
        for inst_id in sorted(module.instances.keys())
    ]
    endpoints = [
        _atomized_endpoint_to_dict(module.endpoints[endpoint_id])
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
        "patterned_module_id": module.patterned_module_id,
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


def _atomized_device_def_to_dict(device: AtomizedDeviceDef) -> dict:
    """Convert an atomized device definition into a JSON-ready dict.

    Args:
        device: Atomized device definition to serialize.

    Returns:
        Mapping payload for the atomized device definition.
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


def _visualizer_module_to_dict(module: ModuleGraph) -> dict:
    """Convert a module graph into a visualizer-ready dict.

    Args:
        module: Module graph to serialize.

    Returns:
        Mapping payload for the module.
    """
    return {
        "module_id": module.module_id,
        "name": module.name,
        "file_id": module.file_id,
        "ports": list(module.ports),
    }


def _visualizer_device_to_dict(device: DeviceDef) -> dict:
    """Convert a device definition into a visualizer-ready dict."""
    return {
        "device_id": device.device_id,
        "name": device.name,
        "file_id": device.file_id,
        "ports": list(device.ports),
    }


def _visualizer_net_to_dict(
    net: NetBundle,
    *,
    net_id: Optional[str] = None,
    name_expr_id: Optional[str] = None,
    endpoint_ids: Optional[list[str]] = None,
) -> dict:
    """Convert a net bundle into a visualizer-ready dict.

    Args:
        net: Net bundle to serialize.
        net_id: Optional net ID override.
        name_expr_id: Optional name expression override.
        endpoint_ids: Optional endpoint ID override list.

    Returns:
        Mapping payload for the net.
    """
    resolved_endpoint_ids = net.endpoint_ids if endpoint_ids is None else endpoint_ids
    return {
        "net_id": net_id or net.net_id,
        "name_expr_id": name_expr_id or net.name_expr_id,
        "endpoint_ids": list(resolved_endpoint_ids),
    }


def _visualizer_instance_to_dict(
    instance: InstanceBundle,
    *,
    inst_id: Optional[str] = None,
    name_expr_id: Optional[str] = None,
) -> dict:
    """Convert an instance bundle into a visualizer-ready dict.

    Args:
        instance: Instance bundle to serialize.
        inst_id: Optional instance ID override.
        name_expr_id: Optional name expression override.

    Returns:
        Mapping payload for the instance.
    """
    return {
        "inst_id": inst_id or instance.inst_id,
        "name_expr_id": name_expr_id or instance.name_expr_id,
        "ref_kind": instance.ref_kind,
        "ref_id": instance.ref_id,
        "ref_raw": instance.ref_raw,
        "param_expr_ids": instance.param_expr_ids,
    }


def _visualizer_endpoint_to_dict(
    endpoint: EndpointBundle,
    *,
    endpoint_id: Optional[str] = None,
    net_id: Optional[str] = None,
    port_expr_id: Optional[str] = None,
    conn_label: Optional[str] = None,
) -> dict:
    """Convert an endpoint bundle into a visualizer-ready dict.

    Args:
        endpoint: Endpoint bundle to serialize.
        endpoint_id: Optional endpoint ID override.
        net_id: Optional net ID override.
        port_expr_id: Optional port expression override.
        conn_label: Optional connection label for numeric patterns.

    Returns:
        Mapping payload for the endpoint.
    """
    payload = {
        "endpoint_id": endpoint_id or endpoint.endpoint_id,
        "net_id": net_id or endpoint.net_id,
        "port_expr_id": port_expr_id or endpoint.port_expr_id,
    }
    if conn_label is not None:
        payload["conn_label"] = conn_label
    return payload


def _visualizer_expand_expr(
    expr_id: str,
    registries: RegistrySet,
) -> tuple[Optional[PatternExpr], Optional[list[VisualizerPatternAtom]]]:
    """Resolve and expand a pattern expression for visualizer output.

    Args:
        expr_id: Pattern expression identifier.
        registries: Registry set containing pattern expressions.

    Returns:
        Tuple of (pattern expression or None, expanded atoms or None).
    """
    if registries.pattern_expressions is None:
        return None, None
    expr = registries.pattern_expressions.get(expr_id)
    if expr is None:
        return None, None
    atoms, errors = expand_literal_enums_for_visualizer(expr)
    if atoms is None or errors:
        return expr, None
    return expr, atoms


def _visualizer_expanded_id(base_id: str, index: int) -> str:
    """Format a stable expanded identifier for visualizer output.

    Args:
        base_id: Base PatternedGraph identifier.
        index: Expansion index.

    Returns:
        Expanded identifier string.
    """
    return f"{base_id}:{index}"


def _visualizer_expr_id_for_atom(
    expr_id: str,
    expr: Optional[PatternExpr],
    atom: VisualizerPatternAtom,
) -> str:
    """Select the best expression identifier for a visualizer atom.

    Args:
        expr_id: Original expression identifier.
        expr: Parsed pattern expression (if available).
        atom: Expanded atom for the expression.

    Returns:
        Expression identifier or literal text for visualizer use.
    """
    if expr is not None and atom.text == expr.raw:
        return expr_id
    return atom.text


@dataclass(frozen=True)
class _VisualizerNetExpansion:
    """Net expansion metadata for visualizer dumps.

    Attributes:
        expr: Parsed pattern expression for the net name, if available.
        atoms: Expanded literal-enum atoms, or None if expansion is unavailable.
    """

    expr: Optional[PatternExpr]
    atoms: Optional[list[VisualizerPatternAtom]]


def _visualizer_net_expansions(
    module: ModuleGraph,
    registries: RegistrySet,
) -> dict[str, _VisualizerNetExpansion]:
    """Resolve net name expansions for visualizer output.

    Args:
        module: Module graph containing net bundles.
        registries: Registry set containing pattern expressions.

    Returns:
        Mapping of net IDs to expansion metadata.
    """
    expansions: dict[str, _VisualizerNetExpansion] = {}
    for net_id in module.nets.keys():
        net = module.nets[net_id]
        expr, atoms = _visualizer_expand_expr(net.name_expr_id, registries)
        expansions[net_id] = _VisualizerNetExpansion(expr=expr, atoms=atoms)
    return expansions


def _visualizer_net_ids_for_atoms(
    net_id: str,
    atoms: list[VisualizerPatternAtom],
) -> list[str]:
    """Build expanded net IDs for each expansion atom.

    Args:
        net_id: Base net ID.
        atoms: Expanded pattern atoms.

    Returns:
        List of net IDs aligned with atom indices.
    """
    return [
        net_id if index == 0 else _visualizer_expanded_id(net_id, index)
        for index in range(len(atoms))
    ]


def _visualizer_select_net_id(
    net_id: str,
    net_ids: Optional[list[str]],
    index: int,
) -> str:
    """Select a net ID for an expansion index.

    Args:
        net_id: Base net ID.
        net_ids: Expanded net IDs, if any.
        index: Expansion index for the endpoint.

    Returns:
        Net ID to use for the endpoint.
    """
    if not net_ids:
        return net_id
    if 0 <= index < len(net_ids):
        return net_ids[index]
    return net_ids[0]


def _visualizer_net_expansion_mismatch_diagnostic(
    net: NetBundle,
    *,
    expr: Optional[PatternExpr],
    net_count: int,
    endpoint_counts: Iterable[int],
    registries: RegistrySet,
) -> Diagnostic:
    """Build a diagnostic for net/endpoint expansion mismatches.

    Args:
        net: Net bundle with literal enum expansion.
        expr: Parsed pattern expression for the net name.
        net_count: Number of expanded net variants.
        endpoint_counts: Observed endpoint expansion counts.
        registries: Registry set for source span lookup.

    Returns:
        Diagnostic warning describing the mismatch.
    """
    span = None
    if registries.source_spans is not None:
        span = registries.source_spans.get(net.net_id)
    net_label = expr.raw if expr is not None else net.name_expr_id
    sorted_counts = ", ".join(str(count) for count in sorted(set(endpoint_counts)))
    message = (
        f"Net '{net_label}' expands to {net_count} literal variants, "
        f"but endpoint expansions have counts {{{sorted_counts}}}; "
        "remapping endpoints to index 0."
    )
    notes = None
    if span is None:
        notes = [VISUALIZER_NO_SPAN_NOTE]
    return Diagnostic(
        code=VISUALIZER_NET_EXPANSION_MISMATCH,
        severity=Severity.WARNING,
        message=message,
        primary_span=span,
        notes=notes,
        source="visualizer-dump",
    )


def _visualizer_instances_to_dict(
    module: ModuleGraph,
    registries: RegistrySet,
) -> list[dict]:
    """Expand instances with literal enums for visualizer output.

    Args:
        module: Module graph containing instances.
        registries: Registry set containing pattern expressions.

    Returns:
        List of instance payloads for the visualizer.
    """
    instances: list[dict] = []
    for inst_id in sorted(module.instances.keys()):
        instance = module.instances[inst_id]
        expr, atoms = _visualizer_expand_expr(instance.name_expr_id, registries)
        if atoms is None:
            instances.append(_visualizer_instance_to_dict(instance))
            continue
        if len(atoms) == 1:
            atom = atoms[0]
            instances.append(
                _visualizer_instance_to_dict(
                    instance,
                    inst_id=inst_id,
                    name_expr_id=_visualizer_expr_id_for_atom(
                        instance.name_expr_id,
                        expr,
                        atom,
                    ),
                )
            )
            continue
        for index, atom in enumerate(atoms):
            expanded_id = inst_id if index == 0 else _visualizer_expanded_id(inst_id, index)
            instances.append(
                _visualizer_instance_to_dict(
                    instance,
                    inst_id=expanded_id,
                    name_expr_id=atom.text,
                )
            )
    return instances


def _visualizer_endpoints_to_dict(
    module: ModuleGraph,
    registries: RegistrySet,
    net_expansions: dict[str, _VisualizerNetExpansion],
) -> tuple[list[dict], dict[str, list[str]], list[Diagnostic]]:
    """Expand endpoints with literal enums and numeric labels.

    Args:
        module: Module graph containing endpoints.
        registries: Registry set containing pattern expressions.
        net_expansions: Net expansion metadata for remapping endpoints.

    Returns:
        Tuple of (endpoint payloads, net endpoint id mapping, diagnostics).
    """
    endpoints: list[dict] = []
    endpoint_ids: dict[str, list[str]] = {}
    diagnostics: list[Diagnostic] = []
    endpoint_counts: dict[str, set[int]] = {}
    net_expansion_ids = {
        net_id: _visualizer_net_ids_for_atoms(net_id, expansion.atoms)
        for net_id, expansion in net_expansions.items()
        if expansion.atoms is not None and len(expansion.atoms) > 1
    }
    for endpoint_id in sorted(module.endpoints.keys()):
        endpoint = module.endpoints[endpoint_id]
        expr, atoms = _visualizer_expand_expr(endpoint.port_expr_id, registries)
        net_ids = net_expansion_ids.get(endpoint.net_id)
        endpoint_len = len(atoms) if atoms is not None else 1
        if net_ids is not None:
            endpoint_counts.setdefault(endpoint.net_id, set()).add(endpoint_len)
        if atoms is None:
            net_id = _visualizer_select_net_id(endpoint.net_id, net_ids, 0)
            payload = _visualizer_endpoint_to_dict(endpoint, net_id=net_id)
            endpoints.append(payload)
            endpoint_ids.setdefault(net_id, []).append(payload["endpoint_id"])
            continue
        if len(atoms) == 1:
            atom = atoms[0]
            net_id = _visualizer_select_net_id(endpoint.net_id, net_ids, 0)
            payload = _visualizer_endpoint_to_dict(
                endpoint,
                endpoint_id=endpoint_id,
                net_id=net_id,
                port_expr_id=_visualizer_expr_id_for_atom(
                    endpoint.port_expr_id,
                    expr,
                    atom,
                ),
                conn_label=atom.numeric_label,
            )
            endpoints.append(payload)
            endpoint_ids.setdefault(net_id, []).append(payload["endpoint_id"])
            continue
        for index, atom in enumerate(atoms):
            expanded_id = endpoint_id if index == 0 else _visualizer_expanded_id(endpoint_id, index)
            net_id = _visualizer_select_net_id(endpoint.net_id, net_ids, index)
            payload = _visualizer_endpoint_to_dict(
                endpoint,
                endpoint_id=expanded_id,
                net_id=net_id,
                port_expr_id=atom.text,
                conn_label=atom.numeric_label,
            )
            endpoints.append(payload)
            endpoint_ids.setdefault(net_id, []).append(expanded_id)
    for net_id, counts in endpoint_counts.items():
        expansion = net_expansions.get(net_id)
        if expansion is None or expansion.atoms is None:
            continue
        net_count = len(expansion.atoms)
        if any(count != net_count for count in counts):
            diagnostics.append(
                _visualizer_net_expansion_mismatch_diagnostic(
                    module.nets[net_id],
                    expr=expansion.expr,
                    net_count=net_count,
                    endpoint_counts=counts,
                    registries=registries,
                )
            )
    return endpoints, endpoint_ids, diagnostics


def _visualizer_nets_to_dict(
    module: ModuleGraph,
    net_expansions: dict[str, _VisualizerNetExpansion],
    endpoint_ids: dict[str, list[str]],
) -> list[dict]:
    """Expand nets with literal enums for visualizer output.

    Args:
        module: Module graph containing nets.
        net_expansions: Net expansion metadata.
        endpoint_ids: Mapping of net IDs to endpoint IDs (after remapping).

    Returns:
        List of net payloads for the visualizer.
    """
    nets: list[dict] = []
    for net_id in sorted(module.nets.keys()):
        net = module.nets[net_id]
        expansion = net_expansions.get(net_id)
        expr = expansion.expr if expansion is not None else None
        atoms = expansion.atoms if expansion is not None else None
        if atoms is None:
            nets.append(
                _visualizer_net_to_dict(
                    net,
                    endpoint_ids=endpoint_ids.get(net_id),
                )
            )
            continue
        if len(atoms) == 1:
            atom = atoms[0]
            nets.append(
                _visualizer_net_to_dict(
                    net,
                    net_id=net_id,
                    name_expr_id=_visualizer_expr_id_for_atom(
                        net.name_expr_id,
                        expr,
                        atom,
                    ),
                    endpoint_ids=endpoint_ids.get(net_id),
                )
            )
            continue
        for index, atom in enumerate(atoms):
            expanded_id = net_id if index == 0 else _visualizer_expanded_id(net_id, index)
            nets.append(
                _visualizer_net_to_dict(
                    net,
                    net_id=expanded_id,
                    name_expr_id=atom.text,
                    endpoint_ids=endpoint_ids.get(expanded_id, []),
                )
            )
    return nets


def _visualizer_pattern_expressions_to_dict(
    registries: RegistrySet,
) -> Optional[dict]:
    """Convert pattern expressions into a minimal visualizer-ready dict."""
    if registries.pattern_expressions is None:
        return None
    return {
        expr_id: {"raw": registries.pattern_expressions[expr_id].raw}
        for expr_id in sorted(registries.pattern_expressions.keys())
    }


def _visualizer_registries_to_dict(registries: RegistrySet) -> dict:
    """Convert registry data into a minimal visualizer-ready dict."""
    return {
        "pattern_expressions": _visualizer_pattern_expressions_to_dict(registries),
        "pattern_origins": _pattern_origins_to_dict(registries.pattern_origins),
        "schematic_hints": _schematic_hints_to_dict(registries.schematic_hints),
    }


def _visualizer_module_refs(
    graph: ProgramGraph, module: ModuleGraph
) -> list[ModuleGraph]:
    """Collect referenced modules for a module's instances.

    Args:
        graph: Program graph containing module definitions.
        module: Module whose instances reference other modules.

    Returns:
        Sorted list of referenced module graphs.
    """
    module_ids: set[str] = set()
    for instance in module.instances.values():
        if instance.ref_kind == "module" and instance.ref_id in graph.modules:
            module_ids.add(instance.ref_id)
    return sorted(
        (graph.modules[module_id] for module_id in module_ids),
        key=lambda ref: (ref.name, ref.module_id),
    )


def _visualizer_device_refs(
    graph: ProgramGraph, module: ModuleGraph
) -> list[DeviceDef]:
    """Collect referenced devices for a module's instances.

    Args:
        graph: Program graph containing device definitions.
        module: Module whose instances reference devices.

    Returns:
        Sorted list of referenced device definitions.
    """
    device_ids: set[str] = set()
    for instance in module.instances.values():
        if instance.ref_kind == "device" and instance.ref_id in graph.devices:
            device_ids.add(instance.ref_id)
    return sorted(
        (graph.devices[device_id] for device_id in device_ids),
        key=lambda ref: (ref.name, ref.device_id),
    )


def visualizer_module_list_to_jsonable(modules: Iterable[ModuleGraph]) -> dict:
    """Convert entry-file modules into a JSON-ready list payload.

    Args:
        modules: Iterable of module graphs to list.

    Returns:
        JSON-ready payload for module listing.
    """
    module_list = sorted(modules, key=lambda module: (module.name, module.module_id))
    return {
        "schema_version": VISUALIZER_SCHEMA_VERSION,
        "modules": [_visualizer_module_to_dict(module) for module in module_list],
    }


def visualizer_dump_to_jsonable(
    graph: ProgramGraph,
    module_id: str,
    *,
    diagnostics: Optional[list[Diagnostic]] = None,
) -> dict:
    """Convert a selected module into a visualizer JSON payload.

    Args:
        graph: Program graph containing module and device definitions.
        module_id: Identifier for the module to dump.
        diagnostics: Optional diagnostics list to append warnings.

    Returns:
        JSON-ready payload for the visualizer.

    Raises:
        KeyError: If the module ID does not exist in the graph.
    """
    module = graph.modules[module_id]
    net_expansions = _visualizer_net_expansions(module, graph.registries)
    endpoints, endpoint_ids, net_diags = _visualizer_endpoints_to_dict(
        module,
        graph.registries,
        net_expansions,
    )
    if diagnostics is not None:
        diagnostics.extend(net_diags)
    nets = _visualizer_nets_to_dict(
        module,
        net_expansions,
        endpoint_ids,
    )
    instances = _visualizer_instances_to_dict(module, graph.registries)
    return {
        "schema_version": VISUALIZER_SCHEMA_VERSION,
        "module": _visualizer_module_to_dict(module),
        "instances": instances,
        "nets": nets,
        "endpoints": endpoints,
        "registries": _visualizer_registries_to_dict(graph.registries),
        "refs": {
            "modules": [
                _visualizer_module_to_dict(ref) for ref in _visualizer_module_refs(graph, module)
            ],
            "devices": [
                _visualizer_device_to_dict(ref)
                for ref in _visualizer_device_refs(graph, module)
            ],
        },
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


def atomized_graph_to_jsonable(graph: AtomizedProgramGraph) -> dict:
    """Convert an AtomizedGraph into a JSON-serializable payload.

    Args:
        graph: Atomized program graph to serialize.

    Returns:
        JSON-ready mapping containing modules and registries.
    """
    modules = [
        _atomized_module_graph_to_dict(graph.modules[module_id])
        for module_id in sorted(graph.modules.keys())
    ]
    devices = [
        _atomized_device_def_to_dict(graph.devices[device_id])
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


def dump_atomized_graph(graph: AtomizedProgramGraph, *, indent: int = 2) -> str:
    """Render a deterministic JSON dump of an AtomizedGraph.

    Args:
        graph: Atomized program graph to serialize.
        indent: JSON indentation level.

    Returns:
        Deterministic JSON string for the graph.
    """
    return json.dumps(atomized_graph_to_jsonable(graph), indent=indent, sort_keys=True)


__all__ = [
    "atomized_graph_to_jsonable",
    "dump_atomized_graph",
    "dump_patterned_graph",
    "patterned_graph_to_jsonable",
    "visualizer_dump_to_jsonable",
    "visualizer_module_list_to_jsonable",
]
