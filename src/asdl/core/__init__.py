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
