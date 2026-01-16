"""Lowering helpers for AST to GraphIR conversion."""

from __future__ import annotations

from typing import Dict, List, Tuple

from asdl.ast import DeviceBackendDecl, DeviceDecl, ModuleDecl
from asdl.diagnostics import Diagnostic
from asdl.ir.converters.ast_to_graphir_context import GraphIrDocumentContext
from asdl.ir.converters.ast_to_graphir_lowering_instances import (
    UNRESOLVED_UNQUALIFIED,
    lower_module_instances,
)
from asdl.ir.converters.ast_to_graphir_lowering_nets import lower_module_nets
from asdl.ir.converters.ast_to_graphir_utils import loc_attr, to_string_dict_attr
from asdl.ir.graphir import DeviceOp, ModuleOp
from asdl.ir.ifir import BackendOp
from asdl.ir.patterns import PatternExpressionTable, encode_pattern_expression_table


def lower_document_ops(
    context: GraphIrDocumentContext,
) -> Tuple[List[ModuleOp], List[DeviceOp], List[Diagnostic], bool]:
    """Lower a document into GraphIR module and device ops.

    Args:
        context: Per-document conversion context.

    Returns:
        Tuple of module ops, device ops, diagnostics, and error flag.
    """
    diagnostics: List[Diagnostic] = []
    had_error = False

    modules: List[ModuleOp] = []
    for name, module in (context.document.modules or {}).items():
        module_op, module_diags, module_error = lower_module(
            name,
            module,
            module_id=context.module_ids[name],
            context=context,
        )
        modules.append(module_op)
        diagnostics.extend(module_diags)
        had_error = had_error or module_error

    devices: List[DeviceOp] = []
    for name, device in (context.document.devices or {}).items():
        devices.append(
            lower_device(
                name,
                device,
                device_id=context.device_ids[name],
                file_id=context.file_id,
            )
        )

    return modules, devices, diagnostics, had_error


def lower_module(
    name: str,
    module: ModuleDecl,
    *,
    module_id: str,
    context: GraphIrDocumentContext,
) -> Tuple[ModuleOp, List[Diagnostic], bool]:
    """Lower a module declaration into GraphIR.

    Args:
        name: Module name.
        module: Module declaration.
        module_id: Stable module identifier.
        context: Per-document conversion context.

    Returns:
        The module op, diagnostics, and error flag.
    """
    diagnostics: List[Diagnostic] = []
    had_error = False
    pattern_table: PatternExpressionTable = {}
    pattern_cache: Dict[Tuple[str, str], str] = {}

    inst_ops, inst_name_to_id, inst_error = lower_module_instances(
        name,
        module,
        context=context,
        pattern_table=pattern_table,
        pattern_cache=pattern_cache,
        diagnostics=diagnostics,
    )
    had_error = had_error or inst_error

    net_ops, port_order, net_error = lower_module_nets(
        name,
        module,
        context=context,
        pattern_table=pattern_table,
        pattern_cache=pattern_cache,
        diagnostics=diagnostics,
        inst_name_to_id=inst_name_to_id,
    )
    had_error = had_error or net_error

    module_op = _assemble_module_op(
        name,
        module_id=module_id,
        file_id=context.file_id,
        net_ops=net_ops,
        inst_ops=inst_ops,
        port_order=port_order,
        pattern_table=pattern_table,
    )
    return module_op, diagnostics, had_error


def _assemble_module_op(
    name: str,
    *,
    module_id: str,
    file_id: str,
    net_ops: List[object],
    inst_ops: List[object],
    port_order: List[str],
    pattern_table: PatternExpressionTable,
) -> ModuleOp:
    """Assemble a GraphIR module op from lowered instance and net ops.

    Args:
        name: Module name.
        module_id: Stable module identifier.
        file_id: Source file identifier.
        net_ops: Lowered net ops.
        inst_ops: Lowered instance ops.
        port_order: Ordered list of port names.
        pattern_table: Pattern expression table to encode.

    Returns:
        Assembled GraphIR module op.
    """
    ops: List[object] = []
    ops.extend(net_ops)
    ops.extend(inst_ops)
    pattern_expr_table_attr = None
    if pattern_table:
        pattern_expr_table_attr = encode_pattern_expression_table(pattern_table)
    return ModuleOp(
        module_id=module_id,
        name=name,
        file_id=file_id,
        region=ops,
        port_order=port_order or None,
        pattern_expression_table=pattern_expr_table_attr,
    )


def lower_device(
    name: str,
    device: DeviceDecl,
    *,
    device_id: str,
    file_id: str,
) -> DeviceOp:
    """Lower a device declaration into GraphIR.

    Args:
        name: Device name.
        device: Device declaration.
        device_id: Stable device identifier.
        file_id: Source file identifier.

    Returns:
        The device op.
    """
    backends: List[BackendOp] = []
    for backend_name, backend in device.backends.items():
        backends.append(lower_backend(backend_name, backend))

    ports = device.ports or []
    return DeviceOp(
        device_id=device_id,
        name=name,
        file_id=file_id,
        ports=ports,
        params=to_string_dict_attr(device.parameters),
        variables=to_string_dict_attr(device.variables),
        region=backends,
    )


def lower_backend(name: str, backend: DeviceBackendDecl) -> BackendOp:
    """Lower a backend declaration into a GraphIR-compatible backend op.

    Args:
        name: Backend identifier.
        backend: Backend declaration payload.

    Returns:
        IFIR backend op embedded under a GraphIR device.
    """
    props = backend.model_extra or None
    return BackendOp(
        name=name,
        template=backend.template,
        params=to_string_dict_attr(backend.parameters),
        variables=to_string_dict_attr(backend.variables),
        props=to_string_dict_attr(props),
        src=loc_attr(backend._loc),
    )


__all__ = [
    "UNRESOLVED_UNQUALIFIED",
    "lower_document_ops",
    "lower_module",
]
