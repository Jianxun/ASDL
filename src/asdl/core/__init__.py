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
from .registries import (
    AnnotationIndex,
    ExprId,
    GraphId,
    GroupSlice,
    PatternExpr,
    PatternExpressionRegistry,
    RegistrySet,
    SchematicHints,
    SourceSpanIndex,
)

__all__ = [
    "AnnotationIndex",
    "EndpointBundle",
    "ExprId",
    "GraphId",
    "GroupSlice",
    "InstanceBundle",
    "InstId",
    "ModuleGraph",
    "ModuleId",
    "NetBundle",
    "NetId",
    "PatternExpr",
    "PatternExpressionRegistry",
    "ProgramGraph",
    "RegistrySet",
    "SchematicHints",
    "SourceSpanIndex",
]
