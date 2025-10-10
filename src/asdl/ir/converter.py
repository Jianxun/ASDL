from __future__ import annotations

"""
AST → xDSL IR converter (Phase 0 skeleton).

This module provides a minimal, opt-in conversion from the ASDL AST to the
ASDL xDSL dialect. It is designed to be safe when the optional dependency is
not installed: import and usage are guarded and will raise ImportError with a
helpful message.
"""

from typing import Tuple

from ..data_structures import ASDLFile, Module, Port


def _import_xdsl_components():
    try:
        from xdsl.ir import MLContext, Region, Block  # type: ignore
        from xdsl.printer import Printer  # type: ignore
        from xdsl.dialects.builtin import (  # type: ignore
            ModuleOp as BuiltinModuleOp,
            ArrayAttr,
            DictionaryAttr,
            StringAttr,
        )
    except Exception as e:  # pragma: no cover - exercised only if optional dep missing
        raise ImportError(
            "xDSL is not installed. Install with `pip install asdl[xdsl]` to use the xdsl engine."
        ) from e
    return MLContext, Region, Block, Printer, BuiltinModuleOp, ArrayAttr, DictionaryAttr, StringAttr


def asdl_ast_to_xdsl_module(asdl_file: ASDLFile):
    """
    Convert an ASDLFile AST to an xDSL Builtin ModuleOp containing asdl.module ops.

    Returns (mlctx, builtin_module_op).
    """
    (
        MLContext,
        Region,
        Block,
        Printer,
        BuiltinModuleOp,
        ArrayAttr,
        DictionaryAttr,
        StringAttr,
    ) = _import_xdsl_components()

    from .xdsl_dialect import register_asdl_dialect
    from .xdsl_dialect.ops import ModuleOp as AsdlModuleOp
    from .xdsl_dialect.attrs import PortAttr

    mlctx = register_asdl_dialect(None)

    ops = []
    for name, mod in (asdl_file.modules or {}).items():
        ports_attr = _ports_to_attr(ArrayAttr, PortAttr, StringAttr, mod)
        asdl_mod = AsdlModuleOp.build(
            attributes={
                "sym_name": StringAttr.get(name),
                "parameters": DictionaryAttr.from_dict({}),
                "variables": DictionaryAttr.from_dict({}),
                "ports": ports_attr,
            },
            regions=[Region(Block())],
        )
        ops.append(asdl_mod)

    top = BuiltinModuleOp.from_region_or_ops(ops)
    return mlctx, top


def print_xdsl_module(mlctx, module_op) -> str:
    """Render the xDSL module to textual form using xDSL's printer."""
    from io import StringIO
    from xdsl.printer import Printer  # type: ignore

    buf = StringIO()
    printer = Printer(stream=buf, context=mlctx)
    printer.print_op(module_op)
    text = buf.getvalue()
    return text


def _ports_to_attr(ArrayAttr, PortAttr, StringAttr, mod: Module):
    ports = mod.ports or {}
    items = []
    for port_name, port in ports.items():
        dir_str = getattr(port.dir, "value", str(port.dir))
        kind_str = getattr(port.type, "value", str(port.type))
        items.append(
            PortAttr([StringAttr.get(port_name), StringAttr.get(dir_str), StringAttr.get(kind_str)])
        )
    return ArrayAttr(items)


