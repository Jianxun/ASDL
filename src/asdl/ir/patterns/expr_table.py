"""Pattern expression table helpers for GraphIR metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal, Mapping, MutableMapping, Optional

from xdsl.dialects.builtin import DictionaryAttr, IntAttr, StringAttr

from asdl.diagnostics import SourcePos, SourceSpan

PatternExpressionKind = Literal["net", "inst", "endpoint", "param"]

EXPRESSION_KEY = "expression"
KIND_KEY = "kind"
SPAN_KEY = "span"
SPAN_FILE_KEY = "file"
SPAN_START_KEY = "start"
SPAN_END_KEY = "end"
SPAN_LINE_KEY = "line"
SPAN_COL_KEY = "col"
SPAN_BYTE_START_KEY = "byte_start"
SPAN_BYTE_END_KEY = "byte_end"
EXPR_ID_PREFIX = "expr"


@dataclass(frozen=True)
class PatternExpressionEntry:
    """Pattern expression metadata for GraphIR modules.

    Attributes:
        expression: Pattern expression string.
        kind: Expression kind (net/inst/endpoint/param).
        span: Optional source span for diagnostics.
    """

    expression: str
    kind: PatternExpressionKind
    span: Optional[SourceSpan] = None


PatternExpressionTable = dict[str, PatternExpressionEntry]


def register_pattern_expression(
    table: MutableMapping[str, PatternExpressionEntry],
    *,
    expression: str,
    kind: PatternExpressionKind,
    span: Optional[SourceSpan] = None,
    expression_id: Optional[str] = None,
) -> str:
    """Register a pattern expression entry in a module-local table.

    Args:
        table: Mutable mapping of expression IDs to entries.
        expression: Pattern expression string.
        kind: Expression kind.
        span: Optional source span.
        expression_id: Optional explicit expression ID to use.

    Returns:
        The assigned expression ID.
    """
    expr_id = expression_id or _next_expression_id(table.keys())
    if expr_id in table:
        raise ValueError(f"pattern expression id '{expr_id}' already exists")
    table[expr_id] = PatternExpressionEntry(
        expression=expression,
        kind=kind,
        span=span,
    )
    return expr_id


def lookup_pattern_expression(
    table: Mapping[str, PatternExpressionEntry],
    expression_id: str,
) -> Optional[PatternExpressionEntry]:
    """Lookup a pattern expression entry by ID.

    Args:
        table: Mapping of expression IDs to entries.
        expression_id: Expression ID to look up.

    Returns:
        The matching entry or None.
    """
    return table.get(expression_id)


def encode_pattern_expression_entry(entry: PatternExpressionEntry) -> DictionaryAttr:
    """Encode a PatternExpressionEntry into a DictionaryAttr.

    Args:
        entry: PatternExpressionEntry to encode.

    Returns:
        DictionaryAttr with expression metadata.
    """
    payload = {
        EXPRESSION_KEY: StringAttr(entry.expression),
        KIND_KEY: StringAttr(entry.kind),
    }
    if entry.span is not None:
        payload[SPAN_KEY] = _encode_source_span(entry.span)
    return DictionaryAttr(payload)


def decode_pattern_expression_entry(entry: DictionaryAttr) -> PatternExpressionEntry:
    """Decode a DictionaryAttr into a PatternExpressionEntry.

    Args:
        entry: DictionaryAttr payload.

    Returns:
        PatternExpressionEntry with decoded metadata.
    """
    if not isinstance(entry, DictionaryAttr):
        raise TypeError(f"pattern expression entry must be DictionaryAttr, got {type(entry)!r}")
    expression_attr = entry.data.get(EXPRESSION_KEY)
    kind_attr = entry.data.get(KIND_KEY)
    if not isinstance(expression_attr, StringAttr):
        raise TypeError("pattern expression entry requires string expression")
    if not isinstance(kind_attr, StringAttr):
        raise TypeError("pattern expression entry requires string kind")
    kind_value = kind_attr.data
    if kind_value not in ("net", "inst", "endpoint", "param"):
        raise ValueError(f"Unsupported pattern expression kind '{kind_value}'")
    span = None
    span_attr = entry.data.get(SPAN_KEY)
    if span_attr is not None:
        span = _decode_source_span(span_attr)
    return PatternExpressionEntry(
        expression=expression_attr.data,
        kind=kind_value,
        span=span,
    )


def encode_pattern_expression_table(table: Mapping[str, PatternExpressionEntry]) -> DictionaryAttr:
    """Encode a pattern expression table into a DictionaryAttr.

    Args:
        table: Mapping of expression IDs to entries.

    Returns:
        DictionaryAttr mapping expression IDs to encoded entries.
    """
    return DictionaryAttr(
        {expr_id: encode_pattern_expression_entry(entry) for expr_id, entry in table.items()}
    )


def decode_pattern_expression_table(table: DictionaryAttr) -> PatternExpressionTable:
    """Decode a DictionaryAttr into a pattern expression table.

    Args:
        table: DictionaryAttr mapping expression IDs to entry payloads.

    Returns:
        Decoded mapping of expression IDs to entries.
    """
    if not isinstance(table, DictionaryAttr):
        raise TypeError(f"pattern expression table must be DictionaryAttr, got {type(table)!r}")
    decoded: PatternExpressionTable = {}
    for expr_id, entry in table.data.items():
        decoded[expr_id] = decode_pattern_expression_entry(entry)
    return decoded


def _encode_source_span(span: SourceSpan) -> DictionaryAttr:
    payload = {
        SPAN_FILE_KEY: StringAttr(span.file),
        SPAN_START_KEY: DictionaryAttr(
            {
                SPAN_LINE_KEY: IntAttr(span.start.line),
                SPAN_COL_KEY: IntAttr(span.start.col),
            }
        ),
        SPAN_END_KEY: DictionaryAttr(
            {
                SPAN_LINE_KEY: IntAttr(span.end.line),
                SPAN_COL_KEY: IntAttr(span.end.col),
            }
        ),
    }
    if span.byte_start is not None:
        payload[SPAN_BYTE_START_KEY] = IntAttr(span.byte_start)
    if span.byte_end is not None:
        payload[SPAN_BYTE_END_KEY] = IntAttr(span.byte_end)
    return DictionaryAttr(payload)


def _decode_source_span(span: object) -> SourceSpan:
    if not isinstance(span, DictionaryAttr):
        raise TypeError(f"span must be DictionaryAttr, got {type(span)!r}")
    file_attr = span.data.get(SPAN_FILE_KEY)
    start_attr = span.data.get(SPAN_START_KEY)
    end_attr = span.data.get(SPAN_END_KEY)
    if not isinstance(file_attr, StringAttr):
        raise TypeError("span.file must be a string")
    start = _decode_span_pos(start_attr, "start")
    end = _decode_span_pos(end_attr, "end")
    byte_start = _decode_optional_int(span.data.get(SPAN_BYTE_START_KEY), "byte_start")
    byte_end = _decode_optional_int(span.data.get(SPAN_BYTE_END_KEY), "byte_end")
    return SourceSpan(
        file=file_attr.data,
        start=start,
        end=end,
        byte_start=byte_start,
        byte_end=byte_end,
    )


def _decode_span_pos(attr: object, label: str) -> SourcePos:
    if not isinstance(attr, DictionaryAttr):
        raise TypeError(f"span.{label} must be a dictionary")
    line_attr = attr.data.get(SPAN_LINE_KEY)
    col_attr = attr.data.get(SPAN_COL_KEY)
    if not isinstance(line_attr, IntAttr) or not isinstance(col_attr, IntAttr):
        raise TypeError(f"span.{label} must include integer line/col")
    return SourcePos(line_attr.data, col_attr.data)


def _decode_optional_int(attr: object, label: str) -> Optional[int]:
    if attr is None:
        return None
    if not isinstance(attr, IntAttr):
        raise TypeError(f"span.{label} must be an integer")
    return attr.data


def _next_expression_id(existing: Iterable[str]) -> str:
    index = 1
    existing_set = set(existing)
    while True:
        candidate = f"{EXPR_ID_PREFIX}{index}"
        if candidate not in existing_set:
            return candidate
        index += 1


__all__ = [
    "PatternExpressionEntry",
    "PatternExpressionKind",
    "PatternExpressionTable",
    "decode_pattern_expression_entry",
    "decode_pattern_expression_table",
    "encode_pattern_expression_entry",
    "encode_pattern_expression_table",
    "lookup_pattern_expression",
    "register_pattern_expression",
]
