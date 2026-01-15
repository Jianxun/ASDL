"""Pattern atomization routines for IR pattern expressions."""

from __future__ import annotations

from dataclasses import dataclass
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
from .parts import PatternPart
from .tokenize import (
    _find_duplicates,
    _has_whitespace,
    _range_values,
    _split_splice_segments,
    _tokenize_segment,
)


@dataclass(frozen=True)
class AtomizedPattern:
    """Single atomized pattern expression with provenance data.

    Attributes:
        literal: Expanded literal atom.
        segment_index: 0-based segment index within the expression.
        base_name: Literal portion of the pattern segment.
        pattern_parts: Ordered substitution values used for this atom.
    """

    literal: str
    segment_index: int
    base_name: str
    pattern_parts: list[PatternPart]


@dataclass(frozen=True)
class AtomizedEndpoint:
    """Atomized endpoint derived from a pattern expression."""

    inst: str
    port: str
    segment_index: int
    base_name: str
    pattern_parts: list[PatternPart]


def atomize_pattern(
    expression: str,
    *,
    max_atoms: int = MAX_EXPANSION_SIZE,
    allow_splice: bool = True,
) -> Tuple[Optional[List[AtomizedPattern]], List[Diagnostic]]:
    """Atomize a pattern expression into annotated atoms.

    Args:
        expression: Pattern expression to atomize.
        max_atoms: Maximum expansion size before aborting.
        allow_splice: Whether to allow splice delimiters in the expression.

    Returns:
        Tuple of (atomized patterns or None, diagnostics).
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

    atoms: List[AtomizedPattern] = []
    for segment_index, segment in enumerate(segments):
        segment_atoms, base_name, diag = _atomize_segment(segment, expression, max_atoms)
        if diag is not None:
            return None, [diag]
        if len(atoms) + len(segment_atoms) > max_atoms:
            return None, [_diagnostic(PATTERN_TOO_LARGE, _too_large_message(expression, max_atoms))]
        atoms.extend(
            AtomizedPattern(
                literal=literal,
                segment_index=segment_index,
                base_name=base_name,
                pattern_parts=parts,
            )
            for literal, parts in segment_atoms
        )

    duplicates = _find_duplicates(atom.literal for atom in atoms)
    if duplicates:
        return None, [_diagnostic(PATTERN_DUPLICATE_ATOM, _duplicate_message(duplicates, expression))]

    return atoms, diagnostics


def atomize_endpoint(
    inst: str,
    port: str,
    *,
    max_atoms: int = MAX_EXPANSION_SIZE,
    allow_splice: bool = True,
) -> Tuple[Optional[List[AtomizedEndpoint]], List[Diagnostic]]:
    """Atomize instance and port tokens into endpoint atoms.

    Atomization is performed on the full endpoint expression before splitting
    on '.' for each expanded atom.

    Args:
        inst: Instance token to atomize.
        port: Port token to atomize.
        max_atoms: Maximum expansion size before aborting.
        allow_splice: Whether to allow splice delimiters in the expression.

    Returns:
        Tuple of (atomized endpoints or None, diagnostics).
    """
    expression = f"{inst}.{port}"
    atoms, diagnostics = atomize_pattern(
        expression,
        max_atoms=max_atoms,
        allow_splice=allow_splice,
    )
    if atoms is None:
        return None, diagnostics

    endpoints: List[AtomizedEndpoint] = []
    for atom in atoms:
        try:
            inst_name, port_name = split_endpoint_atom(atom.literal)
        except ValueError:
            return None, [
                _diagnostic(
                    PATTERN_UNEXPANDED,
                    (
                        f"Endpoint pattern expression '{expression}' expands to "
                        f"invalid atom '{atom.literal}'."
                    ),
                )
            ]
        endpoints.append(
            AtomizedEndpoint(
                inst=inst_name,
                port=port_name,
                segment_index=atom.segment_index,
                base_name=atom.base_name,
                pattern_parts=atom.pattern_parts,
            )
        )

    return endpoints, diagnostics


def _atomize_segment(
    segment: str, expression: str, max_atoms: int
) -> Tuple[Optional[List[Tuple[str, list[PatternPart]]]], Optional[str], Optional[Diagnostic]]:
    """Atomize a splice-free segment into literal/pattern part pairs.

    Args:
        segment: Pattern segment without splice delimiters.
        expression: Original pattern expression for diagnostics.
        max_atoms: Maximum expansion size before aborting.

    Returns:
        Tuple of (segment atoms or None, base name, diagnostic).
    """
    if _has_whitespace(segment):
        return None, None, _diagnostic(
            PATTERN_UNEXPANDED,
            f"Whitespace is not allowed in pattern expression '{expression}'.",
        )

    tokens, diag = _tokenize_segment(segment, expression)
    if diag is not None:
        return None, None, diag

    base_name = "".join(payload for kind, payload in tokens if kind == "literal")

    current: List[Tuple[str, list[PatternPart]]] = [("", [])]
    for kind, payload in tokens:
        if kind == "literal":
            current = [(value + payload, parts) for value, parts in current]
            continue

        if kind == "enum":
            alts = payload
            next_size = len(current) * len(alts)
            if next_size > max_atoms:
                return None, None, _diagnostic(
                    PATTERN_TOO_LARGE,
                    _too_large_message(expression, max_atoms),
                )
            current = [
                (value + alt, [*parts, alt])
                for value, parts in current
                for alt in alts
            ]
            continue

        if kind == "range":
            start, end = payload
            value_count = abs(end - start) + 1
            next_size = len(current) * value_count
            if next_size > max_atoms:
                return None, None, _diagnostic(
                    PATTERN_TOO_LARGE,
                    _too_large_message(expression, max_atoms),
                )
            current = [
                (value + str(atom), [*parts, atom])
                for value, parts in current
                for atom in _range_values(start, end)
            ]
            continue

        return None, None, _diagnostic(
            PATTERN_UNEXPANDED,
            f"Unhandled pattern expression '{expression}'.",
        )

    return current, base_name, None


__all__ = ["AtomizedEndpoint", "AtomizedPattern", "atomize_endpoint", "atomize_pattern"]
