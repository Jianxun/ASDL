"""Pattern expansion and binding helpers for PatternedGraph atomization."""

from __future__ import annotations

from typing import Iterable, Optional

from asdl.core.atomized_graph import AtomizedPatternOrigin, PatternPart
from asdl.core.registries import PatternExpressionRegistry
from asdl.diagnostics import Diagnostic, SourceSpan
from asdl.patterns import (
    BindingPlan,
    DEFAULT_MAX_ATOMS,
    PatternError,
    PatternExpr,
    PatternGroup,
    PatternLiteral,
    bind_patterns,
    expand_pattern,
)

from .patterned_graph_to_atomized_context import (
    PATTERN_EXPANSION_ERROR,
    _diagnostic,
)


def _find_expr_by_raw(
    expr_registry: PatternExpressionRegistry,
    raw_name: str,
    file_id: str,
) -> Optional[PatternExpr]:
    """Lookup a pattern expression by raw string with optional file hint.

    Args:
        expr_registry: Registry of parsed pattern expressions.
        raw_name: Raw expression string to match.
        file_id: Module file identifier for span disambiguation.

    Returns:
        Matching PatternExpr or None when missing/ambiguous.
    """
    matches = [expr for expr in expr_registry.values() if expr.raw == raw_name]
    if not matches:
        return None
    if len(matches) == 1:
        return matches[0]
    if file_id:
        file_matches = [
            expr for expr in matches if expr.span is not None and expr.span.file == file_id
        ]
        if len(file_matches) == 1:
            return file_matches[0]
    return None


def _is_literal_expr(expr: PatternExpr) -> bool:
    """Return True when a parsed expression is a literal without patterns."""
    if len(expr.segments) != 1:
        return False
    for token in expr.segments[0].tokens:
        if isinstance(token, PatternGroup):
            return False
        if not isinstance(token, PatternLiteral):
            return False
    return True


def _lookup_expr(
    expr_id: str,
    expr_registry: PatternExpressionRegistry,
    *,
    span: Optional[SourceSpan],
    diagnostics: list[Diagnostic],
) -> Optional[PatternExpr]:
    """Lookup a pattern expression by ID and emit a diagnostic on miss.

    Args:
        expr_id: Pattern expression identifier.
        expr_registry: Registry of parsed pattern expressions.
        span: Optional source span for diagnostics.
        diagnostics: Diagnostic collection to append to.

    Returns:
        Parsed pattern expression or None when missing.
    """
    expr = expr_registry.get(expr_id)
    if expr is None:
        diagnostics.append(
            _diagnostic(
                PATTERN_EXPANSION_ERROR,
                f"Missing pattern expression '{expr_id}'.",
                span,
            )
        )
    return expr


def _expand_pattern(
    expr: PatternExpr,
    *,
    diagnostics: list[Diagnostic],
    context: str,
    fallback_span: Optional[SourceSpan],
) -> Optional[list[str]]:
    """Expand a pattern expression to atoms with diagnostics.

    Args:
        expr: Pattern expression to expand.
        expr_id: Pattern expression identifier for provenance.
        diagnostics: Diagnostic collection to append to.
        context: Context string for error messages.
        fallback_span: Fallback span when the error lacks location data.

    Returns:
        List of literal atoms or None on failure.
    """
    atoms, errors = expand_pattern(expr)
    if atoms is None:
        diagnostics.extend(
            _pattern_error_diagnostics(
                errors,
                context=context,
                fallback_span=fallback_span,
            )
        )
        return None
    return atoms


