"""Visualizer JSON serialization helpers for PatternedGraph."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from asdl.diagnostics import Diagnostic, Severity, format_code
from asdl.patterns import (
    VisualizerPatternAtom,
    expand_literal_enums_for_visualizer,
)

from .dump_common import _pattern_origins_to_dict, _schematic_hints_to_dict
from .graph import (
    DeviceDef,
    EndpointBundle,
    InstanceBundle,
    ModuleGraph,
    NetBundle,
    ProgramGraph,
)
from .registries import PatternExpr, RegistrySet

VISUALIZER_SCHEMA_VERSION = 0
VISUALIZER_NET_EXPANSION_MISMATCH = format_code("TOOL", 10)
VISUALIZER_NO_SPAN_NOTE = "No source span available."


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


@dataclass(frozen=True)
class _VisualizerEndpointExpansionResult:
    """Expanded endpoint payloads and expansion cardinality."""

    payloads: list[dict]
    endpoint_len: int


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


def _visualizer_net_expansion_ids(
    net_expansions: dict[str, _VisualizerNetExpansion],
) -> dict[str, list[str]]:
    """Build expanded net ID lists for multi-atom net expressions."""
    return {
        net_id: _visualizer_net_ids_for_atoms(net_id, expansion.atoms)
        for net_id, expansion in net_expansions.items()
        if expansion.atoms is not None and len(expansion.atoms) > 1
    }


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


def _visualizer_expand_endpoint_payloads(
    endpoint_id: str,
    endpoint: EndpointBundle,
    registries: RegistrySet,
    net_ids: Optional[list[str]],
) -> _VisualizerEndpointExpansionResult:
    """Expand one endpoint into one or more visualizer endpoint payloads."""
    expr, atoms = _visualizer_expand_expr(endpoint.port_expr_id, registries)
    if atoms is None:
        net_id = _visualizer_select_net_id(endpoint.net_id, net_ids, 0)
        return _VisualizerEndpointExpansionResult(
            payloads=[_visualizer_endpoint_to_dict(endpoint, net_id=net_id)],
            endpoint_len=1,
        )
    if len(atoms) == 1:
        atom = atoms[0]
        net_id = _visualizer_select_net_id(endpoint.net_id, net_ids, 0)
        return _VisualizerEndpointExpansionResult(
            payloads=[
                _visualizer_endpoint_to_dict(
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
            ],
            endpoint_len=1,
        )
    payloads: list[dict] = []
    for index, atom in enumerate(atoms):
        expanded_id = endpoint_id if index == 0 else _visualizer_expanded_id(endpoint_id, index)
        net_id = _visualizer_select_net_id(endpoint.net_id, net_ids, index)
        payloads.append(
            _visualizer_endpoint_to_dict(
                endpoint,
                endpoint_id=expanded_id,
                net_id=net_id,
                port_expr_id=atom.text,
                conn_label=atom.numeric_label,
            )
        )
    return _VisualizerEndpointExpansionResult(payloads=payloads, endpoint_len=len(atoms))


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


def _visualizer_build_endpoint_diagnostics(
    module: ModuleGraph,
    registries: RegistrySet,
    net_expansions: dict[str, _VisualizerNetExpansion],
    endpoint_counts: dict[str, set[int]],
) -> list[Diagnostic]:
    """Build diagnostics for net/endpoint expansion cardinality mismatches."""
    diagnostics: list[Diagnostic] = []
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
    return diagnostics


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
    endpoint_counts: dict[str, set[int]] = {}
    net_expansion_ids = _visualizer_net_expansion_ids(net_expansions)

    for endpoint_id in sorted(module.endpoints.keys()):
        endpoint = module.endpoints[endpoint_id]
        net_ids = net_expansion_ids.get(endpoint.net_id)
        result = _visualizer_expand_endpoint_payloads(
            endpoint_id,
            endpoint,
            registries,
            net_ids,
        )
        if net_ids is not None:
            endpoint_counts.setdefault(endpoint.net_id, set()).add(result.endpoint_len)
        for payload in result.payloads:
            endpoints.append(payload)
            endpoint_ids.setdefault(payload["net_id"], []).append(payload["endpoint_id"])

    diagnostics = _visualizer_build_endpoint_diagnostics(
        module,
        registries,
        net_expansions,
        endpoint_counts,
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
        nets.extend(
            _visualizer_net_payloads(
                net_id,
                module.nets[net_id],
                net_expansions.get(net_id),
                endpoint_ids,
            )
        )
    return nets


def _visualizer_net_payloads(
    net_id: str,
    net: NetBundle,
    expansion: Optional[_VisualizerNetExpansion],
    endpoint_ids: dict[str, list[str]],
) -> list[dict]:
    """Build one or more net payloads for a possibly expanded net."""
    expr = expansion.expr if expansion is not None else None
    atoms = expansion.atoms if expansion is not None else None
    if atoms is None:
        return [
            _visualizer_net_to_dict(
                net,
                endpoint_ids=endpoint_ids.get(net_id),
            )
        ]
    if len(atoms) == 1:
        atom = atoms[0]
        return [
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
        ]
    payloads: list[dict] = []
    for index, atom in enumerate(atoms):
        expanded_id = net_id if index == 0 else _visualizer_expanded_id(net_id, index)
        payloads.append(
            _visualizer_net_to_dict(
                net,
                net_id=expanded_id,
                name_expr_id=atom.text,
                endpoint_ids=endpoint_ids.get(expanded_id, []),
            )
        )
    return payloads


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
                _visualizer_module_to_dict(ref)
                for ref in _visualizer_module_refs(graph, module)
            ],
            "devices": [
                _visualizer_device_to_dict(ref)
                for ref in _visualizer_device_refs(graph, module)
            ],
        },
    }


__all__ = [
    "visualizer_dump_to_jsonable",
    "visualizer_module_list_to_jsonable",
]
