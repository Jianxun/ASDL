from __future__ import annotations

# Minimal attribute definitions using xDSL IRDL when available. Fallbacks are no-ops
# to keep imports working without the optional dependency installed.

try:  # Optional dependency: only import if xdsl is installed
    from xdsl.ir import Attribute
    from xdsl.irdl import ParameterDef, irdl_attr_definition
    from xdsl.dialects.builtin import StringAttr, IntegerAttr
except Exception:  # pragma: no cover - exercised only if optional dep missing
    Attribute = object  # type: ignore
    def irdl_attr_definition(cls):  # type: ignore
        return cls
    class StringAttr:  # type: ignore
        pass
    class IntegerAttr:  # type: ignore
        pass
    class ParameterDef:  # type: ignore
        def __class_getitem__(cls, item):
            return cls


@irdl_attr_definition
class PortAttr(Attribute):  # type: ignore[misc]
    name = "asdl.port"
    port_name: ParameterDef[StringAttr]
    direction: ParameterDef[StringAttr]
    kind: ParameterDef[StringAttr]


@irdl_attr_definition
class RangeAttr(Attribute):  # type: ignore[misc]
    name = "asdl.range"
    msb: ParameterDef[IntegerAttr]
    lsb: ParameterDef[IntegerAttr]


@irdl_attr_definition
class ExprAttr(Attribute):  # type: ignore[misc]
    name = "asdl.expr"
    # textual expression placeholder; will be resolved in later passes
    expr: ParameterDef[StringAttr]


__all__ = [
    "PortAttr",
    "RangeAttr",
    "ExprAttr",
]


