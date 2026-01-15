"""AST to GraphIR conversion for ASDL documents and import graphs."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from asdl.ast import AsdlDocument, DeviceBackendDecl, DeviceDecl, ModuleDecl
from asdl.ast.location import Locatable
from asdl.diagnostics import Diagnostic, format_code
from asdl.imports import ImportGraph, NameEnv, ProgramDB
from asdl.ir.converters.ast_to_graphir_context import (
    GraphIrDocumentContext,
    GraphIrSessionContext,
)
from asdl.ir.converters.ast_to_graphir_parsing import (
    parse_endpoints,
    parse_instance_expr,
    split_net_token,
)
from asdl.ir.converters.ast_to_graphir_symbols import ResolvedSymbol
from asdl.ir.converters.ast_to_graphir_utils import (
    diagnostic,
    loc_attr,
    maybe_src_annotations,
    to_string_dict_attr,
)
from asdl.ir.graphir import DeviceOp, EndpointOp, InstanceOp, ModuleOp, NetOp, ProgramOp
from asdl.ir.ifir import BackendOp

INVALID_INSTANCE_EXPR = format_code("IR", 1)
INVALID_ENDPOINT_EXPR = format_code("IR", 2)
UNRESOLVED_QUALIFIED = format_code("IR", 10)
UNRESOLVED_UNQUALIFIED = format_code("IR", 11)


def convert_document(
    document: AsdlDocument,
    *,
    name_env: Optional[NameEnv] = None,
    program_db: Optional[ProgramDB] = None,
) -> Tuple[Optional[ProgramOp], List[Diagnostic]]:
    """Convert a single ASDL document into GraphIR.

    Args:
        document: Parsed AST document.
        name_env: Optional name environment for file identity.
        program_db: Optional program database for symbol resolution.

    Returns:
        The GraphIR program op (or None on error) and diagnostics.
    """
    diagnostics: List[Diagnostic] = []
    had_error = False

    session = GraphIrSessionContext.for_document(program_db=program_db)
    doc_context = session.document_context(document, name_env=name_env)

    modules, devices, doc_diags, doc_error = _convert_document_ops(doc_context)
    diagnostics.extend(doc_diags)
    had_error = had_error or doc_error

    entry_id: Optional[str] = None
    if document.top is not None:
        entry_id = doc_context.module_ids.get(document.top)
        if entry_id is None:
            diagnostics.append(
                diagnostic(
                    UNRESOLVED_UNQUALIFIED,
                    f"Unresolved top module '{document.top}'.",
                    getattr(document, "_loc", None),
                )
            )
            had_error = True

    program = ProgramOp(region=modules + devices, entry=entry_id)
    if had_error:
        return None, diagnostics
    return program, diagnostics


def convert_import_graph(
    graph: ImportGraph,
) -> Tuple[Optional[ProgramOp], List[Diagnostic]]:
    """Convert an import graph into a unified GraphIR program.

    Args:
        graph: Resolved import graph with documents, name envs, and ProgramDB.

    Returns:
        The GraphIR program op (or None on error) and diagnostics.
    """
    diagnostics: List[Diagnostic] = []
    had_error = False
    session = GraphIrSessionContext.for_import_graph(graph)
    file_order = session.file_order

    ops: List[object] = []
    for file_id in file_order:
        document = graph.documents.get(file_id)
        if document is None:
            diagnostics.append(
                diagnostic(
                    UNRESOLVED_UNQUALIFIED,
                    f"Import graph missing document '{file_id}'.",
                    None,
                )
            )
            had_error = True
            continue
        doc_context = session.document_context(
            document,
            name_env=graph.name_envs.get(file_id),
            file_path=file_id,
        )
        modules, devices, doc_diags, doc_error = _convert_document_ops(doc_context)
        ops.extend(modules)
        ops.extend(devices)
        diagnostics.extend(doc_diags)
        had_error = had_error or doc_error

    entry_id: Optional[str] = None
    entry_document = graph.documents.get(graph.entry_file)
    if entry_document is None:
        diagnostics.append(
            diagnostic(
                UNRESOLVED_UNQUALIFIED,
                f"Import graph missing entry document '{graph.entry_file}'.",
                None,
            )
        )
        had_error = True
    elif entry_document.top is not None:
        entry_id = session.module_ids_by_file.get(graph.entry_file, {}).get(
            entry_document.top
        )
        if entry_id is None:
            diagnostics.append(
                diagnostic(
                    UNRESOLVED_UNQUALIFIED,
                    f"Unresolved top module '{entry_document.top}'.",
                    getattr(entry_document, "_loc", None),
                )
            )
            had_error = True

    program = ProgramOp(
        region=ops,
        entry=entry_id,
        file_order=[str(file_id) for file_id in file_order],
    )
    if had_error:
        return None, diagnostics
    return program, diagnostics


def _convert_document_ops(
    context: GraphIrDocumentContext,
) -> Tuple[List[ModuleOp], List[DeviceOp], List[Diagnostic], bool]:
    """Convert a document into GraphIR module/device ops.

    Args:
        context: Per-document conversion context.

    Returns:
        Tuple of module ops, device ops, diagnostics, and error flag.
    """
    diagnostics: List[Diagnostic] = []
    had_error = False

    modules: List[ModuleOp] = []
    for name, module in (context.document.modules or {}).items():
        module_op, module_diags, module_error = _convert_module(
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
            _convert_device(
                name,
                device,
                device_id=context.device_ids[name],
                file_id=context.file_id,
            )
        )

    return modules, devices, diagnostics, had_error


def _convert_module(
    name: str,
    module: ModuleDecl,
    *,
    module_id: str,
    context: GraphIrDocumentContext,
) -> Tuple[ModuleOp, List[Diagnostic], bool]:
    """Convert a module declaration into GraphIR.

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

    inst_ops: List[InstanceOp] = []
    inst_name_to_id: Dict[str, str] = {}
    if module.instances:
        for inst_name, expr in module.instances.items():
            inst_loc = module._instances_loc.get(inst_name)
            ref, params, parse_error = parse_instance_expr(expr)
            if parse_error is not None:
                diagnostics.append(
                    diagnostic(
                        INVALID_INSTANCE_EXPR,
                        f"{parse_error} in module '{name}'",
                        inst_loc or module._loc,
                    )
                )
                had_error = True
                continue
            if ref is None:
                diagnostics.append(
                    diagnostic(
                        INVALID_INSTANCE_EXPR,
                        f"Instance expression missing reference in module '{name}'",
                        inst_loc or module._loc,
                    )
                )
                had_error = True
                continue
            resolved = _resolve_symbol_reference(
                ref,
                context.symbol_table,
                diagnostics,
                inst_loc or module._loc,
                name_env=context.name_env,
                program_db=context.program_db,
                global_symbols=context.global_symbols,
            )
            if resolved is None:
                had_error = True
                continue
            inst_id = context.id_allocator.next("i")
            inst_name_to_id[inst_name] = inst_id
            inst_ops.append(
                InstanceOp(
                    inst_id=inst_id,
                    name=inst_name,
                    module_ref=(resolved.kind, resolved.sym_id),
                    module_ref_raw=ref,
                    props=to_string_dict_attr(params),
                    annotations=maybe_src_annotations(inst_loc),
                )
            )

    net_ops: List[NetOp] = []
    port_order: List[str] = []
    if module.nets:
        for net_name, endpoint_expr in module.nets.items():
            net_loc = module._nets_loc.get(net_name)
            net_name, is_port = split_net_token(net_name)
            if is_port and net_name not in port_order:
                port_order.append(net_name)

            endpoints, _suppressed, endpoint_error = parse_endpoints(endpoint_expr)
            if endpoint_error is not None:
                diagnostics.append(
                    diagnostic(
                        INVALID_ENDPOINT_EXPR,
                        f"{endpoint_error} in module '{name}'",
                        net_loc or module._loc,
                    )
                )
                had_error = True
                continue

            endpoint_ops: List[EndpointOp] = []
            for inst_name, port_path in endpoints:
                inst_id = inst_name_to_id.get(inst_name)
                if inst_id is None:
                    diagnostics.append(
                        diagnostic(
                            INVALID_ENDPOINT_EXPR,
                            (
                                f"Unknown instance '{inst_name}' referenced by endpoint "
                                f"'{inst_name}.{port_path}' in module '{name}'"
                            ),
                            net_loc or module._loc,
                        )
                    )
                    had_error = True
                    continue
                endpoint_ops.append(
                    EndpointOp(
                        endpoint_id=context.id_allocator.next("e"),
                        inst_id=inst_id,
                        port_path=port_path,
                    )
                )

            net_ops.append(
                NetOp(
                    net_id=context.id_allocator.next("n"),
                    name=net_name,
                    region=endpoint_ops,
                )
            )

    ops: List[object] = []
    ops.extend(net_ops)
    ops.extend(inst_ops)
    return (
        ModuleOp(
            module_id=module_id,
            name=name,
            file_id=context.file_id,
            region=ops,
            port_order=port_order or None,
        ),
        diagnostics,
        had_error,
    )


