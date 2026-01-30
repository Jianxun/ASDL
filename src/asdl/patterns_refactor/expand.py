"""Expansion helpers for refactor pattern expressions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .parser import PatternError, PatternExpr, PatternGroup, PatternLiteral

DEFAULT_MAX_ATOMS = 10_000


@dataclass(frozen=True)
class EndpointAtom:
    """Expanded endpoint atom with instance and pin tokens.

    Attributes:
        inst: Expanded instance name.
        pin: Expanded pin name.
    """

    inst: str
    pin: str


@dataclass(frozen=True)
class VisualizerPatternAtom:
    """Expanded pattern atom for visualizer dumps.

    Attributes:
        text: Expanded pattern text with literal enums resolved.
        numeric_label: Optional numeric label string for range groups.
    """

    text: str
    numeric_label: Optional[str] = None


def expand_literal_enums_for_visualizer(
    expr: PatternExpr,
    *,
    max_atoms: int = DEFAULT_MAX_ATOMS,
) -> tuple[Optional[list[VisualizerPatternAtom]], list[PatternError]]:
    """Expand literal enums while preserving numeric ranges for visualization.

    Args:
        expr: Parsed pattern expression to expand.
        max_atoms: Maximum number of atoms or numeric labels to allow.

    Returns:
        Tuple of (atoms or None, errors).
    """
    atoms: list[VisualizerPatternAtom] = []
    total_atoms = 0
    for segment in expr.segments:
        segment_atoms: list[str] = [""]
        range_axes: list[list[int]] = []
        for token in segment.tokens:
            if isinstance(token, PatternLiteral):
                segment_atoms = [value + token.text for value in segment_atoms]
                continue
            if isinstance(token, PatternGroup):
                if token.kind == "enum":
                    labels = [str(label) for label in token.labels]
                    expanded: list[str] = []
                    for prefix in segment_atoms:
                        for label in labels:
                            expanded.append(prefix + label)
                    segment_atoms = expanded
                    if len(segment_atoms) > max_atoms:
                        return None, [
                            PatternError(
                                f"Pattern expression '{expr.raw}' exceeds {max_atoms} atoms.",
                                expr.span,
                            )
                        ]
                    continue
                if token.kind == "range":
                    axis_labels = [int(label) for label in token.labels]
                    range_axes.append(axis_labels)
                    range_token = _format_range_token(axis_labels)
                    segment_atoms = [
                        value + range_token for value in segment_atoms
                    ]
                    continue
            return None, [
                PatternError(
                    f"Unhandled token in pattern expression '{expr.raw}'.",
                    expr.span,
                )
            ]

        total_atoms += len(segment_atoms)
        if total_atoms > max_atoms:
            return None, [
                PatternError(
                    f"Pattern expression '{expr.raw}' exceeds {max_atoms} atoms.",
                    expr.span,
                )
            ]

        numeric_label, error = _format_numeric_label(
            range_axes, expr=expr, max_atoms=max_atoms
        )
        if error is not None:
            return None, [error]
        for text in segment_atoms:
            atoms.append(
                VisualizerPatternAtom(text=text, numeric_label=numeric_label)
            )

    return atoms, []


def _format_range_token(axis_labels: list[int]) -> str:
    """Render a range group token from numeric labels.

    Args:
        axis_labels: Ordered numeric labels from a range group.

    Returns:
        Range token string using the original order.
    """
    if not axis_labels:
        return "<>"
    return f"<{axis_labels[0]}:{axis_labels[-1]}>"


def _format_numeric_label(
    range_axes: list[list[int]],
    *,
    expr: PatternExpr,
    max_atoms: int,
) -> tuple[Optional[str], Optional[PatternError]]:
    """Format numeric labels for range axes in expansion order.

    Args:
        range_axes: List of numeric label lists for each range group.
        expr: Pattern expression used for error context.
        max_atoms: Maximum number of labels to allow.

    Returns:
        Tuple of (label string or None, error or None).
    """
    if not range_axes:
        return None, None

    label_tuples: list[tuple[int, ...]] = [()]
    for axis_labels in range_axes:
        expanded: list[tuple[int, ...]] = []
        for prefix in label_tuples:
            for label in axis_labels:
                expanded.append((*prefix, label))
                if len(expanded) > max_atoms:
                    return (
                        None,
                        PatternError(
                            f"Pattern expression '{expr.raw}' exceeds {max_atoms} atoms.",
                            expr.span,
                        ),
                    )
        label_tuples = expanded

    label_strings: list[str] = []
    for values in label_tuples:
        if len(values) == 1:
            label_strings.append(f"<{values[0]}>")
        else:
            label_strings.append(
                "<" + ",".join(str(value) for value in values) + ">"
            )
    return ";".join(label_strings), None


def expand_pattern(
    expr: PatternExpr,
    *,
    max_atoms: int = DEFAULT_MAX_ATOMS,
) -> tuple[Optional[list[str]], list[PatternError]]:
    """Expand a parsed pattern expression into literal atoms.

    Args:
        expr: Parsed pattern expression to expand.
        max_atoms: Maximum number of atoms to allow.

    Returns:
        Tuple of (atoms or None, errors).
    """
    atoms: list[str] = []
    for segment in expr.segments:
        segment_atoms: list[str] = [""]
        for token in segment.tokens:
            if isinstance(token, PatternLiteral):
                segment_atoms = [value + token.text for value in segment_atoms]
                continue
            if isinstance(token, PatternGroup):
                labels = [str(label) for label in token.labels]
                expanded: list[str] = []
                for prefix in segment_atoms:
                    for label in labels:
                        expanded.append(prefix + label)
                segment_atoms = expanded
                if len(segment_atoms) > max_atoms:
                    return None, [
                        PatternError(
                            f"Pattern expression '{expr.raw}' exceeds {max_atoms} atoms.",
                            expr.span,
                        )
                    ]
                continue
            return None, [
                PatternError(
                    f"Unhandled token in pattern expression '{expr.raw}'.",
                    expr.span,
                )
            ]
        if len(atoms) + len(segment_atoms) > max_atoms:
            return None, [
                PatternError(
                    f"Pattern expression '{expr.raw}' exceeds {max_atoms} atoms.",
                    expr.span,
                )
            ]
        atoms.extend(segment_atoms)

    return atoms, []


def expand_endpoint(
    expr: PatternExpr,
    *,
    max_atoms: int = DEFAULT_MAX_ATOMS,
) -> tuple[Optional[list[tuple[str, str]]], list[PatternError]]:
    """Expand a parsed endpoint expression into (inst, pin) atoms.

    Args:
        expr: Parsed endpoint expression (inst.pin) to expand.
        max_atoms: Maximum number of atoms to allow.

    Returns:
        Tuple of (endpoint atoms or None, errors).
    """
    atoms, errors = expand_pattern(expr, max_atoms=max_atoms)
    if atoms is None:
        return None, errors

    endpoints: list[tuple[str, str]] = []
    for atom in atoms:
        if atom.count(".") != 1:
            return None, [
                PatternError(
                    (
                        f"Endpoint expression '{expr.raw}' expands to invalid atom "
                        f"'{atom}'."
                    ),
                    expr.span,
                )
            ]
        inst, pin = atom.split(".", 1)
        endpoints.append((inst, pin))

    return endpoints, []


__all__ = [
    "DEFAULT_MAX_ATOMS",
    "EndpointAtom",
    "VisualizerPatternAtom",
    "expand_endpoint",
    "expand_literal_enums_for_visualizer",
    "expand_pattern",
]
