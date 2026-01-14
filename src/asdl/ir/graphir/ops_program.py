"""GraphIR program op definition."""

from __future__ import annotations

from typing import Iterable, Sequence

from xdsl.dialects.builtin import ArrayAttr, StringAttr
from xdsl.ir import Block, Operation, Region
from xdsl.irdl import (
    IRDLOperation,
    irdl_op_definition,
    opt_attr_def,
    region_def,
    traits_def,
)
from xdsl.traits import IsolatedFromAbove, NoTerminator
from xdsl.utils.exceptions import VerifyException

from .attrs import GraphIdAttr, _coerce_graph_id
from .ops_module import DeviceOp, ModuleOp


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
            raise VerifyException(
                "graphir.program region must contain only module/device ops"
            )
        if self.entry is None:
            return
        entry_id = self.entry.value.data
        if entry_id not in module_ids:
            raise VerifyException(f"Entry module_id '{entry_id}' is not defined")


__all__ = ["ProgramOp"]
