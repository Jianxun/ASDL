"""GraphIR module and device ops."""

from __future__ import annotations

from typing import Iterable, Sequence

from xdsl.dialects.builtin import ArrayAttr, DictionaryAttr, StringAttr
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

from .attrs import GraphIdAttr, _coerce_graph_id
from .ops_graph import EndpointOp, InstanceOp, NetOp

PORT_ORDER_KEY = "port_order"
PATTERN_EXPRESSION_TABLE_KEY = "pattern_expression_table"


def _normalize_port_order(
    port_order: ArrayAttr[StringAttr] | Iterable[str] | None,
) -> ArrayAttr[StringAttr] | None:
    """Normalize a port order sequence into an ArrayAttr.

    Args:
        port_order: Iterable of port names or an ArrayAttr of StringAttr.

    Returns:
        An ArrayAttr of StringAttr, or None if no port order is provided.
    """
    if port_order is None:
        return None
    if isinstance(port_order, ArrayAttr):
        return port_order
    return ArrayAttr([StringAttr(item) for item in port_order])


def _merge_module_attrs(
    attrs: DictionaryAttr | None,
    port_order: ArrayAttr[StringAttr] | None,
    pattern_expression_table: DictionaryAttr | None,
) -> DictionaryAttr | None:
    """Merge module attrs with reserved GraphIR metadata entries.

    Args:
        attrs: Existing attrs dictionary.
        port_order: Normalized port order to inject.
        pattern_expression_table: Optional pattern expression table.

    Returns:
        A DictionaryAttr containing merged data, or None if empty.
    """
    if attrs is None and port_order is None and pattern_expression_table is None:
        return None
    merged = dict(attrs.data) if attrs is not None else {}
    if port_order is not None:
        merged[PORT_ORDER_KEY] = port_order
    if pattern_expression_table is not None:
        merged[PATTERN_EXPRESSION_TABLE_KEY] = pattern_expression_table
    return DictionaryAttr(merged)


@irdl_op_definition
class ModuleOp(IRDLOperation):
    """GraphIR module graph container.

    Attributes:
        module_id: Stable module identifier.
        name: Module symbol name.
        file_id: Source file identifier.
        attrs: Optional module attributes (includes port_order/table).
        annotations: Optional annotations.
    """

    name = "graphir.module"

    module_id = attr_def(GraphIdAttr)
    name_attr = attr_def(StringAttr, attr_name="name")
    file_id = attr_def(StringAttr)
    attrs = opt_attr_def(DictionaryAttr)
    annotations = opt_attr_def(DictionaryAttr)
    body = region_def("single_block")

    traits = traits_def(IsolatedFromAbove(), NoTerminator())
    assembly_format = "$body attr-dict"

    def __init__(
        self,
        *,
        module_id: GraphIdAttr | StringAttr | str | int,
        name: StringAttr | str,
        file_id: StringAttr | str,
        region: Region | Sequence[Operation],
        port_order: ArrayAttr[StringAttr] | Iterable[str] | None = None,
        pattern_expression_table: DictionaryAttr | None = None,
        attrs: DictionaryAttr | None = None,
        annotations: DictionaryAttr | None = None,
    ) -> None:
        """Initialize a module op.

        Args:
            module_id: Stable module identifier.
            name: Module symbol name.
            file_id: Source file identifier.
            region: Region containing module contents.
            port_order: Optional port order list stored in attrs.
            pattern_expression_table: Optional pattern expression table attrs.
            attrs: Optional attribute dictionary.
            annotations: Optional annotations dictionary.
        """
        if isinstance(name, str):
            name = StringAttr(name)
        if isinstance(file_id, str):
            file_id = StringAttr(file_id)
        module_id = _coerce_graph_id(module_id)
        port_order_attr = _normalize_port_order(port_order)
        merged_attrs = _merge_module_attrs(
            attrs, port_order_attr, pattern_expression_table
        )
        attributes = {
            "module_id": module_id,
            "name": name,
            "file_id": file_id,
        }
        if merged_attrs is not None:
            attributes["attrs"] = merged_attrs
        if annotations is not None:
            attributes["annotations"] = annotations
        if isinstance(region, Region):
            body = region
        else:
            body = Region(Block(region))
        super().__init__(attributes=attributes, regions=[body])

    @property
    def port_order(self) -> list[str] | None:
        """Return the module port order if present.

        Returns:
            List of port names, or None when not specified.
        """
        if self.attrs is None:
            return None
        port_attr = self.attrs.data.get(PORT_ORDER_KEY)
        if not isinstance(port_attr, ArrayAttr):
            return None
        ports: list[str] = []
        for attr in port_attr.data:
            if not isinstance(attr, StringAttr):
                return None
            ports.append(attr.data)
        return ports

    def verify_(self) -> None:
        """Verify module attributes for GraphIR invariants."""
        if self.attrs is not None:
            port_attr = self.attrs.data.get(PORT_ORDER_KEY)
            if port_attr is not None:
                if not isinstance(port_attr, ArrayAttr):
                    raise VerifyException("module attrs.port_order must be an array")
                port_names: list[str] = []
                for attr in port_attr.data:
                    if not isinstance(attr, StringAttr):
                        raise VerifyException(
                            "module attrs.port_order must contain strings"
                        )
                    port_names.append(attr.data)
                if len(port_names) != len(set(port_names)):
                    raise VerifyException("port_order must contain unique names")
            pattern_table = self.attrs.data.get(PATTERN_EXPRESSION_TABLE_KEY)
            if pattern_table is not None and not isinstance(
                pattern_table, DictionaryAttr
            ):
                raise VerifyException(
                    "module attrs.pattern_expression_table must be a dictionary"
                )

        net_names: set[str] = set()
        net_ids: set[str] = set()
        inst_names: set[str] = set()
        inst_ids: set[str] = set()
        for op in self.body.block.ops:
            if isinstance(op, NetOp):
                net_name = op.name_attr.data
                if net_name in net_names:
                    raise VerifyException(f"Duplicate net name '{net_name}'")
                net_names.add(net_name)
                net_ids.add(op.net_id.value.data)
                continue
            if isinstance(op, InstanceOp):
                inst_name = op.name_attr.data
                if inst_name in inst_names:
                    raise VerifyException(f"Duplicate instance name '{inst_name}'")
                inst_names.add(inst_name)
                inst_ids.add(op.inst_id.value.data)
                continue
            if isinstance(op, EndpointOp):
                raise VerifyException("graphir.endpoint must be nested under graphir.net")

        endpoint_keys: set[tuple[str, str]] = set()
        endpoint_ids: set[str] = set()
        for op in self.body.block.ops:
            if not isinstance(op, NetOp):
                continue
            for endpoint in op.body.block.ops:
                if not isinstance(endpoint, EndpointOp):
                    raise VerifyException(
                        "graphir.net region must contain only endpoint ops"
                    )
                inst_id = endpoint.inst_id.value.data
                if inst_id not in inst_ids:
                    raise VerifyException(
                        f"Endpoint inst_id '{inst_id}' is not defined in module"
                    )
                endpoint_ids.add(endpoint.endpoint_id.value.data)
                key = (inst_id, endpoint.port_path.data)
                if key in endpoint_keys:
                    raise VerifyException(
                        "Duplicate endpoint for instance "
                        f"'{inst_id}' and port_path '{endpoint.port_path.data}'"
                    )
                endpoint_keys.add(key)


