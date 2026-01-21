"""Registry data structures for PatternedGraph metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Protocol, TypeAlias

from asdl.diagnostics import SourceSpan

GraphId: TypeAlias = str
ExprId: TypeAlias = str


class PatternExpr(Protocol):
    """Protocol for parsed pattern expressions.

    Attributes:
        raw: Original pattern expression string.
    """

    raw: str


PatternExpressionRegistry: TypeAlias = Dict[ExprId, PatternExpr]
SourceSpanIndex: TypeAlias = Dict[GraphId, SourceSpan]


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
        source_spans: Optional registry of source spans per entity ID.
        schematic_hints: Optional schematic-only metadata.
    """

    pattern_expressions: Optional[PatternExpressionRegistry] = None
    source_spans: Optional[SourceSpanIndex] = None
    schematic_hints: Optional[SchematicHints] = None


__all__ = [
    "ExprId",
    "GraphId",
    "GroupSlice",
    "PatternExpr",
    "PatternExpressionRegistry",
    "RegistrySet",
    "SchematicHints",
    "SourceSpanIndex",
]
