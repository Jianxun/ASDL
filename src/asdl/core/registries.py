"""Registry data structures for PatternedGraph metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Literal, Optional, Protocol, TypeAlias

from asdl.diagnostics import SourceSpan

GraphId: TypeAlias = str
ExprId: TypeAlias = str
AxisId: TypeAlias = str
PatternExprKind: TypeAlias = Literal["net", "inst", "endpoint", "param"]


class PatternExpr(Protocol):
    """Protocol for parsed pattern expressions.

    Attributes:
        raw: Original pattern expression string.
        segments: Parsed segments with tokens and spans.
        axes: Parsed axis metadata for named groups.
        axis_order: Left-to-right axis ordering for broadcast binding.
        span: Source span for the full expression.
    """

    raw: str
    segments: list["PatternSegment"]
    axes: list["AxisSpec"]
    axis_order: list[AxisId]
    span: Optional[SourceSpan]


class PatternSegment(Protocol):
    """Protocol for a pattern segment with tokens and span."""

    tokens: list[object]
    span: Optional[SourceSpan]


class AxisSpec(Protocol):
    """Protocol for named axis metadata in pattern expressions."""

    axis_id: AxisId
    kind: Literal["enum", "range"]
    labels: list[str | int]
    size: int
    order: int


PatternExpressionRegistry: TypeAlias = Dict[ExprId, PatternExpr]
SourceSpanIndex: TypeAlias = Dict[GraphId, SourceSpan]
AnnotationIndex: TypeAlias = Dict[GraphId, Dict[str, object]]
PatternOriginIndex: TypeAlias = Dict[GraphId, tuple[ExprId, int, int]]
ParamPatternOriginIndex: TypeAlias = Dict[tuple[GraphId, str], tuple[ExprId, int]]
PatternExprKindIndex: TypeAlias = Dict[ExprId, PatternExprKind]
DeviceBackendTemplateIndex: TypeAlias = Dict[GraphId, Dict[str, str]]


@dataclass(frozen=True)
class GroupSlice:
    """Describe a contiguous endpoint group for schematic layouts.

    Attributes:
        start: Starting index in the flattened endpoint list.
        count: Number of endpoints in the group.
        label: Optional label to display in schematics.
    """

    start: int
    count: int
    label: Optional[str] = None


@dataclass(frozen=True)
class SchematicHints:
    """Optional schematic-only metadata keyed by net ID.

    Attributes:
        net_groups: Mapping of net IDs to grouped endpoint slices.
        hub_group_index: Index of the hub group slice for layouts.
    """

    net_groups: Dict[GraphId, list[GroupSlice]] = field(default_factory=dict)
    hub_group_index: int = 0


@dataclass(frozen=True)
class RegistrySet:
    """Container for optional PatternedGraph registries.

    Attributes:
        pattern_expressions: Optional registry of parsed pattern expressions.
        pattern_expr_kinds: Optional registry of expression kinds by expr ID.
        pattern_origins: Optional registry of pattern origin tuples by entity ID.
        param_pattern_origins: Optional registry of instance param origins.
        device_backend_templates: Optional registry of backend templates by device ID.
        source_spans: Optional registry of source spans per entity ID.
        schematic_hints: Optional schematic-only metadata.
        annotations: Optional registry of annotations by entity ID.
    """

    pattern_expressions: Optional[PatternExpressionRegistry] = None
    pattern_expr_kinds: Optional[PatternExprKindIndex] = None
    pattern_origins: Optional[PatternOriginIndex] = None
    param_pattern_origins: Optional[ParamPatternOriginIndex] = None
    device_backend_templates: Optional[DeviceBackendTemplateIndex] = None
    source_spans: Optional[SourceSpanIndex] = None
    schematic_hints: Optional[SchematicHints] = None
    annotations: Optional[AnnotationIndex] = None


__all__ = [
    "ExprId",
    "GraphId",
    "GroupSlice",
    "AxisId",
    "AxisSpec",
    "PatternSegment",
    "PatternExpr",
    "PatternExprKind",
    "PatternExpressionRegistry",
    "PatternExprKindIndex",
    "PatternOriginIndex",
    "ParamPatternOriginIndex",
    "DeviceBackendTemplateIndex",
    "RegistrySet",
    "SchematicHints",
    "SourceSpanIndex",
    "AnnotationIndex",
]
