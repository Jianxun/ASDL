"""PatternedGraph core dataclasses and registries."""

from .dump import dump_patterned_graph, patterned_graph_to_jsonable
from .graph_builder import PatternedGraphBuilder
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
from .pipeline import run_patterned_graph_pipeline
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
    "dump_patterned_graph",
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
    "PatternedGraphBuilder",
    "patterned_graph_to_jsonable",
    "ProgramGraph",
    "query",
    "RegistrySet",
    "run_patterned_graph_pipeline",
    "SchematicHints",
    "SourceSpanIndex",
]
