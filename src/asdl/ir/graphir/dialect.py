"""GraphIR dialect definitions for ASDL.

This module defines the initial GraphIR ops and attributes needed to model
programs, modules, and devices with stable identifiers.
"""

from __future__ import annotations

from typing import Iterable, Sequence

from xdsl.dialects.builtin import ArrayAttr, DictionaryAttr, StringAttr
from xdsl.ir import Block, Dialect, Operation, ParametrizedAttribute, Region
from xdsl.irdl import (
    IRDLOperation,
    attr_def,
    irdl_attr_definition,
    irdl_op_definition,
    opt_attr_def,
    param_def,
    region_def,
    traits_def,
)
from xdsl.traits import IsolatedFromAbove, NoTerminator
from xdsl.utils.exceptions import VerifyException

PORT_ORDER_KEY = "port_order"


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
) -> DictionaryAttr | None:
    """Merge module attrs with the reserved port_order entry.

    Args:
        attrs: Existing attrs dictionary.
        port_order: Normalized port order to inject.

    Returns:
        A DictionaryAttr containing merged data, or None if empty.
    """
    if attrs is None and port_order is None:
        return None
    merged = dict(attrs.data) if attrs is not None else {}
    if port_order is not None:
        merged[PORT_ORDER_KEY] = port_order
    return DictionaryAttr(merged)


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


def _coerce_graph_symbol_ref(
    value: GraphSymbolRefAttr | tuple[str | StringAttr, GraphIdAttr | StringAttr | str | int],
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


@irdl_op_definition
class ModuleOp(IRDLOperation):
    """GraphIR module graph container.

    Attributes:
        module_id: Stable module identifier.
        name: Module symbol name.
        file_id: Source file identifier.
        attrs: Optional module attributes (includes port_order).
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
            attrs: Optional attribute dictionary.
            annotations: Optional annotations dictionary.
        """
        if isinstance(name, str):
            name = StringAttr(name)
        if isinstance(file_id, str):
            file_id = StringAttr(file_id)
        module_id = _coerce_graph_id(module_id)
        port_order_attr = _normalize_port_order(port_order)
        merged_attrs = _merge_module_attrs(attrs, port_order_attr)
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

        net_names: set[str] = set()
        inst_names: set[str] = set()
        inst_ids: set[str] = set()
        for op in self.body.block.ops:
            if isinstance(op, NetOp):
                net_name = op.name_attr.data
                if net_name in net_names:
                    raise VerifyException(f"Duplicate net name '{net_name}'")
                net_names.add(net_name)
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


@irdl_op_definition
class ProgramOp(IRDLOperation):
    """GraphIR program container.

    Attributes:
        entry: Optional entry module ID.
        file_order: Optional file ordering list.
        body: Region containing module and device ops.
    """

    name = "graphir.program"

    entry = opt_attr_def(GraphIdAttr)
    file_order = opt_attr_def(ArrayAttr[StringAttr])
    body = region_def("single_block")

    traits = traits_def(IsolatedFromAbove(), NoTerminator())
    assembly_format = "$body attr-dict"

    def __init__(
        self,
        *,
        region: Region | Sequence[Operation],
        entry: GraphIdAttr | StringAttr | str | int | None = None,
        file_order: ArrayAttr[StringAttr] | Iterable[str] | None = None,
    ) -> None:
        """Initialize a program op.

        Args:
            region: Region containing module/device ops.
            entry: Optional entry module ID.
            file_order: Optional file ordering list.
        """
        attributes: dict[str, object] = {}
        if entry is not None:
            attributes["entry"] = _coerce_graph_id(entry)
        if file_order is not None:
            if not isinstance(file_order, ArrayAttr):
                file_order = ArrayAttr([StringAttr(item) for item in file_order])
            attributes["file_order"] = file_order
        if isinstance(region, Region):
            body = region
        else:
            body = Region(Block(region))
        super().__init__(attributes=attributes, regions=[body])

    def verify_(self) -> None:
        """Verify program structure and ID references."""
        module_ids: set[str] = set()
        device_ids: set[str] = set()
        for op in self.body.block.ops:
            if isinstance(op, ModuleOp):
                module_id = op.module_id.value.data
                if module_id in module_ids:
                    raise VerifyException(f"Duplicate module_id '{module_id}'")
                module_ids.add(module_id)
                continue
            if isinstance(op, DeviceOp):
                device_id = op.device_id.value.data
                if device_id in device_ids:
                    raise VerifyException(f"Duplicate device_id '{device_id}'")
                device_ids.add(device_id)
                continue
            raise VerifyException("graphir.program region must contain only module/device ops")
        if self.entry is None:
            return
        entry_id = self.entry.value.data
        if entry_id not in module_ids:
            raise VerifyException(f"Entry module_id '{entry_id}' is not defined")


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
        module_ref: GraphSymbolRefAttr | tuple[str | StringAttr, GraphIdAttr | StringAttr | str | int],
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


ASDL_GRAPHIR = Dialect(
    "graphir",
    [
        ProgramOp,
        ModuleOp,
        DeviceOp,
        NetOp,
        InstanceOp,
        EndpointOp,
    ],
    [GraphIdAttr, GraphSymbolRefAttr],
)


__all__ = [
    "ASDL_GRAPHIR",
    "DeviceOp",
    "EndpointOp",
    "GraphIdAttr",
    "GraphSymbolRefAttr",
    "InstanceOp",
    "ModuleOp",
    "NetOp",
    "ProgramOp",
]
