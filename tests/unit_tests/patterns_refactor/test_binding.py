from __future__ import annotations

from asdl.patterns_refactor import (
    AxisSpec,
    NamedPattern,
    PatternExpr,
    PatternGroup,
    PatternLiteral,
    PatternSegment,
    bind_patterns,
    expand_endpoint,
    expand_pattern,
    parse_pattern_expr,
)


def test_expand_flattens_splice_segments() -> None:
    expr, errors = parse_pattern_expr("A<0|1>;B<2|3>")
    assert errors == []

    expanded, errors = expand_pattern(expr)
    assert errors == []
    assert expanded == ["A0", "A1", "B2", "B3"]


def test_expand_endpoint_splits_atoms() -> None:
    expr, errors = parse_pattern_expr("U<0|1>.P<0|1>")
    assert errors == []

    endpoints, errors = expand_endpoint(expr)
    assert errors == []
    assert endpoints == [
        ("U0", "P0"),
        ("U0", "P1"),
        ("U1", "P0"),
        ("U1", "P1"),
    ]


def test_bind_axis_size_mismatch_reports_error() -> None:
    named_patterns = {
        "BUS": NamedPattern(expr="<0|1>", tag="bit"),
        "WIDE": NamedPattern(expr="<0|1|2>", tag="bit"),
    }
    net_expr, errors = parse_pattern_expr("NET<@BUS>", named_patterns=named_patterns)
    assert errors == []
    endpoint_expr, errors = parse_pattern_expr(
        "U<@WIDE>.P",
        named_patterns=named_patterns,
    )
    assert errors == []

    plan, errors = bind_patterns(
        net_expr,
        endpoint_expr,
        net_expr_id="net",
        endpoint_expr_id="endpoint",
    )
    assert plan is None
    assert errors
    assert "axis" in errors[0].message.lower()


def test_bind_disallows_broadcast_with_splice() -> None:
    named_patterns = {
        "BUS": NamedPattern(expr="<0|1>", tag="bit"),
    }
    net_expr, errors = parse_pattern_expr("NET<@BUS>;EXTRA", named_patterns=named_patterns)
    assert errors == []
    endpoint_expr, errors = parse_pattern_expr(
        "U<@BUS>.P",
        named_patterns=named_patterns,
    )
    assert errors == []

    plan, errors = bind_patterns(
        net_expr,
        endpoint_expr,
        net_expr_id="net",
        endpoint_expr_id="endpoint",
    )
    assert plan is None
    assert errors
    assert "splice" in errors[0].message.lower()


def test_bind_rejects_axis_size_product_mismatch() -> None:
    net_expr = PatternExpr(
        raw="NET<@A>",
        segments=[
            PatternSegment(
                tokens=[
                    PatternLiteral("NET"),
                    PatternGroup(kind="enum", labels=[0, 1], axis_id="a"),
                ]
            )
        ],
        axes=[AxisSpec(axis_id="a", kind="enum", labels=[0, 1], size=2, order=0)],
        axis_order=["a"],
    )
    endpoint_expr = PatternExpr(
        raw="U<@A>.P<@B>",
        segments=[
            PatternSegment(
                tokens=[
                    PatternLiteral("U"),
                    PatternGroup(kind="enum", labels=[0, 1, 2], axis_id="a"),
                    PatternLiteral(".P"),
                    PatternGroup(kind="enum", labels=["X"], axis_id="b"),
                ]
            )
        ],
        axes=[
            AxisSpec(axis_id="a", kind="enum", labels=[0, 1], size=2, order=0),
            AxisSpec(axis_id="b", kind="enum", labels=[0, 1], size=2, order=1),
        ],
        axis_order=["a", "b"],
    )

    plan, errors = bind_patterns(
        net_expr,
        endpoint_expr,
        net_expr_id="net",
        endpoint_expr_id="endpoint",
    )
    assert plan is None
    assert errors
    assert "axis-size" in errors[0].message.lower()
