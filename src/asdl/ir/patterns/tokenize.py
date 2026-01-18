"""Tokenization helpers for IR pattern expansion and atomization."""

from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

from asdl.diagnostics import Diagnostic

from .diagnostics import (
    PATTERN_EMPTY_ENUM,
    PATTERN_INVALID_RANGE,
    PATTERN_UNEXPANDED,
    _diagnostic,
    _empty_enum_message,
    _invalid_range_message,
    _splice_forbidden_message,
)


def _split_splice_segments(
    expression: str, *, allow_splice: bool = True
) -> Tuple[Optional[List[str]], Optional[Diagnostic]]:
    """Split a pattern expression into splice segments, validating delimiter usage.

    Args:
        expression: Pattern expression containing optional splice delimiters.
        allow_splice: Whether to allow splice delimiters outside of pattern groups.

    Returns:
        Tuple of (segments, diagnostic). Diagnostic is set on error.
    """
    segments: List[str] = []
    buffer: List[str] = []
    state: bool = False

    for char in expression:
        if not state:
            if char == ";":
                if not allow_splice:
                    return None, _diagnostic(
                        PATTERN_UNEXPANDED,
                        _splice_forbidden_message(expression),
                    )
                segments.append("".join(buffer))
                buffer = []
                continue
            if char == "<":
                state = True
            elif char in ("[", "]", ">"):
                return None, _diagnostic(
                    PATTERN_UNEXPANDED,
                    f"Unexpected '{char}' in pattern expression '{expression}'.",
                )
        else:
            if char == ";":
                return None, _diagnostic(
                    PATTERN_UNEXPANDED,
                    (
                        "Splice delimiter ';' is not allowed inside pattern groups in "
                        f"'{expression}'."
                    ),
                )
            if char in ("<", "["):
                return None, _diagnostic(
                    PATTERN_UNEXPANDED,
                    f"Nested pattern delimiters are not allowed in '{expression}'.",
                )
            if char == ">":
                state = False
            elif char == "]":
                return None, _diagnostic(
                    PATTERN_UNEXPANDED,
                    f"Unexpected '{char}' in pattern expression '{expression}'.",
                )
        buffer.append(char)

    if state:
        return None, _diagnostic(
            PATTERN_UNEXPANDED,
            f"Unterminated pattern delimiter in '{expression}'.",
        )

    segments.append("".join(buffer))
    return segments, None


def _tokenize_segment(
    segment: str, expression: str
) -> Tuple[Optional[List[Tuple[str, object]]], Optional[Diagnostic]]:
    """Tokenize a pattern segment into literal and pattern group tokens.

    Args:
        segment: Segment without splice delimiters.
        expression: Original pattern expression for diagnostic messages.

    Returns:
        Tuple of (tokens, diagnostic). Diagnostic is set on error.
    """
    tokens: List[Tuple[str, object]] = []
    literal: List[str] = []
    index = 0

    while index < len(segment):
        char = segment[index]
        if char == "<":
            if literal:
                tokens.append(("literal", "".join(literal)))
                literal = []
            close = segment.find(">", index + 1)
            if close == -1:
                return None, _diagnostic(
                    PATTERN_UNEXPANDED,
                    f"Unterminated enumeration in '{expression}'.",
                )
            content = segment[index + 1 : close]
            if ":" in content:
                if "|" in content:
                    return None, _diagnostic(
                        PATTERN_INVALID_RANGE,
                        _invalid_range_message(expression),
                    )
                range_value, diag = _parse_range_content(content, expression)
                if diag is not None:
                    return None, diag
                tokens.append(("range", range_value))
            else:
                diag = _validate_enum_content(content, expression)
                if diag is not None:
                    return None, diag
                alts = content.split("|") if content else []
                if any(alt == "" for alt in alts):
                    return None, _diagnostic(PATTERN_EMPTY_ENUM, _empty_enum_message(expression))
                tokens.append(("enum", alts))
            index = close + 1
            continue

        if char in ("[", "]", "|", ">"):
            return None, _diagnostic(
                PATTERN_UNEXPANDED,
                f"Unexpected '{char}' in pattern expression '{expression}'.",
            )

        literal.append(char)
        index += 1

    if literal:
        tokens.append(("literal", "".join(literal)))
    return tokens, None


