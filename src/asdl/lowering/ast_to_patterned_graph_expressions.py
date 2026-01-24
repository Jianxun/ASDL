"""Expression parsing helpers for AST -> PatternedGraph lowering."""

from __future__ import annotations

from typing import Dict, List, Mapping, Optional, Sequence

from asdl.ast import ModuleDecl, PatternDecl
from asdl.ast.location import Locatable
from asdl.core.graph_builder import PatternedGraphBuilder
from asdl.core.registries import PatternExprKind
from asdl.diagnostics import Diagnostic, Severity
from asdl.patterns_refactor.parser import (
    NamedPattern,
    PatternError,
    parse_pattern_expr,
)

from .ast_to_patterned_graph_diagnostics import NO_SPAN_NOTE, PATTERN_PARSE_ERROR
from .ast_to_patterned_graph_diagnostics import _diagnostic


def _collect_named_patterns(module: ModuleDecl) -> Dict[str, NamedPattern]:
    """Collect named pattern definitions from a module.

    Args:
        module: Module declaration with optional patterns block.

    Returns:
        Mapping of pattern names to NamedPattern definitions.
    """
    named_patterns: Dict[str, NamedPattern] = {}
    for name, value in (module.patterns or {}).items():
        if isinstance(value, PatternDecl):
            named_patterns[name] = NamedPattern(expr=value.expr, tag=value.tag)
        else:
            named_patterns[name] = NamedPattern(expr=str(value))
    return named_patterns


def _register_expression(
    expression: str,
    *,
    kind: PatternExprKind,
    builder: PatternedGraphBuilder,
    expr_cache: Dict[tuple[PatternExprKind, str], str],
    named_patterns: Mapping[str, NamedPattern],
    loc: Optional[Locatable],
    diagnostics: List[Diagnostic],
    module_name: str,
    context: str,
    require_single_segment: bool = False,
) -> Optional[str]:
    """Register and parse a pattern expression.

    Args:
        expression: Raw expression string to parse.
        kind: Semantic kind for the expression.
        builder: PatternedGraph builder instance.
        expr_cache: Module-local cache keyed by (kind, expression) to IDs.
        named_patterns: Named pattern definitions for parsing.
        loc: Optional source location for spans.
        diagnostics: Diagnostic collection to append to.
        module_name: Module name for context.
        context: Short string describing the expression context.
        require_single_segment: When True, reject spliced expressions.

    Returns:
        Expression ID or None on parse failure.
    """
    cache_key = (kind, expression)
    cached = expr_cache.get(cache_key)
    if cached is not None:
        return cached

    span = loc.to_source_span() if loc is not None else None
    parsed, errors = parse_pattern_expr(
        expression,
        named_patterns=named_patterns,
        span=span,
    )
    if errors:
        diagnostics.extend(
            _pattern_error_diagnostics(
                errors,
                module_name=module_name,
                context=context,
                fallback_loc=loc,
            )
        )
        return None
    if parsed is None:
        diagnostics.append(
            _diagnostic(
                PATTERN_PARSE_ERROR,
                f"Failed to parse '{expression}' in module '{module_name}'",
                loc,
            )
        )
        return None
    if require_single_segment and len(parsed.segments) > 1:
        diagnostics.extend(
            _pattern_error_diagnostics(
                [PatternError("Net name expressions must not contain splices.", span)],
                module_name=module_name,
                context=context,
                fallback_loc=loc,
            )
        )
        return None

    expr_id = builder.add_expression(parsed)
    builder.register_pattern_expr_kind(expr_id, kind)
    expr_cache[cache_key] = expr_id
    return expr_id


def _pattern_error_diagnostics(
    errors: Sequence[PatternError],
    *,
    module_name: str,
    context: str,
    fallback_loc: Optional[Locatable],
) -> List[Diagnostic]:
    """Convert pattern parse errors to diagnostics.

    Args:
        errors: Pattern parse errors.
        module_name: Module name for context.
        context: Expression context description.
        fallback_loc: Fallback location if the error span is missing.

    Returns:
        List of diagnostics for the errors.
    """
    diagnostics: List[Diagnostic] = []
    for error in errors:
        span = error.span
        if span is None and fallback_loc is not None:
            span = fallback_loc.to_source_span()
        notes = None
        if span is None:
            notes = [NO_SPAN_NOTE]
        diagnostics.append(
            Diagnostic(
                code=PATTERN_PARSE_ERROR,
                severity=Severity.ERROR,
                message=f"{error.message} in module '{module_name}' ({context}).",
                primary_span=span,
                notes=notes,
                source="core",
            )
        )
    return diagnostics
