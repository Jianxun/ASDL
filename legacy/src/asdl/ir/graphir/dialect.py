"""GraphIR dialect registration for ASDL."""

from __future__ import annotations

from xdsl.ir import Dialect

from .attrs import (
    GraphIdAttr,
    GraphParamRefAttr,
    GraphPatternOriginAttr,
    GraphSymbolRefAttr,
)
from .ops_graph import EndpointOp, InstanceOp, NetOp
from .ops_module import DeviceOp, ModuleOp
from .ops_program import ProgramOp


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
    [GraphIdAttr, GraphParamRefAttr, GraphPatternOriginAttr, GraphSymbolRefAttr],
)


__all__ = [
    "ASDL_GRAPHIR",
    "DeviceOp",
    "EndpointOp",
    "GraphIdAttr",
    "GraphParamRefAttr",
    "GraphPatternOriginAttr",
    "GraphSymbolRefAttr",
    "InstanceOp",
    "ModuleOp",
    "NetOp",
    "ProgramOp",
]
