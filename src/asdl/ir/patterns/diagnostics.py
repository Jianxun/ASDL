"""Pattern diagnostics helpers and codes for IR pattern expansion."""

from __future__ import annotations

from typing import Iterable

from asdl.diagnostics import Diagnostic, Severity, format_code

MAX_EXPANSION_SIZE = 10_000
NO_SPAN_NOTE = "No source span available."

PATTERN_INVALID_RANGE = format_code("PASS", 101)
PATTERN_EMPTY_ENUM = format_code("PASS", 102)
PATTERN_EMPTY_SPLICE = format_code("PASS", 103)
PATTERN_DUPLICATE_ATOM = format_code("PASS", 104)
PATTERN_TOO_LARGE = format_code("PASS", 105)
PATTERN_UNEXPANDED = format_code("PASS", 106)


def _diagnostic(code: str, message: str) -> Diagnostic:
    """Build a pattern diagnostic with shared metadata.

    Args:
        code: Diagnostic code for the pattern error.
        message: Human-readable description of the error.

    Returns:
        Diagnostic instance with pattern source metadata attached.
    """
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        message=message,
        primary_span=None,
        notes=[NO_SPAN_NOTE],
        source="pattern",
    )


def _empty_enum_message(expression: str) -> str:
    """Build the message for an empty enumeration error.

    Args:
        expression: Original pattern expression.

    Returns:
        Error message describing the empty enumeration.
    """
    return f"Empty enumeration in pattern expression '{expression}'."


def _empty_splice_message(expression: str) -> str:
    """Build the message for an empty splice segment error.

    Args:
        expression: Original pattern expression.

    Returns:
        Error message describing the empty splice.
    """
    return f"Empty splice segment in pattern expression '{expression}'."


def _invalid_range_message(expression: str) -> str:
    """Build the message for an invalid numeric range error.

    Args:
        expression: Original pattern expression.

    Returns:
        Error message describing the invalid range.
    """
    return f"Invalid numeric range in pattern expression '{expression}'."


def _too_large_message(expression: str, max_atoms: int) -> str:
    """Build the message for an expansion overflow error.

    Args:
        expression: Original pattern expression.
        max_atoms: Maximum allowed expansion size.

    Returns:
        Error message describing the overflow.
    """
    return f"Pattern expression '{expression}' expands beyond {max_atoms} atoms."


def _duplicate_message(duplicates: Iterable[str], expression: str) -> str:
    """Build the message for duplicate atom detection.

    Args:
        duplicates: Sequence of duplicate literals.
        expression: Original pattern expression.

    Returns:
        Error message describing duplicate atoms.
    """
    dupes = list(duplicates)
    preview = ", ".join(dupes[:5])
    extra = ""
    if len(dupes) > 5:
        extra = f" (+{len(dupes) - 5} more)"
    return (
        f"Pattern expression '{expression}' expands to duplicate atoms: {preview}{extra}."
    )


def _splice_forbidden_message(expression: str) -> str:
    """Build the message for forbidden splice usage.

    Args:
        expression: Original pattern expression.

    Returns:
        Error message describing the forbidden splice usage.
    """
    return f"Splice delimiter ';' is not allowed in pattern expression '{expression}'."


__all__ = [
    "MAX_EXPANSION_SIZE",
    "PATTERN_DUPLICATE_ATOM",
    "PATTERN_EMPTY_ENUM",
    "PATTERN_EMPTY_SPLICE",
    "PATTERN_INVALID_RANGE",
    "PATTERN_TOO_LARGE",
    "PATTERN_UNEXPANDED",
]
