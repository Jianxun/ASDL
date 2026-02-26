"""Shared helpers for dotted hierarchy instance paths."""

from __future__ import annotations


def join_hierarchy_path(parent_path: str, instance: str) -> str:
    """Join a parent hierarchy path and instance leaf into one dotted path.

    Args:
        parent_path: Parent hierarchy path, or empty string for root.
        instance: Instance leaf name.

    Returns:
        Full dotted hierarchy path.
    """
    if parent_path:
        return f"{parent_path}.{instance}"
    return instance


def is_path_within_scope(full_path: str, scope_path: str) -> bool:
    """Return whether `full_path` is exactly or transitively under `scope_path`.

    Args:
        full_path: Fully qualified hierarchy path to test.
        scope_path: Scope anchor path.

    Returns:
        True when `full_path` equals `scope_path` or is a descendant.
    """
    return full_path == scope_path or full_path.startswith(f"{scope_path}.")


__all__ = ["is_path_within_scope", "join_hierarchy_path"]
