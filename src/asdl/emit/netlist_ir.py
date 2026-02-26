"""NetlistIR dataclass model for emission-ready designs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, TypeAlias

from asdl.diagnostics import SourceSpan

PatternPart: TypeAlias = str | int
PatternExpressionKind: TypeAlias = Literal["net", "inst", "endpoint", "param"]


@dataclass(frozen=True)
class PatternOrigin:
    """Pattern provenance metadata for a literal name.

    Attributes:
        expression_id: Module-local pattern expression identifier.
        segment_index: 0-based segment index for spliced expressions.
        base_name: Base name for the pattern before substitutions.
        pattern_parts: Ordered pattern parts appended to the base name.
    """

    expression_id: str
    segment_index: int
    base_name: str
    pattern_parts: list[PatternPart]


@dataclass(frozen=True)
class PatternExpressionEntry:
    """Pattern expression metadata stored on a module.

    Attributes:
        expression: Original pattern expression string.
        kind: Expression kind (net/inst/endpoint/param).
        span: Optional source span for diagnostics.
    """

    expression: str
    kind: PatternExpressionKind
    span: Optional[SourceSpan] = None


PatternExpressionTable: TypeAlias = dict[str, PatternExpressionEntry]


@dataclass(frozen=True)
class NetlistNet:
    """Represent a literal net within a module.

    Attributes:
        name: Literal net name.
        net_type: Optional net type or classification.
        pattern_origin: Optional pattern provenance metadata.
    """

    name: str
    net_type: Optional[str] = None
    pattern_origin: Optional[PatternOrigin] = None


@dataclass(frozen=True)
class NetlistConn:
    """Represent a named connection from an instance port to a net.

    Attributes:
        port: Port name on the instance.
        net: Target net name within the module.
    """

    port: str
    net: str


@dataclass(frozen=True)
class NetlistInstance:
    """Represent a literal instance in a module.

    Attributes:
        name: Literal instance name.
        ref: Referenced module or device name.
        ref_file_id: File ID where the reference is defined.
        params: Optional mapping of parameter names to literal values.
        conns: Ordered list of port-to-net connections.
        pattern_origin: Optional pattern provenance metadata.
    """

    name: str
    ref: str
    ref_file_id: str
    params: Optional[Dict[str, str]] = None
    conns: List[NetlistConn] = field(default_factory=list)
    pattern_origin: Optional[PatternOrigin] = None


@dataclass(frozen=True)
class NetlistBackend:
    """Represent backend-specific template metadata for a device.

    Attributes:
        name: Backend identifier (e.g., "sim.ngspice").
        template: Backend template string.
        params: Optional backend parameter defaults.
        variables: Optional backend variable defaults.
        props: Optional backend properties for emission.
    """

    name: str
    template: str
    params: Optional[Dict[str, str]] = None
    variables: Optional[Dict[str, str]] = None
    props: Optional[Dict[str, str]] = None


@dataclass(frozen=True)
class NetlistDevice:
    """Represent a device definition available to NetlistIR modules.

    Attributes:
        name: Device name.
        file_id: Source file identifier.
        ports: Ordered port list (empty list allowed).
        params: Optional mapping of parameter defaults.
        variables: Optional mapping of variable defaults.
        backends: Ordered list of backend-specific templates.
    """

    name: str
    file_id: str
    ports: List[str] = field(default_factory=list)
    params: Optional[Dict[str, str]] = None
    variables: Optional[Dict[str, str]] = None
    backends: List[NetlistBackend] = field(default_factory=list)


@dataclass(frozen=True)
class NetlistModule:
    """Represent a module definition in NetlistIR.

    Attributes:
        name: Module name.
        file_id: Source file identifier.
        ports: Ordered port list (empty list allowed).
        parameters: Optional mapping of module parameter defaults.
        nets: Ordered list of nets in the module.
        instances: Ordered list of instances in the module.
        pattern_expression_table: Optional pattern expression metadata.
    """

    name: str
    file_id: str
    ports: List[str] = field(default_factory=list)
    parameters: Optional[Dict[str, str]] = None
    nets: List[NetlistNet] = field(default_factory=list)
    instances: List[NetlistInstance] = field(default_factory=list)
    pattern_expression_table: Optional[PatternExpressionTable] = None


@dataclass(frozen=True)
class NetlistDesign:
    """Represent a NetlistIR design container.

    Attributes:
        modules: Ordered modules in the design.
        devices: Ordered devices in the design.
        top: Optional top module name.
        entry_file_id: Optional entry file identifier.
    """

    modules: List[NetlistModule] = field(default_factory=list)
    devices: List[NetlistDevice] = field(default_factory=list)
    top: Optional[str] = None
    entry_file_id: Optional[str] = None


__all__ = [
    "NetlistBackend",
    "NetlistConn",
    "NetlistDesign",
    "NetlistDevice",
    "NetlistInstance",
    "NetlistModule",
    "NetlistNet",
    "PatternExpressionEntry",
    "PatternExpressionKind",
    "PatternExpressionTable",
    "PatternOrigin",
]
