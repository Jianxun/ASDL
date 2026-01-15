"""GraphIR attribute definitions and coercion helpers."""

from __future__ import annotations

from xdsl.dialects.builtin import ArrayAttr, IntAttr, StringAttr
from xdsl.ir import Attribute, ParametrizedAttribute
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


@irdl_attr_definition
class GraphParamRefAttr(ParametrizedAttribute):
    """Reference to an instance parameter for pattern ownership.

    Attributes:
        inst_id: Stable instance identifier.
        param_name: Parameter name.
    """

    name = "graphir.param_ref"

    inst_id: GraphIdAttr = param_def()
    param_name: StringAttr = param_def()


@irdl_attr_definition
class GraphPatternOriginAttr(ParametrizedAttribute):
    """Pattern provenance metadata for GraphIR atomized names.

    Attributes:
        expression_id: Pattern expression table key.
        segment_index: 0-based segment index within the expression.
        base_name: Base name for the pattern.
        pattern_parts: Ordered list of string or integer substitutions.
    """

    name = "graphir.pattern_origin"

    expression_id: StringAttr = param_def()
    segment_index: IntAttr = param_def()
    base_name: StringAttr = param_def()
    pattern_parts: ArrayAttr = param_def()


PatternOriginInput = GraphPatternOriginAttr | tuple[
    StringAttr | str,
    IntAttr | int,
    StringAttr | str,
    ArrayAttr | list[StringAttr | IntAttr | str | int],
]


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


def _coerce_graph_param_ref(
    value: GraphParamRefAttr
    | tuple[GraphIdAttr | StringAttr | str | int, StringAttr | str],
) -> GraphParamRefAttr:
    """Coerce a Python value into a GraphParamRefAttr.

    Args:
        value: GraphParamRefAttr or (inst_id, param_name) tuple.

    Returns:
        A GraphParamRefAttr instance.
    """
    if isinstance(value, GraphParamRefAttr):
        return value
    if isinstance(value, tuple) and len(value) == 2:
        inst_id, param_name = value
        inst_id = _coerce_graph_id(inst_id)
        if isinstance(param_name, str):
            param_name = StringAttr(param_name)
        if not isinstance(param_name, StringAttr):
            raise TypeError(f"Unsupported param name: {param_name!r}")
        return GraphParamRefAttr(inst_id, param_name)
    raise TypeError(f"Unsupported param ref: {value!r}")


def _coerce_pattern_parts(
    value: ArrayAttr | list[StringAttr | IntAttr | str | int],
) -> ArrayAttr:
    """Coerce pattern parts into an ArrayAttr of StringAttr/IntAttr.

    Args:
        value: ArrayAttr or list of string/integer parts.

    Returns:
        ArrayAttr containing only StringAttr and IntAttr elements.
    """
    if isinstance(value, ArrayAttr):
        for item in value.data:
            if not isinstance(item, (StringAttr, IntAttr)):
                raise TypeError(f"Unsupported pattern part: {item!r}")
        return value
    parts: list[Attribute] = []
    for item in value:
        if isinstance(item, (StringAttr, IntAttr)):
            parts.append(item)
            continue
        if isinstance(item, str):
            parts.append(StringAttr(item))
            continue
        if isinstance(item, int):
            parts.append(IntAttr(item))
            continue
        raise TypeError(f"Unsupported pattern part: {item!r}")
    return ArrayAttr(parts)


def _coerce_graph_pattern_origin(value: PatternOriginInput) -> GraphPatternOriginAttr:
    """Coerce a Python value into a GraphPatternOriginAttr.

    Args:
        value: GraphPatternOriginAttr or tuple payload.

    Returns:
        GraphPatternOriginAttr with normalized attributes.
    """
    if isinstance(value, GraphPatternOriginAttr):
        return value
    if isinstance(value, tuple) and len(value) == 4:
        expression_id, segment_index, base_name, pattern_parts = value
        if isinstance(expression_id, str):
            expression_id = StringAttr(expression_id)
        if not isinstance(expression_id, StringAttr):
            raise TypeError(f"Unsupported expression id: {expression_id!r}")
        if isinstance(segment_index, int):
            segment_index = IntAttr(segment_index)
        if not isinstance(segment_index, IntAttr):
            raise TypeError(f"Unsupported segment index: {segment_index!r}")
        if isinstance(base_name, str):
            base_name = StringAttr(base_name)
        if not isinstance(base_name, StringAttr):
            raise TypeError(f"Unsupported base name: {base_name!r}")
        pattern_parts = _coerce_pattern_parts(pattern_parts)
        return GraphPatternOriginAttr(
            expression_id, segment_index, base_name, pattern_parts
        )
    raise TypeError(f"Unsupported pattern origin: {value!r}")
