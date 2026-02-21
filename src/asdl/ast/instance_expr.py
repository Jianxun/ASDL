"""Utilities for inline instance expression tokenization and parsing."""

from __future__ import annotations

import shlex
from collections import OrderedDict
from typing import Optional


def tokenize_inline_instance_expr(expr: str) -> tuple[Optional[list[str]], Optional[str]]:
    """Tokenize inline instance syntax while honoring shell-style quotes.

    Args:
        expr: Raw inline expression (for example ``"code cmd='.TRAN 0 10u'"``).

    Returns:
        Tuple of ``(tokens, error_message)``. On success ``error_message`` is
        ``None``. On failure ``tokens`` is ``None``.
    """
    lexer = shlex.shlex(expr, posix=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        return list(lexer), None
    except ValueError as exc:
        return None, str(exc)


def parse_inline_instance_expr(
    expr: str,
    *,
    strict_params: bool,
) -> tuple[Optional[str], "OrderedDict[str, str]", Optional[str]]:
    """Parse inline instance syntax into reference and parameters.

    Args:
        expr: Raw inline expression string.
        strict_params: Whether malformed param tokens should be treated as an
            error (`True`) or ignored (`False`).

    Returns:
        Tuple of ``(ref, params, error_message)``.
    """
    tokens, token_error = tokenize_inline_instance_expr(expr)
    if token_error is not None:
        return None, OrderedDict(), f"Invalid quoting in instance expression: {token_error}"
    if not tokens:
        return None, OrderedDict(), "Instance expression must start with a model name"

    ref = tokens[0]
    params: "OrderedDict[str, str]" = OrderedDict()
    for token in tokens[1:]:
        if "=" not in token:
            if strict_params:
                return None, OrderedDict(), (
                    f"Invalid instance param token '{token}'; expected key=value"
                )
            continue
        key, value = token.split("=", 1)
        if not key or not value:
            if strict_params:
                return None, OrderedDict(), (
                    f"Invalid instance param token '{token}'; expected key=value"
                )
            continue
        params[key] = value
    return ref, params, None


def format_inline_param_token(key: str, value: str) -> str:
    """Format one inline ``key=value`` token, quoting value when needed."""
    if any(ch.isspace() for ch in value):
        return f"{key}={shlex.quote(value)}"
    return f"{key}={value}"

