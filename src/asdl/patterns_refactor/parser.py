"""Parse pattern expressions for the refactor pattern service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal, Mapping, Optional, Sequence

from asdl.diagnostics import SourceSpan


@dataclass(frozen=True)
class PatternError:
    """Pattern parsing/expansion error payload.

    Attributes:
        message: Human-readable error description.
        span: Optional source span for the error.
    """

    message: str
    span: Optional[SourceSpan] = None


@dataclass(frozen=True)
class NamedPattern:
    """Named pattern definition with an optional axis tag.

    Attributes:
        expr: Group token string (ex: "<0|1>") for the named pattern.
        tag: Optional axis tag identifier.
    """

    expr: str
    tag: Optional[str] = None


@dataclass(frozen=True)
class PatternLiteral:
    """Literal token inside a pattern segment.

    Attributes:
        text: Literal text to append during expansion.
        span: Optional source span for the token.
    """

    text: str
    span: Optional[SourceSpan] = None


@dataclass(frozen=True)
class PatternGroup:
    """Pattern group token with optional axis metadata.

    Attributes:
        kind: Group kind (enum or range).
        labels: Ordered expansion labels for the group.
        axis_id: Optional axis identifier for named-axis broadcast.
        span: Optional source span for the token.
    """

    kind: Literal["enum", "range"]
    labels: list[str | int]
    axis_id: Optional[str] = None
    span: Optional[SourceSpan] = None


PatternToken = PatternLiteral | PatternGroup


@dataclass(frozen=True)
class PatternSegment:
    """Segment of a pattern expression split on splice delimiters.

    Attributes:
        tokens: Ordered tokens within the segment.
        span: Optional source span for the segment.
    """

    tokens: list[PatternToken]
    span: Optional[SourceSpan] = None


@dataclass(frozen=True)
class AxisSpec:
    """Metadata for a named axis in a pattern expression.

    Attributes:
        axis_id: Axis identifier (tag or pattern name).
        kind: Axis kind (enum or range).
        labels: Ordered labels for the axis.
        size: Number of labels in the axis.
        order: Left-to-right axis order index.
    """

    axis_id: str
    kind: Literal["enum", "range"]
    labels: list[str | int]
    size: int
    order: int


@dataclass(frozen=True)
class PatternExpr:
    """Parsed pattern expression with axis metadata.

    Attributes:
        raw: Original expression string.
        segments: Parsed pattern segments.
        axes: Axis metadata for named group tokens.
        axis_order: Ordered axis identifiers.
        span: Optional source span for the expression.
    """

    raw: str
    segments: list[PatternSegment]
    axes: list[AxisSpec]
    axis_order: list[str]
    span: Optional[SourceSpan] = None


def parse_pattern_expr(
    expression: str,
    *,
    named_patterns: Optional[Mapping[str, NamedPattern | str]] = None,
    span: Optional[SourceSpan] = None,
) -> tuple[Optional[PatternExpr], list[PatternError]]:
    """Parse a pattern expression into structured segments and tokens.

    Args:
        expression: Raw pattern expression string.
        named_patterns: Optional named pattern definitions for <@name> references.
        span: Optional source span for the full expression.

    Returns:
        Tuple of (PatternExpr or None, errors).
    """
    if expression == "":
        return None, [PatternError("Pattern expression is empty.", span)]

    pattern_map = _normalize_named_patterns(named_patterns)
    tokens: list[PatternToken] = []
    segments: list[PatternSegment] = []
    axis_specs: list[AxisSpec] = []
    axis_order: list[str] = []
    axis_ids: set[str] = set()
    literal_buffer: list[str] = []

    def flush_literal() -> None:
        if literal_buffer:
            tokens.append(PatternLiteral("".join(literal_buffer)))
            literal_buffer.clear()

    index = 0
    while index < len(expression):
        char = expression[index]
        if char == ";":
            flush_literal()
            if not tokens:
                return None, [
                    PatternError(
                        f"Empty splice segment in pattern expression '{expression}'.",
                        span,
                    )
                ]
            segments.append(PatternSegment(tokens=list(tokens)))
            tokens.clear()
            index += 1
            continue

        if char == "<":
            flush_literal()
            close = expression.find(">", index + 1)
            if close == -1:
                return None, [
                    PatternError(
                        f"Unterminated pattern group in '{expression}'.",
                        span,
                    )
                ]
            content = expression[index + 1 : close]
            if content.startswith("@"):
                name = content[1:]
                if not name:
                    return None, [
                        PatternError(
                            f"Empty named pattern reference in '{expression}'.",
                            span,
                        )
                    ]
                definition = pattern_map.get(name)
                if definition is None:
                    return None, [
                        PatternError(
                            f"Named pattern '{name}' is undefined.",
                            span,
                        )
                    ]
                group_kind, labels, error = _parse_named_group(
                    definition.expr, expression
                )
                if error is not None:
                    return None, [PatternError(error, span)]
                axis_id = definition.tag or name
                if axis_id in axis_ids:
                    return None, [
                        PatternError(
                            f"Duplicate axis id '{axis_id}' in '{expression}'.",
                            span,
                        )
                    ]
                axis_ids.add(axis_id)
                order = len(axis_order)
                axis_order.append(axis_id)
                axis_specs.append(
                    AxisSpec(
                        axis_id=axis_id,
                        kind=group_kind,
                        labels=labels,
                        size=len(labels),
                        order=order,
                    )
                )
                tokens.append(
                    PatternGroup(
                        kind=group_kind,
                        labels=labels,
                        axis_id=axis_id,
                    )
                )
            else:
                group_kind, labels, error = _parse_group_content(content, expression)
                if error is not None:
                    return None, [PatternError(error, span)]
                tokens.append(
                    PatternGroup(
                        kind=group_kind,
                        labels=labels,
                        axis_id=None,
                    )
                )
            index = close + 1
            continue

        if char in (">", "[", "]", "|"):
            return None, [
                PatternError(
                    f"Unexpected '{char}' in pattern expression '{expression}'.",
                    span,
                )
            ]

        literal_buffer.append(char)
        index += 1

    flush_literal()
    if not tokens:
        return None, [
            PatternError(
                f"Empty splice segment in pattern expression '{expression}'.",
                span,
            )
        ]
    segments.append(PatternSegment(tokens=list(tokens)))

    return (
        PatternExpr(
            raw=expression,
            segments=segments,
            axes=axis_specs,
            axis_order=axis_order,
            span=span,
        ),
        [],
    )


def _normalize_named_patterns(
    named_patterns: Optional[Mapping[str, NamedPattern | str]]
) -> dict[str, NamedPattern]:
    """Normalize named pattern definitions into NamedPattern objects.

    Args:
        named_patterns: Optional mapping of named patterns to normalize.

    Returns:
        Normalized mapping of named patterns.
    """
    if not named_patterns:
        return {}
    normalized: dict[str, NamedPattern] = {}
    for name, definition in named_patterns.items():
        if isinstance(definition, NamedPattern):
            normalized[name] = definition
        else:
            normalized[name] = NamedPattern(expr=str(definition))
    return normalized


def _parse_named_group(expr: str, expression: str) -> tuple[str, list[str | int], Optional[str]]:
    """Parse a named pattern group definition.

    Args:
        expr: Group token string for the named pattern.
        expression: Parent expression for error context.

    Returns:
        Tuple of (kind, labels, error_message).
    """
    if not expr.startswith("<") or not expr.endswith(">"):
        return "enum", [], (
            "Named pattern definitions must be a single group token; "
            f"got '{expr}' while parsing '{expression}'."
        )
    content = expr[1:-1]
    return _parse_group_content(content, expression)


def _parse_group_content(
    content: str,
    expression: str,
) -> tuple[str, list[str | int], Optional[str]]:
    """Parse group token content into labels.

    Args:
        content: Raw group token content without delimiters.
        expression: Parent expression for error context.

    Returns:
        Tuple of (kind, labels, error_message).
    """
    if not content:
        return "enum", [], f"Empty pattern group in '{expression}'."
    if any(char.isspace() for char in content):
        return "enum", [], f"Whitespace is not allowed in '{expression}'."
    if any(char in "<>[];" for char in content):
        return (
            "enum",
            [],
            f"Nested pattern delimiters are not allowed in '{expression}'.",
        )
    if ":" in content:
        if "|" in content:
            return "enum", [], f"Invalid range syntax in '{expression}'."
        start_text, end_text = _split_range_tokens(content)
        if start_text is None or end_text is None:
            return "enum", [], f"Invalid range syntax in '{expression}'."
        try:
            start = int(start_text)
            end = int(end_text)
        except ValueError:
            return "enum", [], f"Invalid range syntax in '{expression}'."
        labels = list(_range_values(start, end))
        return "range", labels, None
    labels = content.split("|")
    if any(label == "" for label in labels):
        return "enum", [], f"Empty enumeration in '{expression}'."
    return "enum", labels, None


def _split_range_tokens(content: str) -> tuple[Optional[str], Optional[str]]:
    """Split a range token on ':'.

    Args:
        content: Raw range token content.

    Returns:
        Tuple of (start_text, end_text) or (None, None) on error.
    """
    if content.count(":") != 1:
        return None, None
    start_text, end_text = content.split(":", 1)
    if start_text == "" or end_text == "":
        return None, None
    return start_text, end_text


def _range_values(start: int, end: int) -> Iterable[int]:
    """Yield numeric range values in left-to-right order.

    Args:
        start: Starting integer.
        end: Ending integer.

    Returns:
        Iterable of numeric values in expansion order.
    """
    if start <= end:
        return range(start, end + 1)
    return range(start, end - 1, -1)


def iter_pattern_groups(expr: PatternExpr) -> Sequence[PatternGroup]:
    """Iterate over pattern group tokens in expression order.

    Args:
        expr: Parsed pattern expression.

    Returns:
        Sequence of pattern group tokens.
    """
    groups: list[PatternGroup] = []
    for segment in expr.segments:
        for token in segment.tokens:
            if isinstance(token, PatternGroup):
                groups.append(token)
    return groups


def has_unnamed_groups(expr: PatternExpr) -> bool:
    """Report whether an expression contains unnamed group tokens.

    Args:
        expr: Parsed pattern expression.

    Returns:
        True if any group token lacks an axis_id.
    """
    for group in iter_pattern_groups(expr):
        if group.axis_id is None:
            return True
    return False


__all__ = [
    "AxisSpec",
    "NamedPattern",
    "PatternError",
    "PatternExpr",
    "PatternGroup",
    "PatternLiteral",
    "PatternSegment",
    "PatternToken",
    "has_unnamed_groups",
    "iter_pattern_groups",
    "parse_pattern_expr",
]
