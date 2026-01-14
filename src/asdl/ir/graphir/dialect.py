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
        if self.attrs is None:
            return
        port_attr = self.attrs.data.get(PORT_ORDER_KEY)
        if port_attr is None:
            return
        if not isinstance(port_attr, ArrayAttr):
            raise VerifyException("module attrs.port_order must be an array")
        port_names: list[str] = []
        for attr in port_attr.data:
            if not isinstance(attr, StringAttr):
                raise VerifyException("module attrs.port_order must contain strings")
            port_names.append(attr.data)
        if len(port_names) != len(set(port_names)):
            raise VerifyException("port_order must contain unique names")


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


ASDL_GRAPHIR = Dialect(
    "graphir",
    [
        ProgramOp,
        ModuleOp,
        DeviceOp,
    ],
    [GraphIdAttr],
)


__all__ = [
    "ASDL_GRAPHIR",
    "DeviceOp",
    "GraphIdAttr",
    "ModuleOp",
    "ProgramOp",
]
