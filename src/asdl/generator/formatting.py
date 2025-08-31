from __future__ import annotations

from typing import Dict, List

from ..data_structures import Module


def get_port_list(module: Module) -> List[str]:
    """Return ordered list of port names preserving declaration order."""
    if not module.ports:
        return []
    return list(module.ports.keys())


def format_named_parameters(params: Dict[str, object]) -> str:
    """Format parameters as sorted param=value pairs."""
    if not params:
        return ""
    parts: List[str] = []
    for name in sorted(params.keys()):
        parts.append(f"{name}={params[name]}")
    return " ".join(parts)


