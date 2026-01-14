"""Pattern expansion and atomization API."""

from __future__ import annotations

from .atomize import AtomizedEndpoint, AtomizedPattern, atomize_endpoint, atomize_pattern
from .diagnostics import (
    MAX_EXPANSION_SIZE,
    PATTERN_DUPLICATE_ATOM,
    PATTERN_EMPTY_ENUM,
    PATTERN_EMPTY_SPLICE,
    PATTERN_INVALID_RANGE,
    PATTERN_TOO_LARGE,
    PATTERN_UNEXPANDED,
)
from .expand import expand_endpoint, expand_pattern
from .verify import (
    collect_literal_collisions,
    format_endpoint_length_mismatch,
    format_literal_collision_message,
    format_param_length_mismatch,
)

__all__ = [
    "AtomizedEndpoint",
    "AtomizedPattern",
    "MAX_EXPANSION_SIZE",
    "PATTERN_INVALID_RANGE",
    "PATTERN_EMPTY_ENUM",
    "PATTERN_EMPTY_SPLICE",
    "PATTERN_DUPLICATE_ATOM",
    "PATTERN_TOO_LARGE",
    "PATTERN_UNEXPANDED",
    "atomize_endpoint",
    "atomize_pattern",
    "collect_literal_collisions",
    "expand_endpoint",
    "expand_pattern",
    "format_endpoint_length_mismatch",
    "format_literal_collision_message",
    "format_param_length_mismatch",
]
