"""Pattern binding verification helpers."""

from __future__ import annotations

from typing import Dict, Iterable, List, Sequence, Tuple


def format_endpoint_length_mismatch(
    net_token: str,
    net_len: int,
    endpoint_token: str,
    endpoint_len: int,
    *,
    verb: str,
) -> str:
    """Build the message for a net/endpoint expansion length mismatch.

    Args:
        net_token: Net pattern token.
        net_len: Net expansion length.
        endpoint_token: Endpoint token ("inst.pin").
        endpoint_len: Endpoint expansion length.
        verb: Expansion verb (for example, "atomizes" or "expands").

    Returns:
        Message describing the expansion length mismatch.
    """
    return (
        f"Net '{net_token}' {verb} to {net_len} atoms but endpoint "
        f"'{endpoint_token}' {verb} to {endpoint_len}"
    )


def format_param_length_mismatch(
    instance_name: str,
    param_name: str,
    param_len: int,
    instance_len: int,
    *,
    verb: str,
) -> str:
    """Build the message for a parameter expansion length mismatch.

    Args:
        instance_name: Instance name token.
        param_name: Parameter name.
        param_len: Parameter expansion length.
        instance_len: Instance expansion length.
        verb: Expansion verb (for example, "atomizes" or "expands").

    Returns:
        Message describing the parameter expansion length mismatch.
    """
    return (
        f"Instance '{instance_name}' parameter '{param_name}' {verb} to {param_len} "
        f"values but instance {verb} to {instance_len}"
    )


def collect_literal_collisions(
    entries: Iterable[Tuple[str, str]],
) -> Dict[str, List[str]]:
    """Group literal collision candidates by literal name.

    Args:
        entries: Iterable of (literal, token) pairs.

    Returns:
        Mapping of literal name to ordered token list for collisions.
    """
    collisions: Dict[str, List[str]] = {}
    for literal, token in entries:
        collisions.setdefault(literal, []).append(token)
    return {
        literal: tokens
        for literal, tokens in collisions.items()
        if len(tokens) > 1
    }


def format_literal_collision_message(
    kind: str,
    literal: str,
    tokens: Sequence[str],
    *,
    phase: str,
) -> str:
    """Build the message for a literal collision after expansion/atomization.

    Args:
        kind: Entity kind ("Net", "Instance", etc.).
        literal: Colliding literal name.
        tokens: Token list that expanded into the literal.
        phase: Phase label ("atomization", "expansion").

    Returns:
        Message describing the literal collision.
    """
    token_list = _format_token_list(tokens)
    return (
        f"{kind} literal name collision after {phase} for '{literal}' "
        f"from tokens {token_list}"
    )


def _format_token_list(tokens: Sequence[str]) -> str:
    """Format a token list for collision diagnostics.

    Args:
        tokens: Token list including potential duplicates.

    Returns:
        Formatted token list with a preview cap.
    """
    unique: List[str] = []
    seen = set()
    for token in tokens:
        if token in seen:
            continue
        seen.add(token)
        unique.append(token)
    preview = ", ".join(f"'{token}'" for token in unique[:5])
    extra = ""
    if len(unique) > 5:
        extra = f" (+{len(unique) - 5} more)"
    return f"{preview}{extra}."


__all__ = [
    "collect_literal_collisions",
    "format_endpoint_length_mismatch",
    "format_literal_collision_message",
    "format_param_length_mismatch",
]
