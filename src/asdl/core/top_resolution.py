"""Shared top-symbol resolution helpers with strict/permissive policy control."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Literal, Optional, Protocol, Sequence, TypeVar


class TopSymbol(Protocol):
    """Structural protocol for symbols eligible for top-resolution."""

    name: str
    file_id: Optional[str]


TopResolutionError = Literal[
    "missing_top_multiple_modules",
    "missing_top_entry_scope",
    "top_not_defined",
    "top_not_defined_in_entry_file",
]


@dataclass(frozen=True)
class TopResolutionPolicy:
    """Policy knobs for top-symbol selection behavior."""

    require_entry_file_match_for_explicit_top: bool


PERMISSIVE_TOP_POLICY = TopResolutionPolicy(
    require_entry_file_match_for_explicit_top=False
)
STRICT_TOP_POLICY = TopResolutionPolicy(
    require_entry_file_match_for_explicit_top=True
)

T = TypeVar("T", bound=TopSymbol)


@dataclass(frozen=True)
class TopResolutionResult(Generic[T]):
    """Top-resolution output with optional structured failure reason."""

    symbol: T | None
    error: TopResolutionError | None


def resolve_top_symbol(
    symbols: Sequence[T],
    *,
    top_name: str | None,
    entry_file_id: str | None,
    policy: TopResolutionPolicy,
) -> TopResolutionResult[T]:
    """Resolve a top symbol from a design symbol list.

    Args:
        symbols: Candidate symbols in deterministic declaration order.
        top_name: Optional explicit top symbol name.
        entry_file_id: Optional entry file identifier.
        policy: Resolution policy for strict/permissive behavior.

    Returns:
        A result containing the selected symbol or an error reason.
    """
    if top_name is not None:
        if entry_file_id is not None:
            for symbol in symbols:
                if symbol.name == top_name and symbol.file_id == entry_file_id:
                    return TopResolutionResult(symbol=symbol, error=None)
            if policy.require_entry_file_match_for_explicit_top:
                if any(symbol.name == top_name for symbol in symbols):
                    return TopResolutionResult(
                        symbol=None, error="top_not_defined_in_entry_file"
                    )
                return TopResolutionResult(symbol=None, error="top_not_defined")
        for symbol in symbols:
            if symbol.name == top_name:
                return TopResolutionResult(symbol=symbol, error=None)
        return TopResolutionResult(symbol=None, error="top_not_defined")

    if entry_file_id is not None:
        entry_symbols = [
            symbol for symbol in symbols if symbol.file_id == entry_file_id
        ]
        if len(entry_symbols) == 1:
            return TopResolutionResult(symbol=entry_symbols[0], error=None)
        return TopResolutionResult(symbol=None, error="missing_top_entry_scope")

    if len(symbols) == 1:
        return TopResolutionResult(symbol=symbols[0], error=None)
    return TopResolutionResult(symbol=None, error="missing_top_multiple_modules")


__all__ = [
    "PERMISSIVE_TOP_POLICY",
    "STRICT_TOP_POLICY",
    "TopResolutionError",
    "TopResolutionPolicy",
    "TopResolutionResult",
    "resolve_top_symbol",
]
