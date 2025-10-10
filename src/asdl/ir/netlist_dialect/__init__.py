"""
Netlist xDSL dialect registration helpers.

Defines a minimal simulator-agnostic netlist dialect with subcircuits and
instances. Optional import guarded by xDSL availability.
"""

from __future__ import annotations

from typing import Any


def _import_xdsl() -> Any:
    try:
        from xdsl.ir import Dialect, MLContext  # type: ignore
    except Exception as e:  # pragma: no cover
        raise ImportError(
            "xDSL is not installed. Install with `pip install asdl[xdsl]`."
        ) from e
    return Dialect, MLContext


def register_netlist_dialect(context: object | None = None) -> object:
    Dialect, MLContext = _import_xdsl()
    from .ops import ModuleOp, InstanceOp  # noqa: WPS433

    mlctx = context if isinstance(context, MLContext) else MLContext()
    netlist_dialect = Dialect(
        "netlist",
        ops=[ModuleOp, InstanceOp],
        attrs=[],
    )
    mlctx.register_dialect(netlist_dialect)
    try:  # pragma: no cover
        from xdsl.dialects.builtin import Builtin  # type: ignore
        mlctx.register_dialect(Builtin)
    except Exception:
        pass
    return mlctx


__all__ = [
    "register_netlist_dialect",
]


