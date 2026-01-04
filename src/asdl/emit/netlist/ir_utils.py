from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from xdsl.dialects import builtin
from xdsl.ir import Operation

from asdl.diagnostics import Severity
from asdl.diagnostics.collector import DiagnosticCollector
from asdl.ir.ifir import BackendOp, DesignOp, DeviceOp, ModuleOp

from .diagnostics import MISSING_TOP, _diagnostic


def _collect_design_ops(
    design: DesignOp,
) -> Tuple[Dict[str, ModuleOp], Dict[str, DeviceOp], List[ModuleOp]]:
    modules: Dict[str, ModuleOp] = {}
    devices: Dict[str, DeviceOp] = {}
    module_ops: List[ModuleOp] = []

    for op in design.body.block.ops:
        if isinstance(op, ModuleOp):
            name = op.sym_name.data
            modules[name] = op
            module_ops.append(op)
            continue
        if isinstance(op, DeviceOp):
            devices[op.sym_name.data] = op

    return modules, devices, module_ops


def _resolve_top_name(
    design: DesignOp,
    module_ops: List[ModuleOp],
    diagnostics: DiagnosticCollector,
) -> Optional[str]:
    top_name = design.top.data if design.top is not None else None
    if top_name is None:
        if len(module_ops) == 1:
            return module_ops[0].sym_name.data
        diagnostics.emit(
            _diagnostic(
                MISSING_TOP,
                "Top module is required when multiple modules exist",
                Severity.ERROR,
            )
        )
        return None
    module_names = {op.sym_name.data for op in module_ops}
    if top_name in module_names:
        return top_name
    diagnostics.emit(
        _diagnostic(
            MISSING_TOP,
            f"Top module '{top_name}' is not defined",
            Severity.ERROR,
        )
    )
    return None


def _find_single_design(
    module: builtin.ModuleOp,
    design_type: type[Operation],
    code: str,
    *,
    diagnostics: DiagnosticCollector,
) -> Optional[DesignOp]:
    found = [op for op in module.body.block.ops if isinstance(op, design_type)]
    if len(found) == 1:
        return found[0]
    diagnostics.emit(
        _diagnostic(
            code,
            f"Expected single design op in module, found {len(found)}",
            Severity.ERROR,
        )
    )
    return None


def _select_backend(device: DeviceOp, backend_name: str) -> Optional[BackendOp]:
    for op in device.body.block.ops:
        if isinstance(op, BackendOp) and op.name_attr.data == backend_name:
            return op
    return None
