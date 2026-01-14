"""Pattern expansion routines."""

from __future__ import annotations

from typing import List, Optional, Tuple

from ..diagnostics import Diagnostic
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
from .tokenize import (
    _find_duplicates,
    _has_whitespace,
    _range_values,
    _split_splice_segments,
    _tokenize_segment,
)


def expand_pattern(
    token: str, *, max_atoms: int = MAX_EXPANSION_SIZE
) -> Tuple[Optional[List[str]], List[Diagnostic]]:
    """Expand a pattern token into its literal atom list.

    Args:
        token: Pattern token to expand.
        max_atoms: Maximum expansion size before aborting.

    Returns:
        Tuple of (atoms or None, diagnostics).
    """
    diagnostics: List[Diagnostic] = []
    if not token:
        diagnostics.append(_diagnostic(PATTERN_UNEXPANDED, "Pattern token is empty."))
        return None, diagnostics

    segments, diag = _split_splice_segments(token)
    if diag is not None:
        return None, [diag]
    if any(segment == "" for segment in segments):
        return None, [_diagnostic(PATTERN_EMPTY_SPLICE, _empty_splice_message(token))]

    expanded: List[str] = []
    for segment in segments:
        segment_expansion, diag = _expand_segment(segment, token, max_atoms)
        if diag is not None:
            return None, [diag]
        if len(expanded) + len(segment_expansion) > max_atoms:
            return None, [_diagnostic(PATTERN_TOO_LARGE, _too_large_message(token, max_atoms))]
        expanded.extend(segment_expansion)

    duplicates = _find_duplicates(expanded)
    if duplicates:
        return None, [_diagnostic(PATTERN_DUPLICATE_ATOM, _duplicate_message(duplicates, token))]

    return expanded, diagnostics


def expand_endpoint(
    inst: str, pin: str, *, max_atoms: int = MAX_EXPANSION_SIZE
) -> Tuple[Optional[List[Tuple[str, str]]], List[Diagnostic]]:
    """Expand instance and pin tokens into the endpoint cross-product.

    Args:
        inst: Instance token to expand.
        pin: Pin token to expand.
        max_atoms: Maximum expansion size before aborting.

    Returns:
        Tuple of (endpoint tuples or None, diagnostics).
    """
    token = f"{inst}.{pin}"
    inst_expanded, inst_diags = expand_pattern(inst, max_atoms=max_atoms)
    if inst_expanded is None:
        return None, inst_diags
    pin_expanded, pin_diags = expand_pattern(pin, max_atoms=max_atoms)
    diagnostics = [*inst_diags, *pin_diags]
    if pin_expanded is None:
        return None, diagnostics

    product_size = len(inst_expanded) * len(pin_expanded)
    if product_size > max_atoms:
        diagnostics.append(
            _diagnostic(
                PATTERN_TOO_LARGE,
                _too_large_message(token, max_atoms),
            )
        )
        return None, diagnostics

    endpoints: List[Tuple[str, str]] = []
    for inst_atom in inst_expanded:
        for pin_atom in pin_expanded:
            endpoints.append((inst_atom, pin_atom))

    return endpoints, diagnostics


def _expand_segment(
    segment: str, token: str, max_atoms: int
) -> Tuple[Optional[List[str]], Optional[Diagnostic]]:
    """Expand a single splice-free segment of a pattern token.

    Args:
        segment: Pattern segment without splice delimiters.
        token: Original pattern token for diagnostics.
        max_atoms: Maximum expansion size before aborting.

    Returns:
        Tuple of (segment expansion or None, diagnostic).
    """
    if _has_whitespace(segment):
        return None, _diagnostic(
            PATTERN_UNEXPANDED,
            f"Whitespace is not allowed in pattern token '{token}'.",
        )

    tokens, diag = _tokenize_segment(segment, token)
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
                return None, _diagnostic(PATTERN_TOO_LARGE, _too_large_message(token, max_atoms))
            current = [_join_with_suffix(prefix, suffix) for prefix in current for suffix in alts]
            continue

        if kind == "range":
            start, end = payload
            value_count = abs(end - start) + 1
            next_size = len(current) * value_count
            if next_size > max_atoms:
                return None, _diagnostic(PATTERN_TOO_LARGE, _too_large_message(token, max_atoms))
            current = [
                _join_with_suffix(prefix, str(value))
                for prefix in current
                for value in _range_values(start, end)
            ]
            continue

        return None, _diagnostic(
            PATTERN_UNEXPANDED,
            f"Unhandled pattern token '{token}'.",
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
