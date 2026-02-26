"""Binding helpers for refactor pattern expressions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .expand import DEFAULT_MAX_ATOMS, expand_pattern
from .parser import PatternError, PatternExpr, has_unnamed_groups


@dataclass(frozen=True)
class BindingPlan:
    """Binding plan for mapping net atoms to endpoint atoms.

    Attributes:
        net_expr_id: Expression identifier for the net token.
        endpoint_expr_id: Expression identifier for the endpoint token.
        net_length: Number of net atoms.
        endpoint_length: Number of endpoint atoms.
        shared_axes: Axis identifiers shared between net and endpoint.
        broadcast_axes: Axis identifiers present only on the endpoint.
        mapping: Net index for each endpoint atom index.
    """

    net_expr_id: str
    endpoint_expr_id: str
    net_length: int
    endpoint_length: int
    shared_axes: list[str]
    broadcast_axes: list[str]
    mapping: list[int]

    def map_index(self, net_index: int, endpoint_index: int) -> int:
        """Return the net index bound to an endpoint index.

        Args:
            net_index: Candidate net index (unused; kept for API compatibility).
            endpoint_index: Endpoint atom index to map.

        Returns:
            Bound net atom index.
        """
        return self.mapping[endpoint_index]


def bind_patterns(
    net_expr: PatternExpr,
    endpoint_expr: PatternExpr,
    *,
    net_expr_id: str,
    endpoint_expr_id: str,
    max_atoms: int = DEFAULT_MAX_ATOMS,
) -> tuple[Optional[BindingPlan], list[PatternError]]:
    """Build a binding plan for net-to-endpoint pattern expressions.

    Args:
        net_expr: Parsed net name expression.
        endpoint_expr: Parsed endpoint expression.
        net_expr_id: Expression identifier for the net token.
        endpoint_expr_id: Expression identifier for the endpoint token.
        max_atoms: Maximum number of atoms to allow during expansion.

    Returns:
        Tuple of (BindingPlan or None, errors).
    """
    net_atoms, errors = expand_pattern(net_expr, max_atoms=max_atoms)
    if net_atoms is None:
        return None, errors
    endpoint_atoms, errors = expand_pattern(endpoint_expr, max_atoms=max_atoms)
    if endpoint_atoms is None:
        return None, errors

    net_length = len(net_atoms)
    endpoint_length = len(endpoint_atoms)
    shared_axes = [
        axis_id
        for axis_id in net_expr.axis_order
        if axis_id in {axis.axis_id for axis in endpoint_expr.axes}
    ]
    broadcast_axes = [
        axis_id
        for axis_id in endpoint_expr.axis_order
        if axis_id not in {axis.axis_id for axis in net_expr.axes}
    ]

    if net_length == endpoint_length:
        mapping = list(range(net_length))
        return (
            BindingPlan(
                net_expr_id=net_expr_id,
                endpoint_expr_id=endpoint_expr_id,
                net_length=net_length,
                endpoint_length=endpoint_length,
                shared_axes=shared_axes,
                broadcast_axes=broadcast_axes,
                mapping=mapping,
            ),
            [],
        )

    if net_length == 1:
        mapping = [0] * endpoint_length
        return (
            BindingPlan(
                net_expr_id=net_expr_id,
                endpoint_expr_id=endpoint_expr_id,
                net_length=net_length,
                endpoint_length=endpoint_length,
                shared_axes=shared_axes,
                broadcast_axes=broadcast_axes,
                mapping=mapping,
            ),
            [],
        )

    if has_unnamed_groups(net_expr) or has_unnamed_groups(endpoint_expr):
        return None, [
            PatternError(
                "Named-axis broadcast requires named groups in both expressions.",
                net_expr.span or endpoint_expr.span,
            )
        ]

    if len(net_expr.segments) > 1 or len(endpoint_expr.segments) > 1:
        return None, [
            PatternError(
                "Named-axis broadcast is not supported for spliced expressions.",
                net_expr.span or endpoint_expr.span,
            )
        ]

    if not net_expr.axis_order or not endpoint_expr.axis_order:
        return None, [
            PatternError(
                "Named-axis broadcast requires axis metadata for both expressions.",
                net_expr.span or endpoint_expr.span,
            )
        ]

    positions, missing_axis = _axis_subsequence_positions(
        net_expr.axis_order, endpoint_expr.axis_order
    )
    if positions is None:
        return None, [
            PatternError(
                (
                    "Endpoint axis order does not include axis "
                    f"'{missing_axis}' from '{net_expr.raw}'."
                ),
                net_expr.span or endpoint_expr.span,
            )
        ]

    net_axis_sizes = {axis.axis_id: axis.size for axis in net_expr.axes}
    endpoint_axis_sizes = {axis.axis_id: axis.size for axis in endpoint_expr.axes}
    net_expected = _axis_size_product(net_expr.axis_order, net_axis_sizes)
    endpoint_expected = _axis_size_product(endpoint_expr.axis_order, endpoint_axis_sizes)
    if net_expected != net_length or endpoint_expected != endpoint_length:
        return None, [
            PatternError(
                (
                    "Axis broadcast requires expansion lengths to match axis-size "
                    f"products (net {net_length}/{net_expected}, "
                    f"endpoint {endpoint_length}/{endpoint_expected})."
                ),
                net_expr.span or endpoint_expr.span,
            )
        ]
    for axis_id in net_expr.axis_order:
        net_size = net_axis_sizes.get(axis_id)
        endpoint_size = endpoint_axis_sizes.get(axis_id)
        if net_size is None or endpoint_size is None:
            return None, [
                PatternError(
                    f"Axis '{axis_id}' is missing for broadcast binding.",
                    net_expr.span or endpoint_expr.span,
                )
            ]
        if net_size != endpoint_size:
            return None, [
                PatternError(
                    (
                        f"Axis '{axis_id}' length mismatch between '{net_expr.raw}' "
                        f"({net_size}) and '{endpoint_expr.raw}' ({endpoint_size})."
                    ),
                    net_expr.span or endpoint_expr.span,
                )
            ]

    endpoint_sizes = [endpoint_axis_sizes[axis_id] for axis_id in endpoint_expr.axis_order]
    net_sizes = [net_axis_sizes[axis_id] for axis_id in net_expr.axis_order]

    mapping: list[int] = []
    for endpoint_index in range(endpoint_length):
        endpoint_coords = _index_to_coords(endpoint_index, endpoint_sizes)
        net_coords = [endpoint_coords[pos] for pos in positions]
        net_index = _coords_to_index(net_coords, net_sizes)
        mapping.append(net_index)

    return (
        BindingPlan(
            net_expr_id=net_expr_id,
            endpoint_expr_id=endpoint_expr_id,
            net_length=net_length,
            endpoint_length=endpoint_length,
            shared_axes=shared_axes,
            broadcast_axes=broadcast_axes,
            mapping=mapping,
        ),
        [],
    )


def _axis_subsequence_positions(
    net_axes: list[str],
    endpoint_axes: list[str],
) -> tuple[Optional[list[int]], Optional[str]]:
    """Find endpoint indices that align to net axes as a subsequence.

    Args:
        net_axes: Ordered axis ids from the net expression.
        endpoint_axes: Ordered axis ids from the endpoint expression.

    Returns:
        Tuple of (positions, missing_axis_id). positions is None when matching fails.
    """
    positions: list[int] = []
    cursor = 0
    for axis_id in net_axes:
        try:
            index = endpoint_axes.index(axis_id, cursor)
        except ValueError:
            return None, axis_id
        positions.append(index)
        cursor = index + 1
    return positions, None


def _index_to_coords(index: int, sizes: list[int]) -> list[int]:
    """Convert a flat index into mixed-radix coordinates.

    Args:
        index: Flat index into the expansion list.
        sizes: Axis sizes in expression order.

    Returns:
        Coordinate list for each axis.
    """
    coords: list[int] = []
    for size in reversed(sizes):
        coords.append(index % size)
        index //= size
    return list(reversed(coords))


def _coords_to_index(coords: list[int], sizes: list[int]) -> int:
    """Convert mixed-radix coordinates back into a flat index.

    Args:
        coords: Axis coordinates in expression order.
        sizes: Axis sizes in expression order.

    Returns:
        Flat index for the coordinates.
    """
    index = 0
    for coord, size in zip(coords, sizes):
        index = index * size + coord
    return index


def _axis_size_product(axis_order: list[str], axis_sizes: dict[str, int]) -> int:
    """Compute the product of axis sizes in expression order.

    Args:
        axis_order: Axis identifier ordering.
        axis_sizes: Mapping from axis identifier to size.

    Returns:
        Product of axis sizes, or 0 when any axis is missing.
    """
    product = 1
    for axis_id in axis_order:
        size = axis_sizes.get(axis_id)
        if size is None:
            return 0
        product *= size
    return product


__all__ = ["BindingPlan", "bind_patterns"]