def _convert_device(
    name: str,
    device: DeviceDecl,
    *,
    device_id: str,
    file_id: str,
) -> DeviceOp:
    """Convert a device declaration into GraphIR.

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
        backends.append(_convert_backend(backend_name, backend))

    ports = device.ports or []
    return DeviceOp(
        device_id=device_id,
        name=name,
        file_id=file_id,
        ports=ports,
        params=to_string_dict_attr(device.params),
        region=backends,
    )


def _convert_backend(name: str, backend: DeviceBackendDecl) -> BackendOp:
    """Convert a backend declaration into a GraphIR-compatible backend op.

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
        params=to_string_dict_attr(backend.params),
        props=to_string_dict_attr(props),
        src=loc_attr(backend._loc),
    )


def _resolve_symbol_reference(
    ref: str,
    symbol_table: Dict[str, List[ResolvedSymbol]],
    diagnostics: List[Diagnostic],
    loc: Optional[Locatable],
    *,
    name_env: Optional[NameEnv] = None,
    program_db: Optional[ProgramDB] = None,
    global_symbols: Optional[Dict[Path, Dict[str, List[ResolvedSymbol]]]] = None,
) -> Optional[ResolvedSymbol]:
    """Resolve an instance reference to a symbol.

    Args:
        ref: Instance reference token.
        symbol_table: Mapping of local symbols.
        diagnostics: Diagnostic collection to append errors to.
        loc: Optional source location.
        name_env: Optional name environment for import resolution.
        program_db: Optional program database for qualified symbol resolution.
        global_symbols: Optional symbol tables keyed by file ID.

    Returns:
        Resolved symbol metadata or None if unresolved.
    """
    if "." in ref:
        if name_env is None or program_db is None or global_symbols is None:
            diagnostics.append(
                diagnostic(
                    UNRESOLVED_QUALIFIED,
                    f"Unresolved symbol '{ref}'.",
                    loc,
                )
            )
            return None
        namespace, symbol = ref.split(".", 1)
        if not namespace or not symbol:
            diagnostics.append(
                diagnostic(
                    UNRESOLVED_QUALIFIED,
                    f"Unresolved symbol '{ref}'.",
                    loc,
                )
            )
            return None
        resolved_file_id = name_env.resolve(namespace)
        if resolved_file_id is None:
            diagnostics.append(
                diagnostic(
                    UNRESOLVED_QUALIFIED,
                    f"Unresolved symbol '{ref}'.",
                    loc,
                )
            )
            return None
        if program_db.lookup(resolved_file_id, symbol) is None:
            diagnostics.append(
                diagnostic(
                    UNRESOLVED_QUALIFIED,
                    f"Unresolved symbol '{ref}'.",
                    loc,
                )
            )
            return None
        candidates = global_symbols.get(resolved_file_id, {}).get(symbol)
        if not candidates:
            diagnostics.append(
                diagnostic(
                    UNRESOLVED_QUALIFIED,
                    f"Unresolved symbol '{ref}'.",
                    loc,
                )
            )
            return None
        if len(candidates) > 1:
            diagnostics.append(
                diagnostic(
                    UNRESOLVED_QUALIFIED,
                    f"Ambiguous symbol '{ref}' refers to multiple definitions.",
                    loc,
                )
            )
            return None
        return candidates[0]
    candidates = symbol_table.get(ref)
    if not candidates:
        diagnostics.append(
            diagnostic(
                UNRESOLVED_UNQUALIFIED,
                f"Unresolved symbol '{ref}'.",
                loc,
            )
        )
        return None
    if len(candidates) > 1:
        diagnostics.append(
            diagnostic(
                UNRESOLVED_UNQUALIFIED,
                f"Ambiguous symbol '{ref}' refers to multiple definitions.",
                loc,
            )
        )
        return None
    return candidates[0]


__all__ = ["convert_document", "convert_import_graph"]
