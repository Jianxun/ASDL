"""Net and endpoint lowering helpers for AST to GraphIR conversion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from asdl.ast import ModuleDecl
from asdl.diagnostics import Diagnostic, Severity, format_code
from asdl.ir.converters.ast_to_graphir_axis import (
    _axis_broadcast_mapping,
    _axis_metadata,
    _collect_named_pattern_axes,
)
from asdl.ir.converters.ast_to_graphir_context import GraphIrDocumentContext
from asdl.ir.converters.ast_to_graphir_lowering_instances import (
    INVALID_ENDPOINT_EXPR,
    PATTERN_COLLISION,
    PATTERN_LENGTH_MISMATCH,
    is_pattern_expression,
    pattern_origin_from_atom,
    register_pattern_entry,
)
from asdl.ir.converters.ast_to_graphir_parsing import parse_endpoints, split_net_token
from asdl.ir.converters.ast_to_graphir_utils import diagnostic, maybe_src_annotations
from asdl.ir.graphir import EndpointOp, NetOp
from asdl.ir.patterns import (
    AtomizedEndpoint,
    AtomizedPattern,
    PatternExpressionTable,
    atomize_endpoint,
    atomize_pattern,
)

DEFAULT_OVERRIDE = format_code("LINT", 2)
_MAX_INSTANCE_PREVIEW = 6
_MAX_INSTANCE_MATCH_SCAN = 200


def _preview_names(names: Iterable[str], limit: int) -> Tuple[List[str], bool]:
    preview: List[str] = []
    iterator = iter(names)
    for _ in range(limit):
        try:
            preview.append(next(iterator))
        except StopIteration:
            return preview, False
    has_more = next(iterator, None) is not None
    return preview, has_more


def _case_insensitive_match(
    target: str, candidates: Iterable[str], *, max_scan: int
) -> Optional[str]:
    target_lower = target.lower()
    match: Optional[str] = None
    scanned = 0
    for candidate in candidates:
        scanned += 1
        if scanned > max_scan:
            return None
        if candidate == target:
            continue
        if candidate.lower() == target_lower:
            if match is not None and match != candidate:
                return None
            match = candidate
    return match


def _unknown_instance_notes(
    inst_name: str, inst_name_to_id: Dict[str, str]
) -> Optional[List[str]]:
    notes: List[str] = []
    preview, truncated = _preview_names(inst_name_to_id.keys(), _MAX_INSTANCE_PREVIEW)
    if preview:
        notes.append(f"Known instances: {', '.join(preview)}")
        if truncated:
            notes.append("See the module instances section for the full list.")
    case_match = _case_insensitive_match(
        inst_name,
        inst_name_to_id.keys(),
        max_scan=_MAX_INSTANCE_MATCH_SCAN,
    )
    if case_match:
        notes.append(f"Instance names are case-sensitive; did you mean '{case_match}'?")
    return notes or None


@dataclass(frozen=True)
class _PreparedNetPattern:
    """Prepared net pattern metadata for net lowering.

    Attributes:
        name: Net name without the port prefix.
        is_port: Whether the net token represents a port.
        atoms: Atomized net pattern expansion.
        expr_id: Registered pattern expression ID for the net.
        axis: Tagged-axis metadata for the net expression.
    """

    name: str
    is_port: bool
    atoms: List[AtomizedPattern]
    expr_id: Optional[str]
    axis: object


def _prepare_net_pattern(
    *,
    net_token: str,
    net_loc: Optional[object],
    module: ModuleDecl,
    module_name: str,
    pattern_table: PatternExpressionTable,
    pattern_cache: Dict[Tuple[str, str], str],
    pattern_names_by_expr: Dict[str, List[str]],
    pattern_lengths: Dict[str, int],
    pattern_index_by_name: Dict[str, Dict[object, int]],
    diagnostics: List[Diagnostic],
) -> Tuple[Optional[_PreparedNetPattern], bool]:
    """Prepare net atoms and axis metadata for net lowering.

    Args:
        net_token: Raw net token from the module nets map.
        net_loc: Optional source span for the net token.
        module: Module declaration.
        module_name: Module name for diagnostics.
        pattern_table: Pattern expression table to populate.
        pattern_cache: Cache of pattern expressions to IDs.
        pattern_names_by_expr: Mapping of pattern expressions to names.
        pattern_lengths: Mapping of pattern names to expansion lengths.
        pattern_index_by_name: Mapping of pattern names to index maps.
        diagnostics: Diagnostic collection to append errors to.

    Returns:
        Tuple of (prepared net metadata or None, had_error flag).
    """
    net_name, is_port = split_net_token(net_token)
    net_atoms, atom_diags = atomize_pattern(net_name, allow_splice=not is_port)
    if net_atoms is None:
        diagnostics.extend(atom_diags)
        return None, True
    net_expr_id = None
    if is_pattern_expression(net_name):
        net_expr_id = register_pattern_entry(
            pattern_table,
            pattern_cache,
            expression=net_name,
            kind="net",
            loc=net_loc or module._loc,
        )
    net_axis = _axis_metadata(
        expression=net_name,
        loc=net_loc,
        module=module,
        names_by_expr=pattern_names_by_expr,
        length_by_name=pattern_lengths,
        index_by_name=pattern_index_by_name,
        diagnostics=diagnostics,
        module_name=module_name,
        context="net",
    )
    if net_axis.had_error:
        return None, True
    return (
        _PreparedNetPattern(
            name=net_name,
            is_port=is_port,
            atoms=net_atoms,
            expr_id=net_expr_id,
            axis=net_axis,
        ),
        False,
    )


def _map_explicit_endpoints(
    *,
    endpoint_expr: object,
    endpoint_locs: List[Optional[object]],
    endpoint_axis_locs: Optional[List[Optional[object]]] = None,
    stop_on_error: bool = False,
    net_atoms: List[AtomizedPattern],
    net_axis: object,
    net_name: str,
    net_loc: Optional[object],
    module: ModuleDecl,
    module_name: str,
    pattern_table: PatternExpressionTable,
    pattern_cache: Dict[Tuple[str, str], str],
    pattern_names_by_expr: Dict[str, List[str]],
    pattern_lengths: Dict[str, int],
    pattern_index_by_name: Dict[str, Dict[object, int]],
    diagnostics: List[Diagnostic],
) -> Tuple[
    List[List[Tuple[AtomizedEndpoint, Optional[str], Optional[object], bool]]], bool
]:
    """Map endpoint expressions onto net atoms.

    Args:
        endpoint_expr: Raw endpoint expression sequence.
        endpoint_locs: Optional source spans for each endpoint entry.
        endpoint_axis_locs: Optional source spans for axis metadata lookups.
        stop_on_error: Whether to stop processing endpoints after the first error.
        net_atoms: Atomized net pattern expansion.
        net_axis: Tagged-axis metadata for the net expression.
        net_name: Net expression string.
        net_loc: Optional source span for the net token.
        module: Module declaration.
        module_name: Module name for diagnostics.
        pattern_table: Pattern expression table to populate.
        pattern_cache: Cache of pattern expressions to IDs.
        pattern_names_by_expr: Mapping of pattern expressions to names.
        pattern_lengths: Mapping of pattern names to expansion lengths.
        pattern_index_by_name: Mapping of pattern names to index maps.
        diagnostics: Diagnostic collection to append errors to.

    Returns:
        Tuple of (endpoints-by-atom list, had_error flag).
    """
    net_endpoints_by_atom: List[
        List[Tuple[AtomizedEndpoint, Optional[str], Optional[object], bool]]
    ] = [[] for _ in range(len(net_atoms))]
    endpoints, endpoint_error = parse_endpoints(endpoint_expr)
    if endpoint_error is not None:
        diagnostics.append(
            diagnostic(
                INVALID_ENDPOINT_EXPR,
                f"{endpoint_error} in module '{module_name}'",
                net_loc or module._loc,
            )
        )
        return net_endpoints_by_atom, True

    net_error = False
    for endpoint_index, (inst_name, port_path, suppressed) in enumerate(endpoints):
        endpoint_loc = None
        if endpoint_index < len(endpoint_locs):
            endpoint_loc = endpoint_locs[endpoint_index]
        axis_loc = endpoint_loc
        if endpoint_axis_locs is not None and endpoint_index < len(endpoint_axis_locs):
            axis_loc = endpoint_axis_locs[endpoint_index]
        endpoint_expr_text = f"{inst_name}.{port_path}"
        endpoint_atoms, endpoint_diags = atomize_endpoint(inst_name, port_path)
        if endpoint_atoms is None:
            diagnostics.extend(endpoint_diags)
            net_error = True
            if stop_on_error:
                break
            continue
        endpoint_expr_id = None
        if is_pattern_expression(endpoint_expr_text):
            endpoint_expr_id = register_pattern_entry(
                pattern_table,
                pattern_cache,
                expression=endpoint_expr_text,
                kind="endpoint",
                loc=net_loc or module._loc,
            )
        endpoint_axis = _axis_metadata(
            expression=endpoint_expr_text,
            loc=axis_loc,
            module=module,
            names_by_expr=pattern_names_by_expr,
            length_by_name=pattern_lengths,
            index_by_name=pattern_index_by_name,
            diagnostics=diagnostics,
            module_name=module_name,
            context="endpoint",
        )
        if endpoint_axis.had_error:
            net_error = True
            if stop_on_error:
                break
            continue
        mapping, axis_used, axis_error = _axis_broadcast_mapping(
            net_atoms=net_atoms,
            net_axis=net_axis,
            endpoint_atoms=endpoint_atoms,
            endpoint_axis=endpoint_axis,
            module_name=module_name,
            net_expr=net_name,
            endpoint_expr=endpoint_expr_text,
            net_loc=net_loc or module._loc,
            endpoint_loc=endpoint_loc,
            diagnostics=diagnostics,
        )
        if axis_error:
            net_error = True
            if stop_on_error:
                break
            continue
        if axis_used and mapping is not None:
            for endpoint_atom, net_index in zip(endpoint_atoms, mapping):
                net_endpoints_by_atom[net_index].append(
                    (endpoint_atom, endpoint_expr_id, endpoint_loc, suppressed)
                )
            continue

        if len(net_atoms) != 1 and len(endpoint_atoms) != len(net_atoms):
            diagnostics.append(
                diagnostic(
                    PATTERN_LENGTH_MISMATCH,
                    (
                        f"Endpoint '{endpoint_expr_text}' expands to "
                        f"{len(endpoint_atoms)} atoms but net '{net_name}' "
                        f"expands to {len(net_atoms)} atoms in module '{module_name}'"
                    ),
                    net_loc or module._loc,
                )
            )
            net_error = True
            if stop_on_error:
                break
            continue

        if len(net_atoms) == 1:
            for endpoint_atom in endpoint_atoms:
                net_endpoints_by_atom[0].append(
                    (endpoint_atom, endpoint_expr_id, endpoint_loc, suppressed)
                )
        else:
            for index, endpoint_atom in enumerate(endpoint_atoms):
                net_endpoints_by_atom[index].append(
                    (endpoint_atom, endpoint_expr_id, endpoint_loc, suppressed)
                )

    return net_endpoints_by_atom, net_error


def lower_module_nets(
    name: str,
    module: ModuleDecl,
    *,
    context: GraphIrDocumentContext,
    pattern_table: PatternExpressionTable,
    pattern_cache: Dict[Tuple[str, str], str],
    diagnostics: List[Diagnostic],
    inst_name_to_id: Dict[str, str],
    inst_names_by_ref: Dict[str, List[str]],
) -> Tuple[List[NetOp], List[str], bool]:
    """Lower module nets and endpoints into GraphIR ops.

    Args:
        name: Module name.
        module: Module declaration.
        context: Per-document conversion context.
        pattern_table: Pattern expression table to populate.
        pattern_cache: Cache of pattern expressions to IDs.
        diagnostics: Diagnostic collection to append errors to.
        inst_name_to_id: Mapping of instance literal names to IDs.
        inst_names_by_ref: Mapping of instance references to instance name tokens.

    Returns:
        Net ops, port order list, and error flag.
    """
    net_ops: List[NetOp] = []
    port_order: List[str] = []
    if not module.nets and not module.instance_defaults:
        return net_ops, port_order, False

    had_error = False
    (
        _pattern_exprs,
        pattern_names_by_expr,
        pattern_lengths,
        pattern_index_by_name,
        pattern_axis_error,
    ) = _collect_named_pattern_axes(module, diagnostics=diagnostics)
    if pattern_axis_error:
        had_error = True
    net_endpoints: Dict[str, List[EndpointOp]] = {}
    net_pattern_origins: Dict[str, Optional[object]] = {}
    net_order: List[str] = []
    explicit_endpoints: Dict[Tuple[str, str], Tuple[str, bool, Optional[object]]] = {}

    if module.nets:
        for net_token, endpoint_expr in module.nets.items():
            net_loc = module._nets_loc.get(net_token)
            prepared_net, net_error = _prepare_net_pattern(
                net_token=net_token,
                net_loc=net_loc,
                module=module,
                module_name=name,
                pattern_table=pattern_table,
                pattern_cache=pattern_cache,
                pattern_names_by_expr=pattern_names_by_expr,
                pattern_lengths=pattern_lengths,
                pattern_index_by_name=pattern_index_by_name,
                diagnostics=diagnostics,
            )
            if net_error or prepared_net is None:
                had_error = had_error or net_error
                continue

            endpoint_locs = module._net_endpoint_locs.get(net_token, [])
            net_endpoints_by_atom, net_error = _map_explicit_endpoints(
                endpoint_expr=endpoint_expr,
                endpoint_locs=endpoint_locs,
                net_atoms=prepared_net.atoms,
                net_axis=prepared_net.axis,
                net_name=prepared_net.name,
                net_loc=net_loc,
                module=module,
                module_name=name,
                pattern_table=pattern_table,
                pattern_cache=pattern_cache,
                pattern_names_by_expr=pattern_names_by_expr,
                pattern_lengths=pattern_lengths,
                pattern_index_by_name=pattern_index_by_name,
                diagnostics=diagnostics,
            )
            if net_error:
                had_error = True
                continue

            for index, net_atom in enumerate(prepared_net.atoms):
                net_literal = net_atom.literal
                if net_literal in net_endpoints:
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

                net_pattern_origin = None
                if prepared_net.expr_id is not None:
                    net_pattern_origin = pattern_origin_from_atom(
                        prepared_net.expr_id, net_atom
                    )
                net_endpoints[net_literal] = []
                net_pattern_origins[net_literal] = net_pattern_origin
                net_order.append(net_literal)
                if prepared_net.is_port and net_literal not in port_order:
                    port_order.append(net_literal)

                for endpoint_atom, endpoint_expr_id, endpoint_loc, suppressed in (
                    net_endpoints_by_atom[index]
                ):
                    inst_id = inst_name_to_id.get(endpoint_atom.inst)
                    if inst_id is None:
                        diagnostics.append(
                            diagnostic(
                                INVALID_ENDPOINT_EXPR,
                                (
                                    f"Unknown instance '{endpoint_atom.inst}' "
                                    f"referenced by endpoint "
                                    f"'{endpoint_atom.inst}.{endpoint_atom.port}' "
                                    f"in module '{name}'"
                                ),
                                net_loc or module._loc,
                                notes=_unknown_instance_notes(
                                    endpoint_atom.inst,
                                    inst_name_to_id,
                                ),
                                help=(
                                    f"Declare the instance under modules.{name}.instances "
                                    "before wiring it in nets."
                                ),
                            )
                        )
                        had_error = True
                        continue
                    endpoint_pattern_origin = None
                    if endpoint_expr_id is not None:
                        endpoint_pattern_origin = pattern_origin_from_atom(
                            endpoint_expr_id, endpoint_atom
                        )
                    net_endpoints[net_literal].append(
                        EndpointOp(
                            endpoint_id=context.id_allocator.next("e"),
                            inst_id=inst_id,
                            port_path=endpoint_atom.port,
                            pattern_origin=endpoint_pattern_origin,
                            annotations=maybe_src_annotations(endpoint_loc),
                        )
                    )
                    key = (endpoint_atom.inst, endpoint_atom.port)
                    explicit = explicit_endpoints.get(key)
                    if explicit is None:
                        explicit_endpoints[key] = (
                            net_literal,
                            suppressed,
                            endpoint_loc,
                        )
                    else:
                        existing_net, existing_suppressed, existing_loc = explicit
                        if existing_suppressed and not suppressed:
                            explicit_endpoints[key] = (
                                existing_net,
                                False,
                                existing_loc,
                            )

    if module.instance_defaults and inst_names_by_ref:
        for ref, defaults in module.instance_defaults.items():
            inst_names = inst_names_by_ref.get(ref)
            if not inst_names:
                continue
            for port_name, net_token in defaults.bindings.items():
                binding_loc = defaults._bindings_loc.get(port_name)
                prepared_net, net_error = _prepare_net_pattern(
                    net_token=net_token,
                    net_loc=binding_loc,
                    module=module,
                    module_name=name,
                    pattern_table=pattern_table,
                    pattern_cache=pattern_cache,
                    pattern_names_by_expr=pattern_names_by_expr,
                    pattern_lengths=pattern_lengths,
                    pattern_index_by_name=pattern_index_by_name,
                    diagnostics=diagnostics,
                )
                if net_error or prepared_net is None:
                    had_error = had_error or net_error
                    continue

                endpoint_exprs = [
                    f"{inst_name}.{port_name}" for inst_name in inst_names
                ]
                endpoint_locs: List[Optional[object]] = []
                endpoint_axis_locs: List[Optional[object]] = []
                for inst_name in inst_names:
                    inst_loc = module._instances_loc.get(inst_name)
                    endpoint_locs.append(inst_loc or binding_loc)
                    # Endpoint expressions from defaults are synthetic; avoid partial source spans.
                    endpoint_axis_locs.append(None)

                net_endpoints_by_atom, net_error = _map_explicit_endpoints(
                    endpoint_expr=endpoint_exprs,
                    endpoint_locs=endpoint_locs,
                    endpoint_axis_locs=endpoint_axis_locs,
                    stop_on_error=True,
                    net_atoms=prepared_net.atoms,
                    net_axis=prepared_net.axis,
                    net_name=prepared_net.name,
                    net_loc=binding_loc,
                    module=module,
                    module_name=name,
                    pattern_table=pattern_table,
                    pattern_cache=pattern_cache,
                    pattern_names_by_expr=pattern_names_by_expr,
                    pattern_lengths=pattern_lengths,
                    pattern_index_by_name=pattern_index_by_name,
                    diagnostics=diagnostics,
                )
                if net_error:
                    had_error = True
                    continue

                for index, net_atom in enumerate(prepared_net.atoms):
                    net_literal = net_atom.literal
                    new_endpoints: List[EndpointOp] = []
                    for (
                        endpoint_atom,
                        endpoint_expr_id,
                        _endpoint_loc,
                        _suppressed,
                    ) in net_endpoints_by_atom[index]:
                        key = (endpoint_atom.inst, endpoint_atom.port)
                        explicit = explicit_endpoints.get(key)
                        if explicit is not None:
                            explicit_net, suppressed, explicit_loc = explicit
                            if explicit_net != net_literal and not suppressed:
                                diagnostics.append(
                                    diagnostic(
                                        DEFAULT_OVERRIDE,
                                        (
                                            "Default binding for "
                                            f"'{endpoint_atom.inst}."
                                            f"{endpoint_atom.port}' to "
                                            f"'{net_literal}' overridden by "
                                            f"explicit net '{explicit_net}'."
                                        ),
                                        explicit_loc or binding_loc or module._loc,
                                        severity=Severity.WARNING,
                                    )
                                )
                            continue

                        inst_id = inst_name_to_id.get(endpoint_atom.inst)
                        if inst_id is None:
                            diagnostics.append(
                                diagnostic(
                                    INVALID_ENDPOINT_EXPR,
                                    (
                                        f"Unknown instance '{endpoint_atom.inst}' "
                                        f"referenced by endpoint "
                                        f"'{endpoint_atom.inst}.{endpoint_atom.port}' "
                                        f"in module '{name}'"
                                    ),
                                    binding_loc or module._loc,
                                    notes=_unknown_instance_notes(
                                        endpoint_atom.inst,
                                        inst_name_to_id,
                                    ),
                                    help=(
                                        f"Declare the instance under modules.{name}.instances "
                                        "before wiring it in nets."
                                    ),
                                )
                            )
                            had_error = True
                            continue
                        endpoint_pattern_origin = None
                        if endpoint_expr_id is not None:
                            endpoint_pattern_origin = pattern_origin_from_atom(
                                endpoint_expr_id, endpoint_atom
                            )
                        new_endpoints.append(
                            EndpointOp(
                                endpoint_id=context.id_allocator.next("e"),
                                inst_id=inst_id,
                                port_path=endpoint_atom.port,
                                pattern_origin=endpoint_pattern_origin,
                                annotations=maybe_src_annotations(binding_loc),
                            )
                        )

                    if not new_endpoints:
                        continue

                    if net_literal not in net_endpoints:
                        net_endpoints[net_literal] = []
                        net_pattern_origin = None
                        if prepared_net.expr_id is not None:
                            net_pattern_origin = pattern_origin_from_atom(
                                prepared_net.expr_id, net_atom
                            )
                        net_pattern_origins[net_literal] = net_pattern_origin
                        net_order.append(net_literal)

                    net_endpoints[net_literal].extend(new_endpoints)
                    if prepared_net.is_port and net_literal not in port_order:
                        port_order.append(net_literal)

    for net_name in net_order:
        net_ops.append(
            NetOp(
                net_id=context.id_allocator.next("n"),
                name=net_name,
                region=net_endpoints.get(net_name, []),
                pattern_origin=net_pattern_origins.get(net_name),
            )
        )

    return net_ops, port_order, had_error


__all__ = ["lower_module_nets"]
