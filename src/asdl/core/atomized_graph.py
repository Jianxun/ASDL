"""AtomizedGraph core dataclasses for fully-resolved graphs."""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from typing import Dict, Literal, Optional, TypeAlias

from .registries import GraphId, RegistrySet

AtomizedModuleId: TypeAlias = GraphId
AtomizedDeviceId: TypeAlias = GraphId
AtomizedNetId: TypeAlias = GraphId
AtomizedInstId: TypeAlias = GraphId
AtomizedEndpointId: TypeAlias = GraphId

PatternedModuleId: TypeAlias = GraphId
PatternedNetId: TypeAlias = GraphId
PatternedInstId: TypeAlias = GraphId
PatternedEndpointId: TypeAlias = GraphId


@dataclass
class AtomizedNet:
    """Represent an atomized net with a resolved name.

    Attributes:
        net_id: Stable net identifier.
        name: Resolved net name.
        endpoint_ids: Ordered endpoint IDs connected to this net.
        patterned_net_id: Optional PatternedGraph net ID provenance.
        attrs: Optional attributes for tools or passes.
    """

    net_id: AtomizedNetId
    name: str
    endpoint_ids: list[AtomizedEndpointId]
    patterned_net_id: Optional[PatternedNetId] = None
    attrs: Optional[Dict[str, object]] = None


@dataclass
class AtomizedInstance:
    """Represent an atomized instance with resolved naming and reference info.

    Attributes:
        inst_id: Stable instance identifier.
        name: Resolved instance name.
        ref_kind: Reference kind ("module" or "device").
        ref_id: Referenced module or device ID.
        ref_raw: Raw reference token.
        param_values: Optional mapping of parameter names to resolved values.
        patterned_inst_id: Optional PatternedGraph instance ID provenance.
        attrs: Optional attributes for tools or passes.
    """

    inst_id: AtomizedInstId
    name: str
    ref_kind: Literal["module", "device"]
    ref_id: GraphId
    ref_raw: str
    param_values: Optional[Dict[str, object]] = None
    patterned_inst_id: Optional[PatternedInstId] = None
    attrs: Optional[Dict[str, object]] = None


@dataclass
class AtomizedEndpoint:
    """Represent an atomized endpoint linking a net to an instance port.

    Attributes:
        endpoint_id: Stable endpoint identifier.
        net_id: Owning net identifier.
        inst_id: Target instance identifier.
        port: Resolved port/pin name on the instance.
        patterned_endpoint_id: Optional PatternedGraph endpoint ID provenance.
        attrs: Optional attributes for tools or passes.
    """

    endpoint_id: AtomizedEndpointId
    net_id: AtomizedNetId
    inst_id: AtomizedInstId
    port: str
    patterned_endpoint_id: Optional[PatternedEndpointId] = None
    attrs: Optional[Dict[str, object]] = None


@dataclass
class AtomizedDeviceDef:
    """Represent an atomized device definition.

    Attributes:
        device_id: Stable device identifier.
        name: Device name.
        file_id: Source file identifier.
        ports: Ordered port list (empty list allowed).
        parameters: Optional mapping of parameter defaults or metadata.
        variables: Optional mapping of variable defaults or metadata.
        attrs: Optional attributes for tools or passes.
    """

    device_id: AtomizedDeviceId
    name: str
    file_id: str
    ports: list[str] = field(default_factory=list)
    parameters: Optional[Dict[str, object]] = None
    variables: Optional[Dict[str, object]] = None
    attrs: Optional[Dict[str, object]] = None


@dataclass
class AtomizedModuleGraph:
    """Module-scoped graph data for AtomizedGraph.

    Attributes:
        module_id: Stable module identifier.
        name: Module name.
        file_id: Source file identifier.
        ports: Ordered port list (empty list allowed).
        nets: Atomized nets keyed by net ID.
        instances: Atomized instances keyed by instance ID.
        endpoints: Atomized endpoints keyed by endpoint ID.
        patterned_module_id: Optional PatternedGraph module ID provenance.
    """

    module_id: AtomizedModuleId
    name: str
    file_id: str
    ports: list[str] = field(default_factory=list)
    nets: Dict[AtomizedNetId, AtomizedNet] = field(default_factory=dict)
    instances: Dict[AtomizedInstId, AtomizedInstance] = field(default_factory=dict)
    endpoints: Dict[AtomizedEndpointId, AtomizedEndpoint] = field(default_factory=dict)
    patterned_module_id: Optional[PatternedModuleId] = None
    port_order: InitVar[Optional[list[str]]] = None

    def __post_init__(self, port_order: Optional[list[str]]) -> None:
        """Normalize ports for legacy callers that pass port_order."""
        if self.ports is None:
            self.ports = []
        if port_order is not None:
            self.ports = list(port_order)


@dataclass
class AtomizedProgramGraph:
    """Program-level container for AtomizedGraph modules.

    Attributes:
        modules: Module graphs keyed by module ID.
        devices: Device definitions keyed by device ID.
        registries: Optional registry metadata carried from PatternedGraph.
    """

    modules: Dict[AtomizedModuleId, AtomizedModuleGraph] = field(default_factory=dict)
    devices: Dict[AtomizedDeviceId, AtomizedDeviceDef] = field(default_factory=dict)
    registries: RegistrySet = field(default_factory=RegistrySet)


def _atomized_module_port_order(module: AtomizedModuleGraph) -> list[str]:
    """Backward-compatible alias for AtomizedModuleGraph ports."""
    return module.ports


def _set_atomized_module_port_order(
    module: AtomizedModuleGraph, value: Optional[list[str]]
) -> None:
    module.ports = list(value) if value else []


AtomizedModuleGraph.port_order = property(
    _atomized_module_port_order,
    _set_atomized_module_port_order,
)


__all__ = [
    "AtomizedDeviceDef",
    "AtomizedDeviceId",
    "AtomizedEndpoint",
    "AtomizedEndpointId",
    "AtomizedInstance",
    "AtomizedInstId",
    "AtomizedModuleGraph",
    "AtomizedModuleId",
    "AtomizedNet",
    "AtomizedNetId",
    "AtomizedProgramGraph",
    "PatternedEndpointId",
    "PatternedInstId",
    "PatternedModuleId",
    "PatternedNetId",
]
