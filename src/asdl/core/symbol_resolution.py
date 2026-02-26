"""Shared symbol-selection helpers for deterministic name/file_id resolution."""

from __future__ import annotations

from typing import Generic, Optional, Protocol, Sequence, TypeVar


class ResolvableSymbol(Protocol):
    """Structural protocol for symbols resolved by name and optional file_id."""

    name: str
    file_id: Optional[str]


T = TypeVar("T", bound=ResolvableSymbol)


def index_symbols(
    symbols: Sequence[T],
) -> tuple[dict[tuple[Optional[str], str], T], dict[str, list[T]]]:
    """Build deterministic lookup indexes for symbol selection.

    Args:
        symbols: Symbols in deterministic declaration order.

    Returns:
        Tuple of `(file_id, name)` exact lookup map and name-grouped candidates.
    """
    symbols_by_key = {(symbol.file_id, symbol.name): symbol for symbol in symbols}
    symbols_by_name: dict[str, list[T]] = {}
    for symbol in symbols:
        symbols_by_name.setdefault(symbol.name, []).append(symbol)
    return symbols_by_key, symbols_by_name


def select_symbol(
    *,
    symbols_by_key: dict[tuple[Optional[str], str], T],
    symbols_by_name: dict[str, list[T]],
    name: str,
    file_id: Optional[str],
    fallback_by_name: dict[str, list[T]] | None = None,
) -> T | None:
    """Select a symbol by exact key first, then deterministic name fallback.

    Args:
        symbols_by_key: Exact `(file_id, name)` lookup map.
        symbols_by_name: Name-grouped candidates used when no exact match exists.
        name: Symbol name to resolve.
        file_id: Optional source file id for exact-match selection.
        fallback_by_name: Optional name-groups used only for fallback selection.

    Returns:
        Selected symbol, or None when no candidate exists.
    """
    if file_id is not None:
        exact = symbols_by_key.get((file_id, name))
        if exact is not None:
            return exact

    fallback_candidates = (
        fallback_by_name.get(name, []) if fallback_by_name is not None else symbols_by_name.get(name, [])
    )
    if len(fallback_candidates) == 1:
        return fallback_candidates[0]
    if fallback_candidates:
        return fallback_candidates[-1]
    return None


def symbol_exists(
    *,
    symbols_by_key: dict[tuple[Optional[str], str], T],
    symbols_by_name: dict[str, list[T]],
    name: str,
    file_id: Optional[str],
    fallback_by_name: dict[str, list[T]] | None = None,
) -> bool:
    """Return whether one symbol resolves under shared selection semantics."""
    return (
        select_symbol(
            symbols_by_key=symbols_by_key,
            symbols_by_name=symbols_by_name,
            name=name,
            file_id=file_id,
            fallback_by_name=fallback_by_name,
        )
        is not None
    )


__all__ = ["index_symbols", "select_symbol", "symbol_exists"]
