"""Endpoint expression splitting helpers for GraphIR metadata."""

from __future__ import annotations


def split_endpoint_atom(atom: str) -> tuple[str, str]:
    """Split an expanded endpoint atom into instance and port names.

    Args:
        atom: Expanded endpoint atom (e.g., "inst.pin").

    Returns:
        Tuple of (instance_name, port_name).
    """
    if atom.count(".") != 1:
        raise ValueError(f"Endpoint atom must contain exactly one '.', got '{atom}'.")
    inst, port = atom.split(".")
    if not inst or not port:
        raise ValueError(f"Endpoint atom must include instance and port, got '{atom}'.")
    return inst, port


__all__ = ["split_endpoint_atom"]
