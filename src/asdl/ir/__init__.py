"""
ASDL IR scaffold (Phase 0)

This package provides a minimal textual IR view built from the existing AST,
serving as a placeholder until the xDSL-backed dialect is wired in.
"""

from .textual import build_textual_ir

__all__ = [
    "build_textual_ir",
]


