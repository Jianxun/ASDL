"""Refactor pattern service utilities."""

from .bind import BindingPlan, bind_patterns
from .expand import DEFAULT_MAX_ATOMS, EndpointAtom, expand_endpoint, expand_pattern
from .parser import (
    AxisSpec,
    NamedPattern,
    PatternError,
    PatternExpr,
    PatternGroup,
    PatternLiteral,
    PatternSegment,
    PatternToken,
    has_unnamed_groups,
    iter_pattern_groups,
    parse_pattern_expr,
)

__all__ = [
    "AxisSpec",
    "BindingPlan",
    "DEFAULT_MAX_ATOMS",
    "EndpointAtom",
    "NamedPattern",
    "PatternError",
    "PatternExpr",
    "PatternGroup",
    "PatternLiteral",
    "PatternSegment",
    "PatternToken",
    "bind_patterns",
    "expand_endpoint",
    "expand_pattern",
    "has_unnamed_groups",
    "iter_pattern_groups",
    "parse_pattern_expr",
]
