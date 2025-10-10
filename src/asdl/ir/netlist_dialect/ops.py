from __future__ import annotations

# Minimal xDSL op definitions for the netlist dialect, guarded on optional dep.

try:  # Optional dependency
    from xdsl.irdl import IRDLOperation, irdl_op_definition, attr_def, region_def
    from xdsl.dialects.builtin import ArrayAttr, StringAttr, DictionaryAttr
except Exception:  # pragma: no cover
    IRDLOperation = object  # type: ignore
    def irdl_op_definition(cls):  # type: ignore
        return cls
    def attr_def(arg):  # type: ignore
        return None
    def region_def():  # type: ignore
        return None
    class ArrayAttr:  # type: ignore
        pass
    class StringAttr:  # type: ignore
        pass
    class DictionaryAttr:  # type: ignore
        pass


@irdl_op_definition
class ModuleOp(IRDLOperation):  # type: ignore[misc]
    name = "netlist.module"
    sym_name = attr_def(StringAttr)
    ports = attr_def(ArrayAttr[StringAttr])
    parameters = attr_def(DictionaryAttr)
    body = region_def()


@irdl_op_definition
class InstanceOp(IRDLOperation):  # type: ignore[misc]
    name = "netlist.instance"
    sym_name = attr_def(StringAttr)
    model_ref = attr_def(StringAttr)
    # Named pin mapping; preserves semantic connectivity
    pin_map = attr_def(DictionaryAttr)
    # Callee port order for positional-only backends
    pin_order = attr_def(ArrayAttr[StringAttr])
    parameters = attr_def(DictionaryAttr)


__all__ = [
    "ModuleOp",
    "InstanceOp",
]


