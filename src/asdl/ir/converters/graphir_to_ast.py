"""GraphIR to AST projection helpers."""

from __future__ import annotations

from typing import Mapping

from asdl.ir.graphir import BundleOp, PatternExprOp
from asdl.ir.graphir.patterns import PatternBundleMetadata, bundle_metadata


def rebundle_bundle(bundle: BundleOp) -> str:
    """Rebundle a GraphIR bundle into a pattern token string.

    Args:
        bundle: Bundle op containing pattern metadata.

    Returns:
        Rebundled pattern token string.
    """
    metadata = bundle_metadata(bundle)
    segments = _rebundle_segments(metadata)
    return ";".join(segments)


def rebundle_pattern_expr(
    pattern_expr: PatternExprOp,
    bundles: Mapping[str, BundleOp],
) -> str:
    """Rebundle a GraphIR pattern expression using bundle order.

    Args:
        pattern_expr: Pattern expression op to rebundle.
        bundles: Mapping from bundle_id to BundleOp.

    Returns:
        Rebundled pattern token string with `;` boundaries preserved.

    Raises:
        ValueError: If referenced bundles are missing or invalid.
    """
    segments: list[str] = []
    for bundle_id_attr in pattern_expr.bundles.data:
        bundle_id = bundle_id_attr.value.data
        bundle = bundles.get(bundle_id)
        if bundle is None:
            raise ValueError(f"pattern_expr references unknown bundle '{bundle_id}'")
        segments.append(rebundle_bundle(bundle))
    return ";".join(segments)


def _rebundle_segments(metadata: PatternBundleMetadata) -> list[str]:
    """Split bundle metadata into rebundled pattern segments.

    Args:
        metadata: Bundle metadata to rebundle.

    Returns:
        Ordered list of rebundled pattern segments.
    """
    segments: list[str] = []
    base_name = metadata.base_name
    tokens = metadata.tokens
    eligible = metadata.eligible
    if metadata.pattern_type == "numeric":
        run: list[int] = []
        run_step: int | None = None

        def flush_run() -> None:
            if not run:
                return
            segments.append(f"{base_name}[{run[0]}:{run[-1]}]")

        for token, is_eligible in zip(tokens, eligible):
            if not is_eligible:
                flush_run()
                run = []
                run_step = None
                segments.append(_literal_segment(base_name, token))
                continue
            value = _coerce_int(token)
            if not run:
                run = [value]
                run_step = None
                continue
            step = value - run[-1]
            if step not in (1, -1):
                flush_run()
                run = [value]
                run_step = None
                continue
            if run_step is None:
                run_step = step
                run.append(value)
                continue
            if step != run_step:
                flush_run()
                run = [value]
                run_step = None
                continue
            run.append(value)

        flush_run()
        return segments

    run_literals: list[str] = []

    def flush_literals() -> None:
        if not run_literals:
            return
        segments.append(f"{base_name}<{ '|'.join(run_literals) }>")

    for token, is_eligible in zip(tokens, eligible):
        if not is_eligible:
            flush_literals()
            run_literals.clear()
            segments.append(_literal_segment(base_name, token))
            continue
        run_literals.append(_coerce_literal(token))

    flush_literals()
    return segments


def _literal_segment(base_name: str, token: str | int) -> str:
    """Format a literal segment from base name and token.

    Args:
        base_name: Bundle base name.
        token: Literal token payload.

    Returns:
        Literal segment string.
    """
    return f"{base_name}{token}"


def _coerce_int(value: str | int) -> int:
    """Coerce a numeric token into an integer.

    Args:
        value: Token value to coerce.

    Returns:
        Parsed integer value.
    """
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Invalid numeric token '{value}'") from exc


def _coerce_literal(value: str | int) -> str:
    """Coerce a literal token into a string.

    Args:
        value: Token value to coerce.

    Returns:
        Parsed string value.
    """
    if isinstance(value, str):
        return value
    raise ValueError(f"Invalid literal token '{value}'")


__all__ = ["rebundle_bundle", "rebundle_pattern_expr"]
