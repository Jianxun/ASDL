"""Pattern helpers for ASDL IR."""

from .atomize import AtomizedEndpoint, AtomizedPattern, atomize_endpoint, atomize_pattern
from .diagnostics import (
    MAX_EXPANSION_SIZE,
    PATTERN_DUPLICATE_ATOM,
    PATTERN_EMPTY_ENUM,
    PATTERN_EMPTY_SPLICE,
    PATTERN_INVALID_RANGE,
    PATTERN_TOO_LARGE,
    PATTERN_UNEXPANDED,
)
from .expand import expand_endpoint, expand_pattern
from .endpoint_split import split_endpoint_atom
from .expr_table import (
    PatternExpressionEntry,
    PatternExpressionKind,
    PatternExpressionTable,
    decode_pattern_expression_entry,
    decode_pattern_expression_table,
    encode_pattern_expression_entry,
    encode_pattern_expression_table,
    lookup_pattern_expression,
    register_pattern_expression,
)
from .origin import PatternOrigin, decode_pattern_origin, encode_pattern_origin
from .parts import (
    PatternPart,
    PatternPartInput,
    PatternPartsInput,
    decode_pattern_parts,
    encode_pattern_parts,
    normalize_pattern_parts,
)

__all__ = [
    "AtomizedEndpoint",
    "AtomizedPattern",
    "MAX_EXPANSION_SIZE",
    "PATTERN_DUPLICATE_ATOM",
    "PATTERN_EMPTY_ENUM",
    "PATTERN_EMPTY_SPLICE",
    "PATTERN_INVALID_RANGE",
    "PATTERN_TOO_LARGE",
    "PATTERN_UNEXPANDED",
    "PatternExpressionEntry",
    "PatternExpressionKind",
    "PatternExpressionTable",
    "PatternOrigin",
    "PatternPart",
    "PatternPartInput",
    "PatternPartsInput",
    "decode_pattern_expression_entry",
    "decode_pattern_expression_table",
    "decode_pattern_origin",
    "decode_pattern_parts",
    "encode_pattern_expression_entry",
    "encode_pattern_expression_table",
    "encode_pattern_origin",
    "encode_pattern_parts",
    "expand_endpoint",
    "expand_pattern",
    "lookup_pattern_expression",
    "normalize_pattern_parts",
    "register_pattern_expression",
    "split_endpoint_atom",
    "atomize_endpoint",
    "atomize_pattern",
]
