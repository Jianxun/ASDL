"""Derived lookup helpers for PatternedGraph modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .graph import EndpointId, InstId, ModuleGraph, NetId
from .registries import ExprId, PatternExpressionRegistry, RegistrySet


def _resolve_expr_name(
    expr_id: ExprId, pattern_expressions: Optional[PatternExpressionRegistry]
) -> str:
    """Resolve a name expression ID to its raw pattern expression.

    Args:
        expr_id: Expression identifier stored on the graph bundle.
        pattern_expressions: Optional registry of parsed pattern expressions.

    Returns:
        Raw pattern expression string if available, otherwise the expr_id.
    """
    if pattern_expressions is None:
        return expr_id
    expr = pattern_expressions.get(expr_id)
    if expr is None:
        return expr_id
    return expr.raw


@dataclass(frozen=True)
class GraphIndex:
    """Index derived from a module graph for deterministic lookups.

    Attributes:
        net_to_endpoints: Ordered endpoint IDs per net.
        inst_name_to_id: Map of instance raw names to instance IDs.
        net_name_to_id: Map of net raw names to net IDs.
    """

    net_to_endpoints: dict[NetId, list[EndpointId]]
    inst_name_to_id: dict[str, InstId]
    net_name_to_id: dict[str, NetId]

    @classmethod
    def from_module(
        cls, module: ModuleGraph, registries: Optional[RegistrySet] = None
    ) -> GraphIndex:
        """Build a GraphIndex for the provided module graph.

        Args:
            module: ModuleGraph to index.
            registries: Optional RegistrySet for resolving name expressions.

        Returns:
            GraphIndex instance with deterministic lookups and adjacency lists.
        """
        pattern_expressions = None
        if registries is not None:
            pattern_expressions = registries.pattern_expressions

        net_to_endpoints = {
            net_id: list(net.endpoint_ids) for net_id, net in module.nets.items()
        }

        net_name_to_id: dict[str, NetId] = {}
        for net_id, net in module.nets.items():
            name = _resolve_expr_name(net.name_expr_id, pattern_expressions)
            if name not in net_name_to_id:
                net_name_to_id[name] = net_id

        inst_name_to_id: dict[str, InstId] = {}
        for inst_id, inst in module.instances.items():
            name = _resolve_expr_name(inst.name_expr_id, pattern_expressions)
            if name not in inst_name_to_id:
                inst_name_to_id[name] = inst_id

        return cls(
            net_to_endpoints=net_to_endpoints,
            inst_name_to_id=inst_name_to_id,
            net_name_to_id=net_name_to_id,
        )


__all__ = ["GraphIndex"]
