"""PatternedGraph core dataclasses for the refactor model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Literal, Optional, TypeAlias

from .registries import ExprId, GraphId, RegistrySet

ModuleId: TypeAlias = GraphId
NetId: TypeAlias = GraphId
InstId: TypeAlias = GraphId
EndpointId: TypeAlias = GraphId


@dataclass
class NetBundle:
    """Represent a net bundle with a name expression reference.

    Attributes:
        net_id: Stable net identifier.
        name_expr_id: Expression ID for the net name.
        endpoint_ids: Ordered endpoint bundle IDs owned by this net.
        attrs: Optional attributes for tools or passes.
    """

    net_id: NetId
    name_expr_id: ExprId
    endpoint_ids: list[EndpointId]
    attrs: Optional[Dict[str, object]] = None


@dataclass
class InstanceBundle:
    """Represent an instance with pattern-aware name references.

    Attributes:
        inst_id: Stable instance identifier.
        name_expr_id: Expression ID for the instance name.
        ref_kind: Reference kind (module/device).
        ref_id: Referenced module or device ID.
        ref_raw: Raw reference token.
        param_expr_ids: Optional mapping of parameter names to expression IDs.
        attrs: Optional attributes for tools or passes.
    """

    inst_id: InstId
    name_expr_id: ExprId
    ref_kind: Literal["module", "device"]
    ref_id: GraphId
    ref_raw: str
    param_expr_ids: Optional[Dict[str, ExprId]] = None
    attrs: Optional[Dict[str, object]] = None


@dataclass
class EndpointBundle:
    """Represent an endpoint bundle owned by a net.

    Attributes:
        endpoint_id: Stable endpoint identifier.
        net_id: Owning net identifier.
        port_expr_id: Expression ID for the endpoint token expression.
        attrs: Optional attributes for tools or passes.
    """

    endpoint_id: EndpointId
    net_id: NetId
    port_expr_id: ExprId
    attrs: Optional[Dict[str, object]] = None


@dataclass
class ModuleGraph:
    """Module-scoped graph data for PatternedGraph.

    Attributes:
        module_id: Stable module identifier.
        name: Module name.
        file_id: Source file identifier.
        port_order: Optional ordered port list for emission.
        nets: Net bundles keyed by net ID.
        instances: Instance bundles keyed by instance ID.
        endpoints: Endpoint bundles keyed by endpoint ID.
    """

    module_id: ModuleId
    name: str
    file_id: str
    port_order: Optional[list[str]] = None
    nets: Dict[NetId, NetBundle] = field(default_factory=dict)
    instances: Dict[InstId, InstanceBundle] = field(default_factory=dict)
    endpoints: Dict[EndpointId, EndpointBundle] = field(default_factory=dict)


@dataclass
class ProgramGraph:
    """Program-level container for PatternedGraph modules.

    Attributes:
        modules: Module graphs keyed by module ID.
        registries: Optional registry set for pattern and metadata lookup.
    """

    modules: Dict[ModuleId, ModuleGraph] = field(default_factory=dict)
    registries: RegistrySet = field(default_factory=RegistrySet)


__all__ = [
    "EndpointBundle",
    "InstanceBundle",
    "InstId",
    "ModuleGraph",
    "ModuleId",
    "NetBundle",
    "NetId",
    "ProgramGraph",
]
