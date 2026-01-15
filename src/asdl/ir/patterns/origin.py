"""Pattern origin helpers for GraphIR metadata."""

from __future__ import annotations

from dataclasses import dataclass

from xdsl.dialects.builtin import IntAttr, StringAttr

from asdl.ir.graphir.attrs import GraphPatternOriginAttr

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


__all__ = ["PatternOrigin", "decode_pattern_origin", "encode_pattern_origin"]
