"""GraphIR graph ops for nets, instances, and endpoints."""

from __future__ import annotations

from typing import Sequence

from xdsl.dialects.builtin import DictionaryAttr, StringAttr
from xdsl.ir import Block, Operation, Region
from xdsl.irdl import (
    IRDLOperation,
    attr_def,
    irdl_op_definition,
    opt_attr_def,
    region_def,
    traits_def,
)
from xdsl.traits import IsolatedFromAbove, NoTerminator
from xdsl.utils.exceptions import VerifyException

from .attrs import GraphIdAttr, GraphSymbolRefAttr, _coerce_graph_id, _coerce_graph_symbol_ref


@irdl_op_definition
class NetOp(IRDLOperation):
    """GraphIR net definition.

    Attributes:
        net_id: Stable net identifier.
        name: Net name.
        attrs: Optional net attributes.
        annotations: Optional annotations.
    """

    name = "graphir.net"

    net_id = attr_def(GraphIdAttr)
    name_attr = attr_def(StringAttr, attr_name="name")
    attrs = opt_attr_def(DictionaryAttr)
    annotations = opt_attr_def(DictionaryAttr)
    body = region_def("single_block")

    traits = traits_def(IsolatedFromAbove(), NoTerminator())
    assembly_format = "$body attr-dict"

    def __init__(
        self,
        *,
        net_id: GraphIdAttr | StringAttr | str | int,
        name: StringAttr | str,
        region: Region | Sequence[Operation],
        attrs: DictionaryAttr | None = None,
        annotations: DictionaryAttr | None = None,
    ) -> None:
        """Initialize a net op.

        Args:
            net_id: Stable net identifier.
            name: Net name.
            region: Region containing endpoint ops.
            attrs: Optional net attributes.
            annotations: Optional annotations dictionary.
        """
        if isinstance(name, str):
            name = StringAttr(name)
        net_id = _coerce_graph_id(net_id)
        attributes = {"net_id": net_id, "name": name}
        if attrs is not None:
            attributes["attrs"] = attrs
        if annotations is not None:
            attributes["annotations"] = annotations
        if isinstance(region, Region):
            body = region
        else:
            body = Region(Block(region))
        super().__init__(attributes=attributes, regions=[body])

    def verify_(self) -> None:
        """Verify net region contents."""
        for op in self.body.block.ops:
            if not isinstance(op, EndpointOp):
                raise VerifyException("graphir.net region must contain only endpoint ops")


@irdl_op_definition
class InstanceOp(IRDLOperation):
    """GraphIR instance definition.

    Attributes:
        inst_id: Stable instance identifier.
        name: Instance name.
        module_ref: Resolved module/device reference.
        module_ref_raw: Original textual reference.
        props: Optional properties.
        annotations: Optional annotations.
    """

    name = "graphir.instance"

    inst_id = attr_def(GraphIdAttr)
    name_attr = attr_def(StringAttr, attr_name="name")
    module_ref = attr_def(GraphSymbolRefAttr)
    module_ref_raw = attr_def(StringAttr)
    props = opt_attr_def(DictionaryAttr)
    annotations = opt_attr_def(DictionaryAttr)

    assembly_format = "attr-dict"

    def __init__(
        self,
        *,
        inst_id: GraphIdAttr | StringAttr | str | int,
        name: StringAttr | str,
        module_ref: GraphSymbolRefAttr
        | tuple[str | StringAttr, GraphIdAttr | StringAttr | str | int],
        module_ref_raw: StringAttr | str,
        props: DictionaryAttr | None = None,
        annotations: DictionaryAttr | None = None,
    ) -> None:
        """Initialize an instance op.

        Args:
            inst_id: Stable instance identifier.
            name: Instance name.
            module_ref: Resolved module/device reference.
            module_ref_raw: Original textual reference.
            props: Optional property dictionary.
            annotations: Optional annotations dictionary.
        """
        if isinstance(name, str):
            name = StringAttr(name)
        if isinstance(module_ref_raw, str):
            module_ref_raw = StringAttr(module_ref_raw)
        inst_id = _coerce_graph_id(inst_id)
        module_ref = _coerce_graph_symbol_ref(module_ref)
        attributes = {
            "inst_id": inst_id,
            "name": name,
            "module_ref": module_ref,
            "module_ref_raw": module_ref_raw,
        }
        if props is not None:
            attributes["props"] = props
        if annotations is not None:
            attributes["annotations"] = annotations
        super().__init__(attributes=attributes)


@irdl_op_definition
class EndpointOp(IRDLOperation):
    """GraphIR endpoint definition.

    Attributes:
        endpoint_id: Stable endpoint identifier.
        inst_id: Stable instance identifier.
        port_path: Port path string.
    """

    name = "graphir.endpoint"

    endpoint_id = attr_def(GraphIdAttr)
    inst_id = attr_def(GraphIdAttr)
    port_path = attr_def(StringAttr)

    assembly_format = "attr-dict"

    def __init__(
        self,
        *,
        endpoint_id: GraphIdAttr | StringAttr | str | int,
        inst_id: GraphIdAttr | StringAttr | str | int,
        port_path: StringAttr | str,
    ) -> None:
        """Initialize an endpoint op.

        Args:
            endpoint_id: Stable endpoint identifier.
            inst_id: Stable instance identifier.
            port_path: Port path string.
        """
        if isinstance(port_path, str):
            port_path = StringAttr(port_path)
        endpoint_id = _coerce_graph_id(endpoint_id)
        inst_id = _coerce_graph_id(inst_id)
        attributes = {
            "endpoint_id": endpoint_id,
            "inst_id": inst_id,
            "port_path": port_path,
        }
        super().__init__(attributes=attributes)


__all__ = ["EndpointOp", "InstanceOp", "NetOp"]
