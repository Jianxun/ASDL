"""Pattern part encoding helpers for GraphIR metadata."""

from __future__ import annotations

from typing import Iterable, Sequence

from xdsl.dialects.builtin import ArrayAttr, IntAttr, StringAttr
from xdsl.ir import Attribute

PatternPart = str | int
PatternPartAttr = StringAttr | IntAttr
PatternPartInput = PatternPart | PatternPartAttr
PatternPartsInput = Sequence[PatternPartInput] | ArrayAttr


def normalize_pattern_parts(parts: PatternPartsInput) -> list[PatternPart]:
    """Normalize pattern parts to native Python values.

    Args:
        parts: Sequence or ArrayAttr containing string/integer parts.

    Returns:
        List of normalized pattern parts.
    """
    if isinstance(parts, ArrayAttr):
        return [_normalize_part(item) for item in parts.data]
    return [_normalize_part(item) for item in parts]


def encode_pattern_parts(parts: PatternPartsInput) -> ArrayAttr:
    """Encode pattern parts into an ArrayAttr.

    Args:
        parts: Sequence or ArrayAttr of pattern parts.

    Returns:
        ArrayAttr containing StringAttr/IntAttr entries.
    """
    normalized = normalize_pattern_parts(parts)
    attrs: list[Attribute] = []
    for part in normalized:
        if isinstance(part, str):
            attrs.append(StringAttr(part))
        else:
            attrs.append(IntAttr(part))
    return ArrayAttr(attrs)


def decode_pattern_parts(parts: ArrayAttr) -> list[PatternPart]:
    """Decode an ArrayAttr into native pattern parts.

    Args:
        parts: ArrayAttr containing pattern parts.

    Returns:
        List of string/integer pattern parts.
    """
    if not isinstance(parts, ArrayAttr):
        raise TypeError(f"pattern parts must be ArrayAttr, got {type(parts)!r}")
    return normalize_pattern_parts(parts)


def _normalize_part(value: PatternPartInput) -> PatternPart:
    """Normalize a single pattern part input.

    Args:
        value: Pattern part input value.

    Returns:
        Normalized string or integer pattern part.
    """
    if isinstance(value, bool):
        raise TypeError("pattern parts must be strings or integers, not bool")
    if isinstance(value, StringAttr):
        return value.data
    if isinstance(value, IntAttr):
        return value.data
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return value
    raise TypeError(f"Unsupported pattern part: {value!r}")


__all__ = [
    "PatternPart",
    "PatternPartInput",
    "PatternPartsInput",
    "decode_pattern_parts",
    "encode_pattern_parts",
    "normalize_pattern_parts",
]
