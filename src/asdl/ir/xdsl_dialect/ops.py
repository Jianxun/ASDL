from __future__ import annotations

# Minimal operation stubs to enable early registration and tests.
# These will gain operands/regions/attributes and verifiers in later phases.

try:  # Optional dependency: only import if xdsl is installed
    from xdsl.ir import Operation
    from xdsl.irdl import IRDLOperation
    from xdsl.irdl import irdl_op_definition
except Exception:  # pragma: no cover - exercised only if optional dep missing
    Operation = object  # type: ignore
    def irdl_op_definition(cls):  # type: ignore
        return cls


@irdl_op_definition
class ModuleOp(Operation):  # type: ignore[misc]
    name = "asdl.module"


@irdl_op_definition
class WireOp(Operation):  # type: ignore[misc]
    name = "asdl.wire"


@irdl_op_definition
class InstanceOp(Operation):  # type: ignore[misc]
    name = "asdl.instance"


__all__ = [
    "ModuleOp",
    "WireOp",
    "InstanceOp",
]


