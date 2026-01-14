"""GraphIR attribute definitions and coercion helpers."""

from __future__ import annotations

from xdsl.dialects.builtin import StringAttr
from xdsl.ir import ParametrizedAttribute
from xdsl.irdl import irdl_attr_definition, param_def


@irdl_attr_definition
class GraphIdAttr(ParametrizedAttribute):
    """Stable opaque identifier for GraphIR entities.

    Attributes:
        value: The serialized identifier string.
    """

    name = "graphir.graph_id"

    value: StringAttr = param_def()


@irdl_attr_definition
class GraphSymbolRefAttr(ParametrizedAttribute):
    """Resolved symbol reference for GraphIR instances.

    Attributes:
        kind: Symbol kind ("module" or "device").
        sym_id: Stable symbol identifier.
    """

    name = "graphir.symbol_ref"

    kind: StringAttr = param_def()
    sym_id: GraphIdAttr = param_def()


def _coerce_graph_id(value: GraphIdAttr | StringAttr | str | int) -> GraphIdAttr:
    """Coerce a Python value into a GraphIdAttr.

    Args:
        value: The value to convert (string, int, or attribute).

    Returns:
        A GraphIdAttr with a normalized string payload.
    """
    if isinstance(value, GraphIdAttr):
        return value
    if isinstance(value, StringAttr):
        return GraphIdAttr(value)
    if isinstance(value, int):
        value = str(value)
    if isinstance(value, str):
        return GraphIdAttr(StringAttr(value))
    raise TypeError(f"Unsupported GraphId value: {value!r}")


def _coerce_graph_symbol_ref(
    value: GraphSymbolRefAttr
    | tuple[str | StringAttr, GraphIdAttr | StringAttr | str | int],
) -> GraphSymbolRefAttr:
    """Coerce a Python value into a GraphSymbolRefAttr.

    Args:
        value: GraphSymbolRefAttr or (kind, id) tuple.

    Returns:
        A GraphSymbolRefAttr instance.
    """
    if isinstance(value, GraphSymbolRefAttr):
        return value
    if isinstance(value, tuple) and len(value) == 2:
        kind, sym_id = value
        if isinstance(kind, str):
            kind = StringAttr(kind)
        if not isinstance(kind, StringAttr):
            raise TypeError(f"Unsupported symbol kind: {kind!r}")
        sym_id = _coerce_graph_id(sym_id)
        return GraphSymbolRefAttr(kind, sym_id)
    raise TypeError(f"Unsupported symbol ref: {value!r}")
