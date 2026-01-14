"""Tokenization helpers for pattern expansion and atomization."""

from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

from ..diagnostics import Diagnostic
from .diagnostics import (
    PATTERN_EMPTY_ENUM,
    PATTERN_INVALID_RANGE,
    PATTERN_UNEXPANDED,
    _diagnostic,
    _empty_enum_message,
    _invalid_range_message,
)


def _split_splice_segments(token: str) -> Tuple[Optional[List[str]], Optional[Diagnostic]]:
    """Split a pattern token into splice segments, validating delimiter usage.

    Args:
        token: Pattern token containing optional splice delimiters.

    Returns:
        Tuple of (segments, diagnostic). Diagnostic is set on error.
    """
    segments: List[str] = []
    buffer: List[str] = []
    state: Optional[str] = None

    for char in token:
        if state is None:
            if char == ";":
                segments.append("".join(buffer))
                buffer = []
                continue
            if char == "<":
                state = "enum"
            elif char == "[":
                state = "range"
            elif char in ("]", ">"):
                return None, _diagnostic(
                    PATTERN_UNEXPANDED,
                    f"Unexpected '{char}' in pattern token '{token}'.",
                )
        else:
            if char == ";":
                return None, _diagnostic(
                    PATTERN_UNEXPANDED,
                    f"Splice delimiter ';' is not allowed inside pattern groups in '{token}'.",
                )
            if char in ("<", "["):
                return None, _diagnostic(
                    PATTERN_UNEXPANDED,
                    f"Nested pattern delimiters are not allowed in '{token}'.",
                )
            if state == "enum" and char == ">":
                state = None
            elif state == "range" and char == "]":
                state = None
        buffer.append(char)

    if state is not None:
        return None, _diagnostic(
            PATTERN_UNEXPANDED,
            f"Unterminated pattern delimiter in '{token}'.",
        )

    segments.append("".join(buffer))
    return segments, None


def _tokenize_segment(
    segment: str, token: str
) -> Tuple[Optional[List[Tuple[str, object]]], Optional[Diagnostic]]:
    """Tokenize a pattern segment into literal and pattern group tokens.

    Args:
        segment: Segment without splice delimiters.
        token: Original pattern token for diagnostic messages.

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
                    f"Unterminated enumeration in '{token}'.",
                )
            content = segment[index + 1 : close]
            diag = _validate_enum_content(content, token)
            if diag is not None:
                return None, diag
            alts = content.split("|") if content else []
            if any(alt == "" for alt in alts):
                return None, _diagnostic(PATTERN_EMPTY_ENUM, _empty_enum_message(token))
            tokens.append(("enum", alts))
            index = close + 1
            continue

        if char == "[":
            if literal:
                tokens.append(("literal", "".join(literal)))
                literal = []
            close = segment.find("]", index + 1)
            if close == -1:
                return None, _diagnostic(
                    PATTERN_UNEXPANDED,
                    f"Unterminated numeric range in '{token}'.",
                )
            content = segment[index + 1 : close]
            range_value, diag = _parse_range_content(content, token)
            if diag is not None:
                return None, diag
            tokens.append(("range", range_value))
            index = close + 1
            continue

        if char in "|]>":
            return None, _diagnostic(
                PATTERN_UNEXPANDED,
                f"Unexpected '{char}' in pattern token '{token}'.",
            )

        literal.append(char)
        index += 1

    if literal:
        tokens.append(("literal", "".join(literal)))
    return tokens, None


def _validate_enum_content(content: str, token: str) -> Optional[Diagnostic]:
    """Validate enumeration content for a pattern group.

    Args:
        content: Raw enumeration content between delimiters.
        token: Original pattern token for diagnostic messages.

    Returns:
        Diagnostic on error, otherwise None.
    """
    if content == "":
        return _diagnostic(PATTERN_EMPTY_ENUM, _empty_enum_message(token))
    if _has_whitespace(content):
        return _diagnostic(
            PATTERN_UNEXPANDED,
            f"Whitespace is not allowed around '|' in '{token}'.",
        )
    if "," in content:
        return _diagnostic(
            PATTERN_UNEXPANDED,
            f"Enumeration alternatives must use '|' in '{token}'.",
        )
    if any(char in "<>[];" for char in content):
        return _diagnostic(
            PATTERN_UNEXPANDED,
            f"Nested pattern delimiters are not allowed in '{token}'.",
        )
    return None


def _parse_range_content(
    content: str, token: str
) -> Tuple[Optional[Tuple[int, int]], Optional[Diagnostic]]:
    """Parse numeric range content for a pattern token.

    Args:
        content: Raw numeric range content between delimiters.
        token: Original pattern token for diagnostic messages.

    Returns:
        Tuple of (range, diagnostic). Diagnostic is set on error.
    """
    if content.count(":") != 1:
        return None, _diagnostic(PATTERN_INVALID_RANGE, _invalid_range_message(token))
    if _has_whitespace(content):
        return None, _diagnostic(PATTERN_INVALID_RANGE, _invalid_range_message(token))
    if any(char in "<>[];|" for char in content):
        return None, _diagnostic(PATTERN_INVALID_RANGE, _invalid_range_message(token))

    start_text, end_text = content.split(":", 1)
    if start_text == "" or end_text == "":
        return None, _diagnostic(PATTERN_INVALID_RANGE, _invalid_range_message(token))
    try:
        start = int(start_text)
        end = int(end_text)
    except ValueError:
        return None, _diagnostic(PATTERN_INVALID_RANGE, _invalid_range_message(token))

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


def _has_pattern_delimiters(token: str) -> bool:
    """Report whether the token includes any pattern delimiter characters.

    Args:
        token: Pattern token to inspect.

    Returns:
        True if the token contains a pattern delimiter.
    """
    return any(char in "<>[];" for char in token)
