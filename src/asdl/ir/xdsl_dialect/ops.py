from __future__ import annotations

# Minimal operation definitions using xDSL IRDL when available. Fallbacks are no-ops
# to keep imports working without the optional dependency installed.

try:  # Optional dependency: only import if xdsl is installed
    from xdsl.ir import Operation
    from xdsl.irdl import (
        IRDLOperation,
        irdl_op_definition,
        attr_def,
        Operand,
        VarOperand,
        Region,
        AttrSizedOperandSegments,
    )
    from xdsl.dialects.builtin import ArrayAttr, StringAttr, DictionaryAttr
    from .attrs import PortAttr
except Exception:  # pragma: no cover - exercised only if optional dep missing
    Operation = object  # type: ignore
    def irdl_op_definition(cls):  # type: ignore
        return cls
    def attr_def(arg):  # type: ignore
        return None
    class Operand:  # type: ignore
        pass
    class VarOperand:  # type: ignore
        pass
    class Region:  # type: ignore
        pass
    class AttrSizedOperandSegments:  # type: ignore
        pass
    class ArrayAttr:  # type: ignore
        pass
    class StringAttr:  # type: ignore
        pass
    class DictionaryAttr:  # type: ignore
        pass
    class PortAttr:  # type: ignore
        pass


@irdl_op_definition
class ModuleOp(IRDLOperation):  # type: ignore[misc]
    name = "asdl.module"
    # Single region with one block (entry);
    # ports are represented as an array attribute for stable ordering
    ports = attr_def(ArrayAttr[PortAttr])
    parameters = attr_def(DictionaryAttr)
    variables = attr_def(DictionaryAttr)
    sym_name = attr_def(StringAttr)
    region: Region


@irdl_op_definition
class WireOp(IRDLOperation):  # type: ignore[misc]
    name = "asdl.wire"
    sym_name = attr_def(StringAttr)


@irdl_op_definition
class InstanceOp(IRDLOperation):  # type: ignore[misc]
    name = "asdl.instance"
    sym_name = attr_def(StringAttr)
    model_ref = attr_def(StringAttr)
    parameters = attr_def(DictionaryAttr)
    pins = attr_def(ArrayAttr[StringAttr])
    # Operands reference wires in pin order
    operands: VarOperand


__all__ = [
    "ModuleOp",
    "WireOp",
    "InstanceOp",
]


