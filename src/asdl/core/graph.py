"""PatternedGraph core dataclasses for the refactor model."""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from typing import Dict, Literal, Optional, TypeAlias

from .registries import ExprId, GraphId, RegistrySet

ModuleId: TypeAlias = GraphId
DeviceId: TypeAlias = GraphId
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
class DeviceDef:
    """Represent a device definition for PatternedGraph.

    Attributes:
        device_id: Stable device identifier.
        name: Device name.
        file_id: Source file identifier.
        ports: Ordered port list (empty list allowed).
        parameters: Optional mapping of parameter defaults or metadata.
        variables: Optional mapping of variable defaults or metadata.
        attrs: Optional attributes for tools or passes.
    """

    device_id: DeviceId
    name: str
    file_id: str
    ports: list[str] = field(default_factory=list)
    parameters: Optional[Dict[str, object]] = None
    variables: Optional[Dict[str, object]] = None
    attrs: Optional[Dict[str, object]] = None


@dataclass
class ModuleGraph:
    """Module-scoped graph data for PatternedGraph.

    Attributes:
        module_id: Stable module identifier.
        name: Module name.
        file_id: Source file identifier.
        ports: Ordered port list (empty list allowed).
        variables: Optional mapping of variable defaults or metadata.
        nets: Net bundles keyed by net ID.
        instances: Instance bundles keyed by instance ID.
        endpoints: Endpoint bundles keyed by endpoint ID.
    """

    module_id: ModuleId
    name: str
    file_id: str
    ports: list[str] = field(default_factory=list)
    variables: Optional[Dict[str, object]] = None
    nets: Dict[NetId, NetBundle] = field(default_factory=dict)
    instances: Dict[InstId, InstanceBundle] = field(default_factory=dict)
    endpoints: Dict[EndpointId, EndpointBundle] = field(default_factory=dict)
    port_order: InitVar[Optional[list[str]]] = None

    def __post_init__(self, port_order: Optional[list[str]]) -> None:
        """Normalize ports for legacy callers that pass port_order."""
        if self.ports is None:
            self.ports = []
        if port_order is not None:
            self.ports = list(port_order)


@dataclass
class ProgramGraph:
    """Program-level container for PatternedGraph modules.

    Attributes:
        modules: Module graphs keyed by module ID.
        devices: Device definitions keyed by device ID.
        registries: Optional registry set for pattern and metadata lookup.
    """

    modules: Dict[ModuleId, ModuleGraph] = field(default_factory=dict)
    devices: Dict[DeviceId, DeviceDef] = field(default_factory=dict)
    registries: RegistrySet = field(default_factory=RegistrySet)


def _module_port_order(module: ModuleGraph) -> list[str]:
    """Backward-compatible alias for ModuleGraph ports."""
    return module.ports


def _set_module_port_order(module: ModuleGraph, value: Optional[list[str]]) -> None:
    module.ports = list(value) if value else []


ModuleGraph.port_order = property(_module_port_order, _set_module_port_order)


__all__ = [
    "DeviceDef",
    "DeviceId",
    "EndpointBundle",
    "InstanceBundle",
    "InstId",
    "ModuleGraph",
    "ModuleId",
    "NetBundle",
    "NetId",
    "ProgramGraph",
]
