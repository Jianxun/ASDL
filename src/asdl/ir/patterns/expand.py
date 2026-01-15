"""Pattern expansion routines for IR pattern expressions."""

from __future__ import annotations

from typing import List, Optional, Tuple

from asdl.diagnostics import Diagnostic

from .diagnostics import (
    MAX_EXPANSION_SIZE,
    PATTERN_DUPLICATE_ATOM,
    PATTERN_EMPTY_SPLICE,
    PATTERN_TOO_LARGE,
    PATTERN_UNEXPANDED,
    _diagnostic,
    _duplicate_message,
    _empty_splice_message,
    _too_large_message,
)
from .endpoint_split import split_endpoint_atom
from .tokenize import (
    _find_duplicates,
    _has_whitespace,
    _range_values,
    _split_splice_segments,
    _tokenize_segment,
)


def expand_pattern(
    expression: str,
    *,
    max_atoms: int = MAX_EXPANSION_SIZE,
    allow_splice: bool = True,
) -> Tuple[Optional[List[str]], List[Diagnostic]]:
    """Expand a pattern expression into its literal atom list.

    Args:
        expression: Pattern expression to expand.
        max_atoms: Maximum expansion size before aborting.
        allow_splice: Whether to allow splice delimiters in the expression.

    Returns:
        Tuple of (atoms or None, diagnostics).
    """
    diagnostics: List[Diagnostic] = []
    if not expression:
        diagnostics.append(
            _diagnostic(PATTERN_UNEXPANDED, "Pattern expression is empty.")
        )
        return None, diagnostics

    segments, diag = _split_splice_segments(expression, allow_splice=allow_splice)
    if diag is not None:
        return None, [diag]
    if any(segment == "" for segment in segments):
        return None, [_diagnostic(PATTERN_EMPTY_SPLICE, _empty_splice_message(expression))]

    expanded: List[str] = []
    for segment in segments:
        segment_expansion, diag = _expand_segment(segment, expression, max_atoms)
        if diag is not None:
            return None, [diag]
        if len(expanded) + len(segment_expansion) > max_atoms:
            return None, [_diagnostic(PATTERN_TOO_LARGE, _too_large_message(expression, max_atoms))]
        expanded.extend(segment_expansion)

    duplicates = _find_duplicates(expanded)
    if duplicates:
        return None, [_diagnostic(PATTERN_DUPLICATE_ATOM, _duplicate_message(duplicates, expression))]

    return expanded, diagnostics


def expand_endpoint(
    inst: str,
    port: str,
    *,
    max_atoms: int = MAX_EXPANSION_SIZE,
    allow_splice: bool = True,
) -> Tuple[Optional[List[Tuple[str, str]]], List[Diagnostic]]:
    """Expand instance and port tokens into endpoint atoms.

    Endpoint expansion is performed on the full expression before splitting
    on '.' for each expanded atom.

    Args:
        inst: Instance token to expand.
        port: Port token to expand.
        max_atoms: Maximum expansion size before aborting.
        allow_splice: Whether to allow splice delimiters in the expression.

    Returns:
        Tuple of (endpoint tuples or None, diagnostics).
    """
    expression = f"{inst}.{port}"
    expanded, diagnostics = expand_pattern(
        expression,
        max_atoms=max_atoms,
        allow_splice=allow_splice,
    )
    if expanded is None:
        return None, diagnostics

    endpoints: List[Tuple[str, str]] = []
    for atom in expanded:
        try:
            inst_name, port_name = split_endpoint_atom(atom)
        except ValueError:
            return None, [
                _diagnostic(
                    PATTERN_UNEXPANDED,
                    (
                        f"Endpoint pattern expression '{expression}' expands to "
                        f"invalid atom '{atom}'."
                    ),
                )
            ]
        endpoints.append((inst_name, port_name))

    return endpoints, diagnostics


def _expand_segment(
    segment: str, expression: str, max_atoms: int
) -> Tuple[Optional[List[str]], Optional[Diagnostic]]:
    """Expand a single splice-free segment of a pattern expression.

    Args:
        segment: Pattern segment without splice delimiters.
        expression: Original pattern expression for diagnostics.
        max_atoms: Maximum expansion size before aborting.

    Returns:
        Tuple of (segment expansion or None, diagnostic).
    """
    if _has_whitespace(segment):
        return None, _diagnostic(
            PATTERN_UNEXPANDED,
            f"Whitespace is not allowed in pattern expression '{expression}'.",
        )

    tokens, diag = _tokenize_segment(segment, expression)
    if diag is not None:
        return None, diag

    current: List[str] = [""]
    for kind, payload in tokens:
        if kind == "literal":
            current = [value + payload for value in current]
            continue

        if kind == "enum":
            alts = payload
            next_size = len(current) * len(alts)
            if next_size > max_atoms:
                return None, _diagnostic(
                    PATTERN_TOO_LARGE,
                    _too_large_message(expression, max_atoms),
                )
            current = [_join_with_suffix(prefix, suffix) for prefix in current for suffix in alts]
            continue

        if kind == "range":
            start, end = payload
            value_count = abs(end - start) + 1
            next_size = len(current) * value_count
            if next_size > max_atoms:
                return None, _diagnostic(
                    PATTERN_TOO_LARGE,
                    _too_large_message(expression, max_atoms),
                )
            current = [
                _join_with_suffix(prefix, str(value))
                for prefix in current
                for value in _range_values(start, end)
            ]
            continue

        return None, _diagnostic(
            PATTERN_UNEXPANDED,
            f"Unhandled pattern expression '{expression}'.",
        )

    return current, None


def _join_with_suffix(prefix: str, suffix: str) -> str:
    """Join literal prefixes with suffixes without implicit separators.

    Args:
        prefix: Existing literal prefix.
        suffix: Expansion suffix to append.

    Returns:
        Combined literal string.
    """
    if prefix:
        return f"{prefix}{suffix}"
    return suffix


__all__ = ["expand_endpoint", "expand_pattern"]
