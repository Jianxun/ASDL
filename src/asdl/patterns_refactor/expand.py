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


__all__ = ["DEFAULT_MAX_ATOMS", "EndpointAtom", "expand_endpoint", "expand_pattern"]
