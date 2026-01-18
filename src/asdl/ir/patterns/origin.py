"""Pattern origin helpers for GraphIR metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from xdsl.dialects.builtin import IntAttr, StringAttr

from asdl.ir.graphir.attrs import GraphPatternOriginAttr

from .expr_table import PatternExpressionEntry
from .parts import PatternPart, decode_pattern_parts, encode_pattern_parts


@dataclass(frozen=True)
class PatternOrigin:
    """Pattern provenance metadata for an atomized GraphIR name.

    Attributes:
        expression_id: Pattern expression table key.
        segment_index: 0-based segment index within the expression.
        base_name: Base name for the pattern.
        pattern_parts: Ordered list of string/integer substitutions.
    """

    expression_id: str
    segment_index: int
    base_name: str
    pattern_parts: list[PatternPart]


def encode_pattern_origin(origin: PatternOrigin | GraphPatternOriginAttr) -> GraphPatternOriginAttr:
    """Encode a PatternOrigin into a GraphPatternOriginAttr.

    Args:
        origin: PatternOrigin or already-encoded GraphPatternOriginAttr.

    Returns:
        GraphPatternOriginAttr instance.
    """
    if isinstance(origin, GraphPatternOriginAttr):
        return origin
    if not isinstance(origin, PatternOrigin):
        raise TypeError(f"Unsupported pattern origin: {origin!r}")
    if isinstance(origin.segment_index, bool):
        raise TypeError("segment_index must be an integer")
    return GraphPatternOriginAttr(
        StringAttr(origin.expression_id),
        IntAttr(origin.segment_index),
        StringAttr(origin.base_name),
        encode_pattern_parts(origin.pattern_parts),
    )


def decode_pattern_origin(origin: GraphPatternOriginAttr) -> PatternOrigin:
    """Decode a GraphPatternOriginAttr into a PatternOrigin.

    Args:
        origin: GraphPatternOriginAttr to decode.

    Returns:
        PatternOrigin dataclass instance.
    """
    if not isinstance(origin, GraphPatternOriginAttr):
        raise TypeError(f"Expected GraphPatternOriginAttr, got {type(origin)!r}")
    return PatternOrigin(
        expression_id=origin.expression_id.data,
        segment_index=origin.segment_index.data,
        base_name=origin.base_name.data,
        pattern_parts=decode_pattern_parts(origin.pattern_parts),
    )


def render_pattern_origin(
    origin: PatternOrigin | GraphPatternOriginAttr,
    *,
    pattern_rendering: str = "{N}",
) -> str:
    """Render a pattern-derived name using numeric formatting policy.

    Args:
        origin: Pattern origin metadata to render.
        pattern_rendering: Format string for numeric parts using "{N}".

    Returns:
        Rendered name string.
    """
    normalized = (
        origin if isinstance(origin, PatternOrigin) else decode_pattern_origin(origin)
    )
    rendered_parts: list[str] = []
    for part in normalized.pattern_parts:
        if isinstance(part, int):
            rendered_parts.append(_render_numeric_part(part, pattern_rendering))
        else:
            rendered_parts.append(str(part))
    return f"{normalized.base_name}{''.join(rendered_parts)}"


def _render_numeric_part(value: int, pattern_rendering: str) -> str:
    """Render a numeric pattern part using the backend formatting policy.

    Args:
        value: Numeric pattern part to render.
        pattern_rendering: Format string containing "{N}" for numeric values.

    Returns:
        Rendered numeric string.
    """
    if not isinstance(pattern_rendering, str):
        return str(value)
    if "{N" not in pattern_rendering:
        return str(value)
    try:
        return pattern_rendering.format_map({"N": value})
    except (KeyError, ValueError):
        return str(value)


def lookup_pattern_origin_entry(
    origin: GraphPatternOriginAttr,
    table: Mapping[str, PatternExpressionEntry],
) -> PatternExpressionEntry:
    """Lookup the pattern expression entry for a GraphPatternOriginAttr.

    Args:
        origin: GraphPatternOriginAttr with the expression ID to resolve.
        table: Mapping of expression IDs to expression table entries.

    Returns:
        The matching PatternExpressionEntry.

    Raises:
        KeyError: If the expression ID is not present in the table.
        TypeError: If origin is not a GraphPatternOriginAttr.
    """
    if not isinstance(origin, GraphPatternOriginAttr):
        raise TypeError(f"Expected GraphPatternOriginAttr, got {type(origin)!r}")
    entry = table.get(origin.expression_id.data)
    if entry is None:
        raise KeyError(
            f"pattern expression id '{origin.expression_id.data}' is not in the table"
        )
    return entry


__all__ = [
    "PatternOrigin",
    "decode_pattern_origin",
    "encode_pattern_origin",
    "lookup_pattern_origin_entry",
    "render_pattern_origin",
]
