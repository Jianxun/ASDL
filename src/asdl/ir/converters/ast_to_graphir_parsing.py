"""Parsing helpers for AST to GraphIR conversion."""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple


def parse_instance_expr(expr: str) -> Tuple[Optional[str], Dict[str, str], Optional[str]]:
    """Parse an instance expression into a reference and params.

    Args:
        expr: Instance expression string.

    Returns:
        Tuple of (reference, params, error message).
    """
    tokens = expr.split()
    if not tokens:
        return None, {}, "Instance expression must start with a model name"
    ref = tokens[0]
    params: Dict[str, str] = {}
    for token in tokens[1:]:
        if "=" not in token:
            return None, {}, f"Invalid instance param token '{token}'; expected key=value"
        key, value = token.split("=", 1)
        if not key or not value:
            return None, {}, f"Invalid instance param token '{token}'; expected key=value"
        params[key] = value
    return ref, params, None


def parse_endpoints(
    expr: Sequence[str],
) -> Tuple[List[Tuple[str, str, bool]], Optional[str]]:
    """Parse endpoint expressions into (instance, port, suppressed) tuples.

    Args:
        expr: Sequence of endpoint tokens.

    Returns:
        Tuple of endpoints and error message.
    """
    endpoints: List[Tuple[str, str, bool]] = []
    if isinstance(expr, str):
        return (
            [],
            "Endpoint lists must be YAML lists of '<instance>.<pin>' strings",
        )
    for token in expr:
        raw_token = token
        suppress_override = False
        if token.startswith("!"):
            suppress_override = True
            token = token[1:]
        if token.count(".") != 1:
            return [], f"Invalid endpoint token '{raw_token}'; expected inst.pin"
        inst, pin = token.split(".", 1)
        if not inst or not pin:
            return [], f"Invalid endpoint token '{raw_token}'; expected inst.pin"
        endpoints.append((inst, pin, suppress_override))
    return endpoints, None


def split_net_token(net_token: str) -> Tuple[str, bool]:
    """Split a net token into name and port flag.

    Args:
        net_token: Net token, optionally prefixed with '$'.

    Returns:
        Tuple of (net name, is port).
    """
    if net_token.startswith("$"):
        return net_token[1:], True
    return net_token, False


__all__ = ["parse_endpoints", "parse_instance_expr", "split_net_token"]
