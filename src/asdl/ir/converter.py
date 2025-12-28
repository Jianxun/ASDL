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
        from xdsl.ir import Region, Block  # type: ignore
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
    return Region, Block, Printer, BuiltinModuleOp, ArrayAttr, DictionaryAttr, StringAttr


def asdl_ast_to_xdsl_module(asdl_file: ASDLFile):
    """
    Convert an ASDLFile AST to an xDSL Builtin ModuleOp containing asdl.module ops.

    Returns (mlctx, builtin_module_op).
    """
    (
        Region,
        Block,
        Printer,
        BuiltinModuleOp,
        ArrayAttr,
        DictionaryAttr,
        StringAttr,
    ) = _import_xdsl_components()

    # Import op classes so their IRDL definitions are available
    from .xdsl_dialect.ops import ModuleOp as AsdlModuleOp

    ops = []
    for name, mod in (asdl_file.modules or {}).items():
        ports_attr = _ports_to_attr(ArrayAttr, StringAttr, mod)
        asdl_mod = AsdlModuleOp.build(
            attributes={
                "sym_name": StringAttr.get(name),
                "parameters": DictionaryAttr({}),
                "variables": DictionaryAttr({}),
                "ports": ports_attr,
            },
            regions=[Region(Block())],
        )
        ops.append(asdl_mod)

    top = BuiltinModuleOp(ops=ops)
    return top


def _import_netlist_components():
    try:
        from xdsl.ir import Region, Block  # type: ignore
        from xdsl.dialects.builtin import (  # type: ignore
            ModuleOp as BuiltinModuleOp,
            ArrayAttr,
            DictionaryAttr,
            StringAttr,
        )
    except Exception as e:  # pragma: no cover
        raise ImportError(
            "xDSL is not installed. Install with `pip install asdl[xdsl]` to use the xdsl engine."
        ) from e
    return Region, Block, BuiltinModuleOp, ArrayAttr, DictionaryAttr, StringAttr


def asdl_ast_to_netlist_module(asdl_file: ASDLFile):
    """Lower ASDL AST directly to netlist dialect (minimal phase)."""
    (
        Region,
        Block,
        BuiltinModuleOp,
        ArrayAttr,
        DictionaryAttr,
        StringAttr,
    ) = _import_netlist_components()

    from .netlist_dialect.ops import ModuleOp as NLModuleOp, InstanceOp as NLInstanceOp

    ops = []
    modules = asdl_file.modules or {}

    # Precompute port orders for callee modules
    port_order_by_module: dict[str, list[str]] = {}
    for mod_name, mod in modules.items():
        port_order_by_module[mod_name] = list((mod.ports or {}).keys())

    for name, mod in modules.items():
        ports_attr = ArrayAttr([StringAttr.get(p) for p in port_order_by_module[name]])
        nl_mod = NLModuleOp.build(
            attributes={
                "sym_name": StringAttr.get(name),
                "ports": ports_attr,
                "parameters": DictionaryAttr({}),
            },
            regions=[Region(Block())],
        )

        # Populate instances in module body (minimal, no nets SSA)
        block = nl_mod.regions[0].blocks[0]
        for inst_id, inst in (mod.instances or {}).items():
            # pin_map: DictAttr expects Python str keys -> Attribute values
            pin_map_dict = {k: StringAttr.get(v) for k, v in (inst.mappings or {}).items()}
            pin_map_attr = DictionaryAttr(pin_map_dict)
            # pin_order from callee declaration if available, else use mapping keys order
            callee_ports = port_order_by_module.get(inst.model, list((inst.mappings or {}).keys()))
            pin_order_attr = ArrayAttr([StringAttr.get(p) for p in callee_ports])
            nl_inst = NLInstanceOp.build(
                attributes={
                    "sym_name": StringAttr.get(inst_id),
                    "model_ref": StringAttr.get(inst.model),
                    "pin_map": pin_map_attr,
                    "pin_order": pin_order_attr,
                    "parameters": DictionaryAttr({}),
                }
            )
            block.add_op(nl_inst)

        ops.append(nl_mod)

    top = BuiltinModuleOp(ops=ops)
    return top


def print_xdsl_module(module_op) -> str:
    """Render the xDSL module to textual form using xDSL's printer."""
    from io import StringIO
    from xdsl.printer import Printer  # type: ignore

    buf = StringIO()
    printer = Printer(stream=buf)
    printer.print_op(module_op)
    text = buf.getvalue()
    return text


def _ports_to_attr(ArrayAttr, StringAttr, mod: Module):
    ports = mod.ports or {}
    items = []
    for port_name, port in ports.items():
        items.append(StringAttr.get(port_name))
    return ArrayAttr(items)


