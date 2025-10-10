from __future__ import annotations

"""
Neutral textual netlist emitter from the Netlist xDSL dialect.

Emits a SPICE-like, simulator-agnostic deck using `.subckt` / `.ends` and
`X<id>` instance lines with named pin assignments in canonical order.
"""

from typing import List


def _import_xdsl():
    try:
        from xdsl.dialects.builtin import ModuleOp as BuiltinModuleOp  # type: ignore
    except Exception as e:  # pragma: no cover
        raise ImportError(
            "xDSL is not installed. Install with `pip install asdl[xdsl]`."
        ) from e
    return BuiltinModuleOp


def _get_string(attr) -> str:
    # StringAttr
    return getattr(attr, "data", str(attr))


def _get_array_of_strings(array_attr) -> List[str]:
    data = getattr(array_attr, "data", [])
    return [_get_string(x) for x in data]


def emit_netlist_text(builtin_module, dialect: str = "ngspice") -> str:
    """Emit a textual netlist deck from a BuiltinModuleOp that contains netlist.module ops.

    dialect: one of {"ngspice", "neutral"}. Future: {"spectre", "xyce"}.
    - ngspice: positional pins, ".subckt"/".ends" syntax
    - neutral: named pin assignments (pin=net), ".subckt"/".ends" syntax
    """
    BuiltinModuleOp = _import_xdsl()
    if not isinstance(builtin_module, BuiltinModuleOp):  # pragma: no cover
        raise TypeError("emit_netlist_text expects a builtin.module")

    lines: List[str] = []
    # Walk top-level ops
    for op in builtin_module.ops:  # type: ignore[attr-defined]
        if getattr(op, "name", None) == "netlist.module":
            sym_name = _get_string(op.attributes["sym_name"])  # type: ignore[index]
            ports = _get_array_of_strings(op.attributes["ports"])  # type: ignore[index]
            lines.append(f".subckt {sym_name} {' '.join(ports)}")

            # Instances are inside the module's single block
            region = op.regions[0]
            block = region.blocks[0]
            for inst in block.ops:
                if getattr(inst, "name", None) != "netlist.instance":
                    continue
                inst_id = _get_string(inst.attributes["sym_name"])  # type: ignore[index]
                model = _get_string(inst.attributes["model_ref"])  # type: ignore[index]
                pin_map = inst.attributes["pin_map"]  # type: ignore[index]
                pin_order = _get_array_of_strings(inst.attributes["pin_order"])  # type: ignore[index]
                # pin_map is a DictionaryAttr with python str keys and StringAttr values
                if dialect == "neutral":
                    pin_kv = []
                    for pin in pin_order:
                        val_attr = pin_map.data.get(pin)  # type: ignore[attr-defined]
                        net = _get_string(val_attr) if val_attr is not None else ""
                        pin_kv.append(f"{pin}={net}")
                    pins_str = " ".join(pin_kv)
                else:  # ngspice and similar positional syntax
                    nets: List[str] = []
                    for pin in pin_order:
                        val_attr = pin_map.data.get(pin)  # type: ignore[attr-defined]
                        net = _get_string(val_attr) if val_attr is not None else ""
                        nets.append(net)
                    pins_str = " ".join(nets)
                # parameters (dictionary) currently empty in minimal phase
                lines.append(f"X{inst_id} {pins_str} {model}")

            # For portability, emit plain .ends without name
            lines.append(f".ends")

    return "\n".join(lines) + ("\n" if lines else "")