def _expand_pattern_atoms(
    expr: PatternExpr,
    *,
    expr_id: str,
    diagnostics: list[Diagnostic],
    context: str,
    fallback_span: Optional[SourceSpan],
    max_atoms: int = DEFAULT_MAX_ATOMS,
) -> Optional[list[tuple[str, AtomizedPatternOrigin]]]:
    """Expand a pattern expression into atoms with per-atom origin metadata.

    Args:
        expr: Pattern expression to expand.
        expr_id: Pattern expression identifier for provenance.
        diagnostics: Diagnostic collection to append to.
        context: Context string for error messages.
        fallback_span: Fallback span when the error lacks location data.
        max_atoms: Maximum number of atoms to allow.

    Returns:
        List of (literal atom, origin) tuples or None on failure.
    """
    atoms: list[tuple[str, AtomizedPatternOrigin]] = []
    for segment_index, segment in enumerate(expr.segments):
        base_name = "".join(
            token.text
            for token in segment.tokens
            if isinstance(token, PatternLiteral)
        )
        current: list[tuple[str, list[PatternPart]]] = [("", [])]
        for token in segment.tokens:
            if isinstance(token, PatternLiteral):
                current = [
                    (value + token.text, parts) for value, parts in current
                ]
                continue
            if isinstance(token, PatternGroup):
                expanded: list[tuple[str, list[PatternPart]]] = []
                for value, parts in current:
                    for label in token.labels:
                        expanded.append((value + str(label), [*parts, label]))
                current = expanded
                if len(current) > max_atoms:
                    diagnostics.extend(
                        _pattern_error_diagnostics(
                            [
                                PatternError(
                                    (
                                        f"Pattern expression '{expr.raw}' exceeds "
                                        f"{max_atoms} atoms."
                                    ),
                                    expr.span,
                                )
                            ],
                            context=context,
                            fallback_span=fallback_span,
                        )
                    )
                    return None
                continue
            diagnostics.extend(
                _pattern_error_diagnostics(
                    [
                        PatternError(
                            f"Unhandled token in pattern expression '{expr.raw}'.",
                            expr.span,
                        )
                    ],
                    context=context,
                    fallback_span=fallback_span,
                )
            )
            return None
        if len(atoms) + len(current) > max_atoms:
            diagnostics.extend(
                _pattern_error_diagnostics(
                    [
                        PatternError(
                            f"Pattern expression '{expr.raw}' exceeds {max_atoms} atoms.",
                            expr.span,
                        )
                    ],
                    context=context,
                    fallback_span=fallback_span,
                )
            )
            return None
        atoms.extend(
            (
                literal,
                AtomizedPatternOrigin(
                    expression_id=expr_id,
                    segment_index=segment_index,
                    atom_index=atom_index,
                    base_name=base_name,
                    pattern_parts=parts,
                ),
            )
            for atom_index, (literal, parts) in enumerate(current)
        )
    return atoms


def _expand_endpoint(
    expr: PatternExpr,
    *,
    expr_id: str,
    diagnostics: list[Diagnostic],
    context: str,
    fallback_span: Optional[SourceSpan],
) -> Optional[list[tuple[str, str, AtomizedPatternOrigin]]]:
    """Expand an endpoint expression to (inst, pin, origin) atoms.

    Args:
        expr: Pattern expression to expand.
        diagnostics: Diagnostic collection to append to.
        context: Context string for error messages.
        fallback_span: Fallback span when the error lacks location data.

    Returns:
        List of (instance, port, origin) atoms or None on failure.
    """
    atoms = _expand_pattern_atoms(
        expr,
        expr_id=expr_id,
        diagnostics=diagnostics,
        context=context,
        fallback_span=fallback_span,
    )
    if atoms is None:
        return None

    endpoints: list[tuple[str, str, AtomizedPatternOrigin]] = []
    for literal, origin in atoms:
        if literal.count(".") != 1:
            diagnostics.extend(
                _pattern_error_diagnostics(
                    [
                        PatternError(
                            (
                                f"Endpoint expression '{expr.raw}' expands to "
                                f"invalid atom '{literal}'."
                            ),
                            expr.span,
                        )
                    ],
                    context=context,
                    fallback_span=fallback_span,
                )
            )
            return None
        inst, pin = literal.split(".", 1)
        endpoints.append((inst, pin, origin))

    return endpoints


def _bind_patterns(
    net_expr: PatternExpr,
    endpoint_expr: PatternExpr,
    *,
    net_expr_id: str,
    endpoint_expr_id: str,
    diagnostics: list[Diagnostic],
    context: str,
    fallback_span: Optional[SourceSpan],
) -> Optional[BindingPlan]:
    """Bind net and endpoint expressions with diagnostics.

    Args:
        net_expr: Parsed net expression.
        endpoint_expr: Parsed endpoint expression.
        net_expr_id: Net expression identifier.
        endpoint_expr_id: Endpoint expression identifier.
        diagnostics: Diagnostic collection to append to.
        context: Context string for error messages.
        fallback_span: Fallback span when the error lacks location data.

    Returns:
        Binding plan or None on failure.
    """
    plan, errors = bind_patterns(
        net_expr,
        endpoint_expr,
        net_expr_id=net_expr_id,
        endpoint_expr_id=endpoint_expr_id,
    )
    if plan is None:
        diagnostics.extend(
            _pattern_error_diagnostics(
                errors,
                context=context,
                fallback_span=fallback_span,
            )
        )
    return plan


def _pattern_error_diagnostics(
    errors: Iterable[PatternError],
    *,
    context: str,
    fallback_span: Optional[SourceSpan],
) -> list[Diagnostic]:
    """Convert pattern errors to diagnostics with context.

    Args:
        errors: Pattern errors to convert.
        context: Context string for error messages.
        fallback_span: Fallback span when the error lacks location data.

    Returns:
        List of diagnostics derived from pattern errors.
    """
    diagnostics: list[Diagnostic] = []
    for error in errors:
        diagnostics.append(
            _diagnostic(
                PATTERN_EXPANSION_ERROR,
                f"{error.message} ({context}).",
                error.span or fallback_span,
            )
        )
    return diagnostics
