"""
ASDL xDSL dialect registration helpers.

This package defines the ASDL dialect's operations and attributes backed by xDSL.
It is optional and imported only when explicitly used to avoid hard dependency
when the `xdsl` extra is not installed.
"""

from __future__ import annotations

from typing import Any


def _import_xdsl() -> Any:
    """Import xDSL lazily and raise a helpful message if unavailable."""
    try:
        # Import core xDSL bits only when needed
        from xdsl.ir import Dialect, MLContext  # type: ignore
    except Exception as e:  # pragma: no cover - exercised only if optional dep missing
        raise ImportError(
            "xDSL is not installed. Install with `pip install asdl[xdsl]` or add the `xdsl` "
            "optional dependency in pyproject.toml."
        ) from e
    return Dialect, MLContext


def register_asdl_dialect(context: object | None = None) -> object:
    """
    Register the ASDL dialect in a provided MLContext (or create one).

    Returns the MLContext used for registration to enable chaining.
    """
    Dialect, MLContext = _import_xdsl()
    # Import ops/attrs after ensuring xDSL is present
    from .ops import ModuleOp, WireOp, InstanceOp  # noqa: WPS433
    from .attrs import PortAttr, RangeAttr, ExprAttr  # noqa: WPS433

    mlctx = context if isinstance(context, MLContext) else MLContext()
    asdl_dialect = Dialect(
        "asdl",
        ops=[ModuleOp, WireOp, InstanceOp],
        attrs=[PortAttr, RangeAttr, ExprAttr],
    )
    mlctx.register_dialect(asdl_dialect)
    return mlctx


__all__ = [
    "register_asdl_dialect",
]


