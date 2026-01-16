"""Lowering helpers for AST to GraphIR conversion."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from xdsl.dialects.builtin import DictionaryAttr

from asdl.ast import DeviceBackendDecl, DeviceDecl, ModuleDecl
from asdl.ast.location import Locatable
from asdl.diagnostics import Diagnostic, format_code
from asdl.imports import NameEnv, ProgramDB
from asdl.ir.converters.ast_to_graphir_context import GraphIrDocumentContext
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
from asdl.ir.graphir import DeviceOp, EndpointOp, InstanceOp, ModuleOp, NetOp
from asdl.ir.patterns import (
    AtomizedEndpoint,
    AtomizedPattern,
    PatternExpressionTable,
    atomize_endpoint,
    atomize_pattern,
    encode_pattern_expression_table,
    register_pattern_expression,
)
from asdl.ir.patterns.origin import PatternOrigin, encode_pattern_origin
from asdl.ir.ifir import BackendOp

INVALID_INSTANCE_EXPR = format_code("IR", 1)
INVALID_ENDPOINT_EXPR = format_code("IR", 2)
PATTERN_LENGTH_MISMATCH = format_code("IR", 3)
PATTERN_COLLISION = format_code("IR", 4)
UNRESOLVED_QUALIFIED = format_code("IR", 10)
UNRESOLVED_UNQUALIFIED = format_code("IR", 11)


_PATTERN_DELIMITERS = set("<>[];")


def _is_pattern_expression(expression: str) -> bool:
    """Check whether a token includes pattern delimiter characters.

    Args:
        expression: Token to inspect.

    Returns:
        True if any pattern delimiter characters are present.
    """
    return any(char in _PATTERN_DELIMITERS for char in expression)


def _register_pattern_entry(
    table: PatternExpressionTable,
    cache: Dict[Tuple[str, str], str],
    *,
    expression: str,
    kind: str,
    loc: Optional[Locatable],
) -> str:
    """Register a pattern expression entry, caching by kind/expression.

    Args:
        table: Pattern expression table to populate.
        cache: Cache of (kind, expression) to expression IDs.
        expression: Pattern expression string.
        kind: Pattern expression kind string.
        loc: Optional source location for span metadata.

    Returns:
        Assigned expression ID for the entry.
    """
    cache_key = (kind, expression)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    span = loc.to_source_span() if loc is not None else None
    expr_id = register_pattern_expression(
        table,
        expression=expression,
        kind=kind,
        span=span,
    )
    cache[cache_key] = expr_id
    return expr_id


def _pattern_origin_from_atom(
    expression_id: str,
    atom: AtomizedPattern | AtomizedEndpoint,
):
    """Build a GraphIR pattern origin attribute from an atomized pattern.

    Args:
        expression_id: Expression table ID for the originating expression.
        atom: Atomized pattern metadata.

    Returns:
        Encoded GraphIR pattern origin attribute.
    """
    return encode_pattern_origin(
        PatternOrigin(
            expression_id=expression_id,
            segment_index=atom.segment_index,
            base_name=atom.base_name,
            pattern_parts=atom.pattern_parts,
        )
    )


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
            resolved = resolve_symbol_reference(
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
            inst_atoms, atom_diags = atomize_pattern(inst_name)
            if inst_atoms is None:
                diagnostics.extend(atom_diags)
                had_error = True
                continue
            inst_is_pattern = _is_pattern_expression(inst_name)
            inst_expr_id = None
            if inst_is_pattern:
                inst_expr_id = _register_pattern_entry(
                    pattern_table,
                    pattern_cache,
                    expression=inst_name,
                    kind="inst",
                    loc=inst_loc or module._loc,
                )

            inst_count = len(inst_atoms)
            param_values_by_inst = [dict() for _ in range(inst_count)]
            param_origins_by_inst: List[Dict[str, object]] = [
                dict() for _ in range(inst_count)
            ]
            param_error = False
            if params:
                for param_name, param_expr in params.items():
                    param_is_pattern = _is_pattern_expression(param_expr)
                    if param_is_pattern:
                        param_atoms, param_diags = atomize_pattern(param_expr)
                        if param_atoms is None:
                            diagnostics.extend(param_diags)
                            param_error = True
                            break
                        param_count = len(param_atoms)
                        param_expr_id = _register_pattern_entry(
                            pattern_table,
                            pattern_cache,
                            expression=param_expr,
                            kind="param",
                            loc=inst_loc or module._loc,
                        )
                    else:
                        param_atoms = [param_expr]
                        param_count = 1
                        param_expr_id = None

                    if param_count not in (1, inst_count):
                        diagnostics.append(
                            diagnostic(
                                PATTERN_LENGTH_MISMATCH,
                                (
                                    f"Instance param '{param_name}' expands to {param_count} "
                                    f"atoms but instance '{inst_name}' expands to {inst_count} "
                                    f"atoms in module '{name}'"
                                ),
                                inst_loc or module._loc,
                            )
                        )
                        param_error = True
                        break

                    for index in range(inst_count):
                        if param_is_pattern:
                            param_atom = (
                                param_atoms[0] if param_count == 1 else param_atoms[index]
                            )
                            param_values_by_inst[index][param_name] = param_atom.literal
                            param_origins_by_inst[index][param_name] = (
                                _pattern_origin_from_atom(param_expr_id, param_atom)
                            )
                        else:
                            param_values_by_inst[index][param_name] = param_expr

            if param_error:
                had_error = True
                continue

            for index, inst_atom in enumerate(inst_atoms):
                inst_literal = inst_atom.literal
                if inst_literal in inst_name_to_id:
                    diagnostics.append(
                        diagnostic(
                            PATTERN_COLLISION,
                            (
                                f"Instance pattern expansion collides on '{inst_literal}' "
                                f"in module '{name}'"
                            ),
                            inst_loc or module._loc,
                        )
                    )
                    had_error = True
                    continue
                inst_id = context.id_allocator.next("i")
                inst_name_to_id[inst_literal] = inst_id
                props = to_string_dict_attr(param_values_by_inst[index])
                param_pattern_origin = None
                if param_origins_by_inst[index]:
                    param_pattern_origin = DictionaryAttr(param_origins_by_inst[index])
                inst_pattern_origin = None
                if inst_expr_id is not None:
                    inst_pattern_origin = _pattern_origin_from_atom(
                        inst_expr_id, inst_atom
                    )
                inst_ops.append(
                    InstanceOp(
                        inst_id=inst_id,
                        name=inst_literal,
                        module_ref=(resolved.kind, resolved.sym_id),
                        module_ref_raw=ref,
                        pattern_origin=inst_pattern_origin,
                        props=props,
                        param_pattern_origin=param_pattern_origin,
                        annotations=maybe_src_annotations(inst_loc),
                    )
                )

    net_ops: List[NetOp] = []
    port_order: List[str] = []
    if module.nets:
        for net_name, endpoint_expr in module.nets.items():
            net_loc = module._nets_loc.get(net_name)
            net_name, is_port = split_net_token(net_name)
            net_atoms, atom_diags = atomize_pattern(
                net_name, allow_splice=not is_port
            )
            if net_atoms is None:
                diagnostics.extend(atom_diags)
                had_error = True
                continue
            net_is_pattern = _is_pattern_expression(net_name)
            net_expr_id = None
            if net_is_pattern:
                net_expr_id = _register_pattern_entry(
                    pattern_table,
                    pattern_cache,
                    expression=net_name,
                    kind="net",
                    loc=net_loc or module._loc,
                )

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

            net_endpoints: List[List[Tuple[AtomizedEndpoint, Optional[str]]]] = [
                [] for _ in range(len(net_atoms))
            ]
            net_error = False
            for inst_name, port_path in endpoints:
                endpoint_expr = f"{inst_name}.{port_path}"
                endpoint_atoms, endpoint_diags = atomize_endpoint(inst_name, port_path)
                if endpoint_atoms is None:
                    diagnostics.extend(endpoint_diags)
                    had_error = True
                    net_error = True
                    continue
                endpoint_count = len(endpoint_atoms)
                endpoint_expr_id = None
                if _is_pattern_expression(endpoint_expr):
                    endpoint_expr_id = _register_pattern_entry(
                        pattern_table,
                        pattern_cache,
                        expression=endpoint_expr,
                        kind="endpoint",
                        loc=net_loc or module._loc,
                    )
                if len(net_atoms) != 1 and endpoint_count != len(net_atoms):
                    diagnostics.append(
                        diagnostic(
                            PATTERN_LENGTH_MISMATCH,
                            (
                                f"Endpoint '{endpoint_expr}' expands to {endpoint_count} "
                                f"atoms but net '{net_name}' expands to {len(net_atoms)} "
                                f"atoms in module '{name}'"
                            ),
                            net_loc or module._loc,
                        )
                    )
                    had_error = True
                    net_error = True
                    continue

                if len(net_atoms) == 1:
                    for endpoint_atom in endpoint_atoms:
                        net_endpoints[0].append((endpoint_atom, endpoint_expr_id))
                else:
                    for index, endpoint_atom in enumerate(endpoint_atoms):
                        net_endpoints[index].append((endpoint_atom, endpoint_expr_id))

            if net_error:
                continue

            for index, net_atom in enumerate(net_atoms):
                net_literal = net_atom.literal
                if net_literal in {net.name_attr.data for net in net_ops}:
                    diagnostics.append(
                        diagnostic(
                            PATTERN_COLLISION,
                            (
                                f"Net pattern expansion collides on '{net_literal}' "
                                f"in module '{name}'"
                            ),
                            net_loc or module._loc,
                        )
                    )
                    had_error = True
                    continue

                endpoint_ops: List[EndpointOp] = []
                for endpoint_atom, endpoint_expr_id in net_endpoints[index]:
                    inst_id = inst_name_to_id.get(endpoint_atom.inst)
                    if inst_id is None:
                        diagnostics.append(
                            diagnostic(
                                INVALID_ENDPOINT_EXPR,
                                (
                                    f"Unknown instance '{endpoint_atom.inst}' referenced by "
                                    f"endpoint '{endpoint_atom.inst}.{endpoint_atom.port}' "
                                    f"in module '{name}'"
                                ),
                                net_loc or module._loc,
                            )
                        )
                        had_error = True
                        continue
                    endpoint_pattern_origin = None
                    if endpoint_expr_id is not None:
                        endpoint_pattern_origin = _pattern_origin_from_atom(
                            endpoint_expr_id, endpoint_atom
                        )
                    endpoint_ops.append(
                        EndpointOp(
                            endpoint_id=context.id_allocator.next("e"),
                            inst_id=inst_id,
                            port_path=endpoint_atom.port,
                            pattern_origin=endpoint_pattern_origin,
                        )
                    )

                net_pattern_origin = None
                if net_expr_id is not None:
                    net_pattern_origin = _pattern_origin_from_atom(
                        net_expr_id, net_atom
                    )
                net_ops.append(
                    NetOp(
                        net_id=context.id_allocator.next("n"),
                        name=net_literal,
                        region=endpoint_ops,
                        pattern_origin=net_pattern_origin,
                    )
                )
                if is_port and net_literal not in port_order:
                    port_order.append(net_literal)

    ops: List[object] = []
    ops.extend(net_ops)
    ops.extend(inst_ops)
    pattern_expr_table_attr = None
    if pattern_table:
        pattern_expr_table_attr = encode_pattern_expression_table(pattern_table)
    return (
        ModuleOp(
            module_id=module_id,
            name=name,
            file_id=context.file_id,
            region=ops,
            port_order=port_order or None,
            pattern_expression_table=pattern_expr_table_attr,
        ),
        diagnostics,
        had_error,
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
        props=to_string_dict_attr(props),
        src=loc_attr(backend._loc),
    )


def resolve_symbol_reference(
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
