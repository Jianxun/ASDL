"""Net and endpoint atomization helpers."""

from __future__ import annotations

from asdl.core.atomized_graph import AtomizedEndpoint, AtomizedNet
from asdl.core.graph import ModuleGraph, NetBundle
from asdl.patterns_refactor import PatternExpr

from .patterned_graph_to_atomized_context import (
    INVALID_ENDPOINT_EXPR,
    PATTERN_EXPANSION_ERROR,
    ModuleAtomizationContext,
    _diagnostic,
    _entity_span,
)
from .patterned_graph_to_atomized_patterns import (
    _bind_patterns,
    _expand_endpoint,
    _expand_pattern,
    _lookup_expr,
)


def atomize_nets(context: ModuleAtomizationContext) -> None:
    """Populate atomized nets and endpoints for a module.

    Args:
        context: Shared atomization context.
    """
    module = context.module
    expr_registry = context.expr_registry
    diagnostics = context.diagnostics
    atomized_module = context.atomized_module
    allocator = context.allocator
    net_name_to_id = context.net_name_to_id
    net_spans = context.net_spans

    for net_bundle in module.nets.values():
        net_span = _entity_span(context.source_spans, net_bundle.net_id)
        net_expr = _lookup_expr(
            net_bundle.name_expr_id,
            expr_registry,
            span=net_span,
            diagnostics=diagnostics,
        )
        if net_expr is None:
            continue

        net_atoms = _expand_pattern(
            net_expr,
            diagnostics=diagnostics,
            context=f"net '{net_expr.raw}' in module '{module.name}'",
            fallback_span=net_span,
        )
        if net_atoms is None:
            continue

        net_atom_ids: list[str] = []
        reported_duplicates: set[str] = set()
        for name in net_atoms:
            existing_id = net_name_to_id.get(name)
            if existing_id is not None:
                if name not in reported_duplicates:
                    diagnostics.append(
                        _diagnostic(
                            PATTERN_EXPANSION_ERROR,
                            (
                                "Pattern expansion for net "
                                f"'{net_expr.raw}' in module '{module.name}' "
                                f"produced duplicate atom '{name}'."
                            ),
                            net_span or net_expr.span,
                        )
                    )
                    reported_duplicates.add(name)
                net_atom_ids.append(existing_id)
                continue
            net_id = allocator.next_net()
            atomized_module.nets[net_id] = AtomizedNet(
                net_id=net_id,
                name=name,
                endpoint_ids=[],
                patterned_net_id=net_bundle.net_id,
                attrs=net_bundle.attrs,
            )
            net_name_to_id[name] = net_id
            net_spans[net_id] = net_span or net_expr.span
            net_atom_ids.append(net_id)

        _expand_endpoints_for_net(
            net_bundle,
            module,
            net_expr,
            net_atom_ids,
            context,
        )


def _expand_endpoints_for_net(
    net_bundle: NetBundle,
    module: ModuleGraph,
    net_expr: PatternExpr,
    net_atom_ids: list[str],
    context: ModuleAtomizationContext,
) -> None:
    """Expand endpoint expressions for a net bundle.

    Args:
        net_bundle: Patterned net bundle with endpoint references.
        module: Patterned module graph containing the endpoint bundles.
        net_expr: Parsed net name expression.
        net_atom_ids: Ordered atomized net identifiers.
        context: Shared atomization context.
    """
    for endpoint_id in net_bundle.endpoint_ids:
        endpoint_bundle = module.endpoints.get(endpoint_id)
        if endpoint_bundle is None:
            continue
        endpoint_expr = _lookup_expr(
            endpoint_bundle.port_expr_id,
            context.expr_registry,
            span=_entity_span(context.source_spans, endpoint_bundle.endpoint_id),
            diagnostics=context.diagnostics,
        )
        if endpoint_expr is None:
            continue

        endpoint_atoms = _expand_endpoint(
            endpoint_expr,
            diagnostics=context.diagnostics,
            context=f"endpoint '{endpoint_expr.raw}' in module '{module.name}'",
            fallback_span=_entity_span(context.source_spans, endpoint_bundle.endpoint_id),
        )
        if endpoint_atoms is None:
            continue

        plan = _bind_patterns(
            net_expr,
            endpoint_expr,
            net_expr_id=net_bundle.name_expr_id,
            endpoint_expr_id=endpoint_bundle.port_expr_id,
            diagnostics=context.diagnostics,
            context=(
                f"net '{net_expr.raw}' to endpoint '{endpoint_expr.raw}' in "
                f"module '{module.name}'"
            ),
            fallback_span=_entity_span(context.source_spans, endpoint_bundle.endpoint_id),
        )
        if plan is None:
            continue

        for endpoint_index, (inst_name, port) in enumerate(endpoint_atoms):
            if inst_name in context.duplicate_inst_names:
                context.diagnostics.append(
                    _diagnostic(
                        INVALID_ENDPOINT_EXPR,
                        (
                            f"Endpoint '{endpoint_expr.raw}' references non-unique "
                            f"instance '{inst_name}' in module '{module.name}'."
                        ),
                        _entity_span(context.source_spans, endpoint_bundle.endpoint_id),
                    )
                )
                continue
            inst_id = context.inst_name_to_id.get(inst_name)
            if inst_id is None:
                context.diagnostics.append(
                    _diagnostic(
                        INVALID_ENDPOINT_EXPR,
                        (
                            f"Endpoint '{endpoint_expr.raw}' references unknown "
                            f"instance '{inst_name}' in module '{module.name}'."
                        ),
                        _entity_span(context.source_spans, endpoint_bundle.endpoint_id),
                    )
                )
                continue

            net_index = plan.map_index(0, endpoint_index)
            if net_index >= len(net_atom_ids):
                context.diagnostics.append(
                    _diagnostic(
                        PATTERN_EXPANSION_ERROR,
                        (
                            "Endpoint binding produced an out-of-range net index "
                            f"for '{net_expr.raw}' in module '{module.name}'."
                        ),
                        _entity_span(context.source_spans, endpoint_bundle.endpoint_id),
                    )
                )
                continue

            net_id = net_atom_ids[net_index]
            endpoint_key = (inst_id, port)
            if endpoint_key in context.endpoint_keys:
                context.diagnostics.append(
                    _diagnostic(
                        INVALID_ENDPOINT_EXPR,
                        (
                            f"Endpoint '{endpoint_expr.raw}' binds instance "
                            f"'{inst_name}' port '{port}' multiple times in module "
                            f"'{module.name}'."
                        ),
                        _entity_span(context.source_spans, endpoint_bundle.endpoint_id),
                    )
                )
                continue
            context.endpoint_keys.add(endpoint_key)
            endpoint_atom_id = context.allocator.next_endpoint()
            context.atomized_module.endpoints[endpoint_atom_id] = AtomizedEndpoint(
                endpoint_id=endpoint_atom_id,
                net_id=net_id,
                inst_id=inst_id,
                port=port,
                patterned_endpoint_id=endpoint_bundle.endpoint_id,
                attrs=endpoint_bundle.attrs,
            )
            context.atomized_module.nets[net_id].endpoint_ids.append(endpoint_atom_id)
