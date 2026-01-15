"""GraphIR to AST projection helpers."""

from __future__ import annotations

from typing import Mapping


def rebundle_bundle(bundle: object) -> str:
    """Rebundle a GraphIR bundle into a pattern token string.

    Args:
        bundle: GraphIR bundle op (removed).

    Returns:
        Pattern token string.

    Raises:
        NotImplementedError: GraphIR pattern ops are no longer supported.
    """
    raise NotImplementedError(
        "GraphIR pattern ops were removed; rebundling is unsupported."
    )


def rebundle_pattern_expr(
    pattern_expr: object,
    bundles: Mapping[str, object],
) -> str:
    """Rebundle a GraphIR pattern expression using bundle order.

    Args:
        pattern_expr: GraphIR pattern_expr op (removed).
        bundles: Mapping from bundle_id to bundle op.

    Returns:
        Pattern token string.

    Raises:
        NotImplementedError: GraphIR pattern ops are no longer supported.
    """
    raise NotImplementedError(
        "GraphIR pattern ops were removed; rebundling is unsupported."
    )


__all__ = ["rebundle_bundle", "rebundle_pattern_expr"]
