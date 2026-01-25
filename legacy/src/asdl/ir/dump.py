"""Canonical textual dump helpers for GraphIR and IFIR."""

from __future__ import annotations

import io

from xdsl.ir import Operation
from xdsl.printer import Printer

from asdl.ir.graphir import ProgramOp
from asdl.ir.ifir import DesignOp


def _dump_op(op: Operation) -> str:
    """Render an xDSL operation using the canonical printer settings.

    Args:
        op: Operation to render.

    Returns:
        Canonical textual representation with a trailing newline.

    Side Effects:
        None.

    Invariants:
        Uses xDSL Printer defaults (no debuginfo) and preserves region and
        dictionary insertion order.
    """
    stream = io.StringIO()
    printer = Printer(stream=stream)
    printer.print_op(op)
    text = stream.getvalue()
    if not text.endswith("\n"):
        text += "\n"
    return text


def dump_graphir(program: ProgramOp) -> str:
    """Return the canonical GraphIR program dump.

    Args:
        program: GraphIR program op to dump.

    Returns:
        Canonical textual representation with a trailing newline.

    Side Effects:
        None.

    Invariants:
        Output preserves region order and dictionary insertion order.
    """
    return _dump_op(program)


def dump_ifir(design: DesignOp) -> str:
    """Return the canonical IFIR design dump.

    Args:
        design: IFIR design op to dump.

    Returns:
        Canonical textual representation with a trailing newline.

    Side Effects:
        None.

    Invariants:
        Output preserves region order and dictionary insertion order.
    """
    return _dump_op(design)


__all__ = ["dump_graphir", "dump_ifir"]
