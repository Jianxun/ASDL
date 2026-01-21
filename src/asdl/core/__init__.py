"""PatternedGraph core dataclasses and registries."""

from .graph import (
    EndpointBundle,
    InstanceBundle,
    InstId,
    ModuleGraph,
    ModuleId,
    NetBundle,
    NetId,
    ProgramGraph,
)
from .index import GraphIndex
from .query import DesignQuery, query
from .registries import (
    AnnotationIndex,
    AxisId,
    AxisSpec,
    ExprId,
    GraphId,
    GroupSlice,
    ParamPatternOriginIndex,
    PatternExpr,
    PatternExpressionRegistry,
    PatternOriginIndex,
    PatternSegment,
    RegistrySet,
    SchematicHints,
    SourceSpanIndex,
)

__all__ = [
    "AnnotationIndex",
    "AxisId",
    "AxisSpec",
    "DesignQuery",
    "EndpointBundle",
    "ExprId",
    "GraphId",
    "GroupSlice",
    "GraphIndex",
    "InstanceBundle",
    "InstId",
    "ModuleGraph",
    "ModuleId",
    "NetBundle",
    "NetId",
    "ParamPatternOriginIndex",
    "PatternExpr",
    "PatternExpressionRegistry",
    "PatternOriginIndex",
    "PatternSegment",
    "ProgramGraph",
    "query",
    "RegistrySet",
    "SchematicHints",
    "SourceSpanIndex",
]
