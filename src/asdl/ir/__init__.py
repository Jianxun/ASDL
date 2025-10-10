"""
ASDL IR scaffold (Phase 0)

This package provides a minimal textual IR view built from the existing AST,
serving as a placeholder until the xDSL-backed dialect is wired in.
"""

from .textual import build_textual_ir
try:
    # Optional: only available when xDSL extra is installed
    from .xdsl_dialect import register_asdl_dialect  # type: ignore
except Exception:  # pragma: no cover - optional dependency not installed
    register_asdl_dialect = None  # type: ignore

__all__ = [
    "build_textual_ir",
    "register_asdl_dialect",
]


