"""Pattern atomization routines."""

from __future__ import annotations

from dataclasses import dataclass
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
    _has_pattern_delimiters,
    _has_whitespace,
    _range_values,
    _split_splice_segments,
    _tokenize_segment,
)


@dataclass(frozen=True)
class AtomizedPattern:
    """Single atomized pattern token representation.

    Attributes:
        token: Pattern token for the atomized value.
        literal: Literal expansion for the atomized value.
        origin: Original pattern token when atomized from a pattern.
    """

    token: str
    literal: str
    origin: Optional[str] = None


@dataclass(frozen=True)
class AtomizedEndpoint:
    """Atomized instance/pin pair for endpoints."""

    inst: AtomizedPattern
    pin: AtomizedPattern


def atomize_pattern(
    token: str, *, max_atoms: int = MAX_EXPANSION_SIZE
) -> Tuple[Optional[List[AtomizedPattern]], List[Diagnostic]]:
    """Atomize a pattern token into annotated pattern atoms.

    Args:
        token: Pattern token to atomize.
        max_atoms: Maximum expansion size before aborting.

    Returns:
        Tuple of (atomized patterns or None, diagnostics).
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

    atoms: List[Tuple[str, str]] = []
    for segment in segments:
        segment_atoms, diag = _atomize_segment(segment, token, max_atoms)
        if diag is not None:
            return None, [diag]
        if len(atoms) + len(segment_atoms) > max_atoms:
            return None, [_diagnostic(PATTERN_TOO_LARGE, _too_large_message(token, max_atoms))]
        atoms.extend(segment_atoms)

    duplicates = _find_duplicates(literal for _, literal in atoms)
    if duplicates:
        return None, [_diagnostic(PATTERN_DUPLICATE_ATOM, _duplicate_message(duplicates, token))]

    origin = token if _has_pattern_delimiters(token) else None
    return [
        AtomizedPattern(token=atom_token, literal=literal, origin=origin)
        for atom_token, literal in atoms
    ], diagnostics


def atomize_endpoint(
    inst: str, pin: str, *, max_atoms: int = MAX_EXPANSION_SIZE
) -> Tuple[Optional[List[AtomizedEndpoint]], List[Diagnostic]]:
    """Atomize instance/pin patterns into endpoint atoms.

    Args:
        inst: Instance token to atomize.
        pin: Pin token to atomize.
        max_atoms: Maximum expansion size before aborting.

    Returns:
        Tuple of (atomized endpoints or None, diagnostics).
    """
    token = f"{inst}.{pin}"
    inst_atoms, inst_diags = atomize_pattern(inst, max_atoms=max_atoms)
    if inst_atoms is None:
        return None, inst_diags
    pin_atoms, pin_diags = atomize_pattern(pin, max_atoms=max_atoms)
    diagnostics = [*inst_diags, *pin_diags]
    if pin_atoms is None:
        return None, diagnostics

    product_size = len(inst_atoms) * len(pin_atoms)
    if product_size > max_atoms:
        diagnostics.append(_diagnostic(PATTERN_TOO_LARGE, _too_large_message(token, max_atoms)))
        return None, diagnostics

    endpoints: List[AtomizedEndpoint] = []
    for inst_atom in inst_atoms:
        for pin_atom in pin_atoms:
            endpoints.append(AtomizedEndpoint(inst=inst_atom, pin=pin_atom))

    return endpoints, diagnostics


def _atomize_segment(
    segment: str, token: str, max_atoms: int
) -> Tuple[Optional[List[Tuple[str, str]]], Optional[Diagnostic]]:
    """Atomize a splice-free segment into pattern token/literal pairs.

    Args:
        segment: Pattern segment without splice delimiters.
        token: Original pattern token for diagnostics.
        max_atoms: Maximum expansion size before aborting.

    Returns:
        Tuple of (segment atoms or None, diagnostic).
    """
    if _has_whitespace(segment):
        return None, _diagnostic(
            PATTERN_UNEXPANDED,
            f"Whitespace is not allowed in pattern token '{token}'.",
        )

    tokens, diag = _tokenize_segment(segment, token)
    if diag is not None:
        return None, diag

    current: List[Tuple[str, str]] = [("", "")]
    for kind, payload in tokens:
        if kind == "literal":
            current = [(value + payload, literal + payload) for value, literal in current]
            continue

        if kind == "enum":
            alts = payload
            next_size = len(current) * len(alts)
            if next_size > max_atoms:
                return None, _diagnostic(PATTERN_TOO_LARGE, _too_large_message(token, max_atoms))
            current = [
                (value + f"<{alt}>", literal + alt)
                for value, literal in current
                for alt in alts
            ]
            continue

        if kind == "range":
            start, end = payload
            value_count = abs(end - start) + 1
            next_size = len(current) * value_count
            if next_size > max_atoms:
                return None, _diagnostic(PATTERN_TOO_LARGE, _too_large_message(token, max_atoms))
            current = [
                (value + _format_range_atom(atom), literal + str(atom))
                for value, literal in current
                for atom in _range_values(start, end)
            ]
            continue

        return None, _diagnostic(
            PATTERN_UNEXPANDED,
            f"Unhandled pattern token '{token}'.",
        )

    return current, None


def _format_range_atom(value: int) -> str:
    """Format a single numeric atom as a closed range token.

    Args:
        value: Numeric value for the range atom.

    Returns:
        Range token string for the atom.
    """
    return f"[{value}:{value}]"
