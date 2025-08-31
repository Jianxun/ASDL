"""
ASDL validator package.

Exposes `ASDLValidator` as the package-level symbol to preserve the
public API `from src.asdl.validator import ASDLValidator`.
"""

from .core.runner import ASDLValidator

__all__ = [
    "ASDLValidator",
]


