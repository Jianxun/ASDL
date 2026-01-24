from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, TypeVar

from xdsl.dialects import builtin
from xdsl.ir import Operation

from asdl.diagnostics import Severity
from asdl.diagnostics.collector import DiagnosticCollector
from asdl.emit.netlist_ir import NetlistDesign, NetlistDevice, NetlistModule
from asdl.ir.ifir import BackendOp, DesignOp, DeviceOp, ModuleOp

from .diagnostics import MISSING_TOP, _diagnostic


def _collect_design_ops(
    design: DesignOp,
) -> Tuple[Dict[str, List[ModuleOp]], Dict[str, List[DeviceOp]], List[ModuleOp]]:
    modules: Dict[str, List[ModuleOp]] = {}
    devices: Dict[str, List[DeviceOp]] = {}
    module_ops: List[ModuleOp] = []

    for op in design.body.block.ops:
        if isinstance(op, ModuleOp):
            name = op.sym_name.data
            modules.setdefault(name, []).append(op)
            module_ops.append(op)
            continue
        if isinstance(op, DeviceOp):
            devices.setdefault(op.sym_name.data, []).append(op)

    return modules, devices, module_ops


@dataclass(frozen=True)
class NetlistIRIndex:
    """Lookup tables for NetlistIR symbols.

    Attributes:
        modules_by_name: Module list keyed by symbol name.
        devices_by_name: Device list keyed by symbol name.
        modules_by_key: Module map keyed by (file_id, name).
        devices_by_key: Device map keyed by (file_id, name).
        top_name: Resolved top module name.
    """

    modules_by_name: Dict[str, List[NetlistModule]]
    devices_by_name: Dict[str, List[NetlistDevice]]
    modules_by_key: Dict[Tuple[Optional[str], str], NetlistModule]
    devices_by_key: Dict[Tuple[Optional[str], str], NetlistDevice]
    top_name: str


def _build_netlist_ir_index(
    design: NetlistDesign,
    diagnostics: DiagnosticCollector,
) -> Optional[NetlistIRIndex]:
    """Build NetlistIR lookup tables and resolve the top module name.

    Args:
        design: NetlistIR design to index.
        diagnostics: Collector for top resolution diagnostics.

    Returns:
        NetlistIRIndex if a top name can be resolved, otherwise None.
    """
    modules_by_name: Dict[str, List[NetlistModule]] = {}
    devices_by_name: Dict[str, List[NetlistDevice]] = {}

    for module in design.modules:
        modules_by_name.setdefault(module.name, []).append(module)
    for device in design.devices:
        devices_by_name.setdefault(device.name, []).append(device)

    modules_by_key = {
        (module.file_id, module.name): module for module in design.modules
    }
    devices_by_key = {
        (device.file_id, device.name): device for device in design.devices
    }

    top_name = _resolve_netlist_ir_top_name(design, design.modules, diagnostics)
    if top_name is None:
        return None

    return NetlistIRIndex(
        modules_by_name=modules_by_name,
        devices_by_name=devices_by_name,
        modules_by_key=modules_by_key,
        devices_by_key=devices_by_key,
        top_name=top_name,
    )


def _resolve_netlist_ir_top_name(
    design: NetlistDesign,
    modules: List[NetlistModule],
    diagnostics: DiagnosticCollector,
) -> Optional[str]:
    """Resolve the top module name for a NetlistIR design.

    Args:
        design: NetlistIR design to inspect.
        modules: Modules defined in the design.
        diagnostics: Collector for missing-top diagnostics.

    Returns:
        Resolved top module name, or None when invalid.
    """
    top_name = design.top
    if top_name is None:
        if len(modules) == 1:
            return modules[0].name
        diagnostics.emit(
            _diagnostic(
                MISSING_TOP,
                "Top module is required when multiple modules exist",
                Severity.ERROR,
            )
        )
        return None
    module_names = {module.name for module in modules}
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


T = TypeVar("T")


def _select_symbol(
    symbols_by_name: Dict[str, List[T]],
    symbol_index: Dict[Tuple[str, Optional[str]], T],
    name: str,
    file_id: Optional[str],
) -> Optional[T]:
    if file_id is not None:
        return symbol_index.get((name, file_id))
    candidates = symbols_by_name.get(name, [])
    if len(candidates) == 1:
        return candidates[0]
    if candidates:
        return candidates[-1]
    return None


def _select_netlist_ir_symbol(
    symbols_by_name: Dict[str, List[T]],
    symbol_index: Dict[Tuple[Optional[str], str], T],
    name: str,
    file_id: Optional[str],
) -> Optional[T]:
    """Select a NetlistIR symbol by name and file id.

    Args:
        symbols_by_name: Symbol lists keyed by name.
        symbol_index: Symbol map keyed by (file_id, name).
        name: Symbol name to select.
        file_id: Optional file id to disambiguate.

    Returns:
        Selected symbol or None if not found.
    """
    if file_id is not None:
        return symbol_index.get((file_id, name))
    candidates = symbols_by_name.get(name, [])
    if len(candidates) == 1:
        return candidates[0]
    if candidates:
        return candidates[-1]
    return None


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