def _validate_enum_content(content: str, expression: str) -> Optional[Diagnostic]:
    """Validate enumeration content for a pattern group.

    Args:
        content: Raw enumeration content between delimiters.
        expression: Original pattern expression for diagnostic messages.

    Returns:
        Diagnostic on error, otherwise None.
    """
    if content == "":
        return _diagnostic(PATTERN_EMPTY_ENUM, _empty_enum_message(expression))
    if _has_whitespace(content):
        return _diagnostic(
            PATTERN_UNEXPANDED,
            f"Whitespace is not allowed around '|' in '{expression}'.",
        )
    if "," in content:
        return _diagnostic(
            PATTERN_UNEXPANDED,
            f"Enumeration alternatives must use '|' in '{expression}'.",
        )
    if any(char in "<>[];" for char in content):
        return _diagnostic(
            PATTERN_UNEXPANDED,
            f"Nested pattern delimiters are not allowed in '{expression}'.",
        )
    return None


def _parse_range_content(
    content: str, expression: str
) -> Tuple[Optional[Tuple[int, int]], Optional[Diagnostic]]:
    """Parse numeric range content for a pattern expression.

    Args:
        content: Raw numeric range content between delimiters.
        expression: Original pattern expression for diagnostic messages.

    Returns:
        Tuple of (range, diagnostic). Diagnostic is set on error.
    """
    if content.count(":") != 1:
        return None, _diagnostic(PATTERN_INVALID_RANGE, _invalid_range_message(expression))
    if _has_whitespace(content):
        return None, _diagnostic(PATTERN_INVALID_RANGE, _invalid_range_message(expression))
    if any(char in "<>[];|" for char in content):
        return None, _diagnostic(PATTERN_INVALID_RANGE, _invalid_range_message(expression))

    start_text, end_text = content.split(":", 1)
    if start_text == "" or end_text == "":
        return None, _diagnostic(PATTERN_INVALID_RANGE, _invalid_range_message(expression))
    try:
        start = int(start_text)
        end = int(end_text)
    except ValueError:
        return None, _diagnostic(PATTERN_INVALID_RANGE, _invalid_range_message(expression))

    return (start, end), None


def _range_values(start: int, end: int) -> Iterable[int]:
    """Return the numeric range values in the correct expansion order.

    Args:
        start: Starting integer.
        end: Ending integer.

    Returns:
        Iterable over the numeric values in expansion order.
    """
    if start <= end:
        return range(start, end + 1)
    return range(start, end - 1, -1)


def _find_duplicates(items: Iterable[str]) -> List[str]:
    """Return items that are duplicates while preserving first-seen order.

    Args:
        items: Sequence of items to inspect.

    Returns:
        List of duplicate values in the order they first repeated.
    """
    seen: set[str] = set()
    duplicates: List[str] = []
    for item in items:
        if item in seen and item not in duplicates:
            duplicates.append(item)
            continue
        seen.add(item)
    return duplicates


def _has_whitespace(value: str) -> bool:
    """Report whether the string contains any whitespace characters.

    Args:
        value: String to inspect.

    Returns:
        True if the string contains whitespace.
    """
    return any(char.isspace() for char in value)


def _has_pattern_delimiters(expression: str) -> bool:
    """Report whether the expression includes pattern delimiter characters.

    Args:
        expression: Pattern expression to inspect.

    Returns:
        True if the expression contains a pattern delimiter.
    """
    return any(char in "<>[];" for char in expression)


__all__ = [
    "_find_duplicates",
    "_has_pattern_delimiters",
    "_has_whitespace",
    "_range_values",
    "_split_splice_segments",
    "_tokenize_segment",
]
