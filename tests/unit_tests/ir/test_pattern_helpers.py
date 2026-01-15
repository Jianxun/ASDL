import pytest

pytest.importorskip("xdsl")

from asdl.diagnostics import SourcePos, SourceSpan
from asdl.ir.patterns import (
    PatternExpressionEntry,
    PatternOrigin,
    decode_pattern_expression_table,
    decode_pattern_origin,
    decode_pattern_parts,
    encode_pattern_expression_table,
    encode_pattern_origin,
    encode_pattern_parts,
    register_pattern_expression,
    split_endpoint_atom,
)


def test_pattern_parts_roundtrip() -> None:
    parts = ["A", 2, "B"]
    attr = encode_pattern_parts(parts)

    assert decode_pattern_parts(attr) == parts


def test_pattern_origin_roundtrip() -> None:
    origin = PatternOrigin(
        expression_id="expr1",
        segment_index=1,
        base_name="N",
        pattern_parts=["A", 2],
    )

    attr = encode_pattern_origin(origin)
    decoded = decode_pattern_origin(attr)

    assert decoded == origin


def test_pattern_expression_table_roundtrip() -> None:
    span = SourceSpan(
        file="a.asdl",
        start=SourcePos(1, 2),
        end=SourcePos(1, 5),
    )
    table = {}
    expr_id = register_pattern_expression(
        table,
        expression="N<1|2>",
        kind="net",
        span=span,
    )

    encoded = encode_pattern_expression_table(table)
    decoded = decode_pattern_expression_table(encoded)

    assert decoded[expr_id] == PatternExpressionEntry(
        expression="N<1|2>",
        kind="net",
        span=span,
    )


def test_split_endpoint_atom_valid() -> None:
    assert split_endpoint_atom("U1.A") == ("U1", "A")


def test_split_endpoint_atom_invalid() -> None:
    with pytest.raises(ValueError):
        split_endpoint_atom("U1")

    with pytest.raises(ValueError):
        split_endpoint_atom("U1.A.B")

    with pytest.raises(ValueError):
        split_endpoint_atom(".A")

    with pytest.raises(ValueError):
        split_endpoint_atom("U1.")