@irdl_op_definition
class DeviceOp(IRDLOperation):
    """GraphIR device symbol definition.

    Attributes:
        device_id: Stable device identifier.
        name: Device symbol name.
        file_id: Source file identifier.
        ports: Ordered list of port names.
        params: Optional device parameter metadata.
        annotations: Optional annotations.
    """

    name = "graphir.device"

    device_id = attr_def(GraphIdAttr)
    name_attr = attr_def(StringAttr, attr_name="name")
    file_id = attr_def(StringAttr)
    ports = attr_def(ArrayAttr[StringAttr])
    params = opt_attr_def(DictionaryAttr)
    annotations = opt_attr_def(DictionaryAttr)
    body = region_def("single_block")

    traits = traits_def(IsolatedFromAbove(), NoTerminator())
    assembly_format = "$body attr-dict"

    def __init__(
        self,
        *,
        device_id: GraphIdAttr | StringAttr | str | int,
        name: StringAttr | str,
        file_id: StringAttr | str,
        ports: ArrayAttr[StringAttr] | Iterable[str],
        region: Region | Sequence[Operation],
        params: DictionaryAttr | None = None,
        annotations: DictionaryAttr | None = None,
    ) -> None:
        """Initialize a device op.

        Args:
            device_id: Stable device identifier.
            name: Device symbol name.
            file_id: Source file identifier.
            ports: Ordered port list.
            region: Region containing device metadata.
            params: Optional parameter metadata.
            annotations: Optional annotations.
        """
        if isinstance(name, str):
            name = StringAttr(name)
        if isinstance(file_id, str):
            file_id = StringAttr(file_id)
        device_id = _coerce_graph_id(device_id)
        if not isinstance(ports, ArrayAttr):
            ports = ArrayAttr([StringAttr(item) for item in ports])
        attributes = {
            "device_id": device_id,
            "name": name,
            "file_id": file_id,
            "ports": ports,
        }
        if params is not None:
            attributes["params"] = params
        if annotations is not None:
            attributes["annotations"] = annotations
        if isinstance(region, Region):
            body = region
        else:
            body = Region(Block(region))
        super().__init__(attributes=attributes, regions=[body])

    def verify_(self) -> None:
        """Verify device port ordering constraints."""
        port_names = [attr.data for attr in self.ports.data]
        if len(port_names) != len(set(port_names)):
            raise VerifyException("device ports must be unique")


__all__ = ["DeviceOp", "ModuleOp"]
