"""Net and endpoint lowering helpers for AST to GraphIR conversion."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from asdl.ast import ModuleDecl
from asdl.diagnostics import Diagnostic, Severity, format_code
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
from asdl.ir.converters.ast_to_graphir_utils import diagnostic
from asdl.ir.graphir import EndpointOp, NetOp
from asdl.ir.patterns import (
    AtomizedEndpoint,
    PatternExpressionTable,
    atomize_endpoint,
    atomize_pattern,
)

DEFAULT_OVERRIDE = format_code("LINT", 2)


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
    net_endpoints: Dict[str, List[EndpointOp]] = {}
    net_pattern_origins: Dict[str, Optional[object]] = {}
    net_order: List[str] = []
    explicit_endpoints: Dict[Tuple[str, str], Tuple[str, bool, Optional[object]]] = {}

    if module.nets:
        for net_token, endpoint_expr in module.nets.items():
            net_loc = module._nets_loc.get(net_token)
            net_name, is_port = split_net_token(net_token)
            net_atoms, atom_diags = atomize_pattern(net_name, allow_splice=not is_port)
            if net_atoms is None:
                diagnostics.extend(atom_diags)
                had_error = True
                continue
            net_expr_id = None
            if is_pattern_expression(net_name):
                net_expr_id = register_pattern_entry(
                    pattern_table,
                    pattern_cache,
                    expression=net_name,
                    kind="net",
                    loc=net_loc or module._loc,
                )

            endpoints, endpoint_error = parse_endpoints(endpoint_expr)
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

            endpoint_locs = module._net_endpoint_locs.get(net_token, [])
            net_endpoints_by_atom: List[
                List[Tuple[AtomizedEndpoint, Optional[str], Optional[object], bool]]
            ] = [[] for _ in range(len(net_atoms))]
            net_error = False
            for endpoint_index, (inst_name, port_path, suppressed) in enumerate(
                endpoints
            ):
                endpoint_loc = None
                if endpoint_index < len(endpoint_locs):
                    endpoint_loc = endpoint_locs[endpoint_index]
                endpoint_expr = f"{inst_name}.{port_path}"
                endpoint_atoms, endpoint_diags = atomize_endpoint(inst_name, port_path)
                if endpoint_atoms is None:
                    diagnostics.extend(endpoint_diags)
                    had_error = True
                    net_error = True
                    continue
                endpoint_expr_id = None
                if is_pattern_expression(endpoint_expr):
                    endpoint_expr_id = register_pattern_entry(
                        pattern_table,
                        pattern_cache,
                        expression=endpoint_expr,
                        kind="endpoint",
                        loc=net_loc or module._loc,
                    )
                if len(net_atoms) != 1 and len(endpoint_atoms) != len(net_atoms):
                    diagnostics.append(
                        diagnostic(
                            PATTERN_LENGTH_MISMATCH,
                            (
                                f"Endpoint '{endpoint_expr}' expands to "
                                f"{len(endpoint_atoms)} atoms but net '{net_name}' "
                                f"expands to {len(net_atoms)} atoms in module '{name}'"
                            ),
                            net_loc or module._loc,
                        )
                    )
                    had_error = True
                    net_error = True
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

            if net_error:
                continue

            for index, net_atom in enumerate(net_atoms):
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
                if net_expr_id is not None:
                    net_pattern_origin = pattern_origin_from_atom(net_expr_id, net_atom)
                net_endpoints[net_literal] = []
                net_pattern_origins[net_literal] = net_pattern_origin
                net_order.append(net_literal)
                if is_port and net_literal not in port_order:
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
                net_name, is_port = split_net_token(net_token)
                net_atoms, atom_diags = atomize_pattern(
                    net_name, allow_splice=not is_port
                )
                if net_atoms is None:
                    diagnostics.extend(atom_diags)
                    had_error = True
                    continue
                net_expr_id = None
                if is_pattern_expression(net_name):
                    net_expr_id = register_pattern_entry(
                        pattern_table,
                        pattern_cache,
                        expression=net_name,
                        kind="net",
                        loc=binding_loc or module._loc,
                    )

                net_endpoints_by_atom: List[
                    List[Tuple[AtomizedEndpoint, Optional[str]]]
                ] = [[] for _ in range(len(net_atoms))]
                net_error = False
                for inst_name in inst_names:
                    endpoint_expr = f"{inst_name}.{port_name}"
                    endpoint_atoms, endpoint_diags = atomize_endpoint(
                        inst_name, port_name
                    )
                    if endpoint_atoms is None:
                        diagnostics.extend(endpoint_diags)
                        had_error = True
                        net_error = True
                        break
                    endpoint_expr_id = None
                    if is_pattern_expression(endpoint_expr):
                        endpoint_expr_id = register_pattern_entry(
                            pattern_table,
                            pattern_cache,
                            expression=endpoint_expr,
                            kind="endpoint",
                            loc=binding_loc or module._loc,
                        )
                    if len(net_atoms) != 1 and len(endpoint_atoms) != len(net_atoms):
                        diagnostics.append(
                            diagnostic(
                                PATTERN_LENGTH_MISMATCH,
                                (
                                    f"Endpoint '{endpoint_expr}' expands to "
                                    f"{len(endpoint_atoms)} atoms but net '{net_name}' "
                                    f"expands to {len(net_atoms)} atoms in module "
                                    f"'{name}'"
                                ),
                                binding_loc or module._loc,
                            )
                        )
                        had_error = True
                        net_error = True
                        break

                    if len(net_atoms) == 1:
                        for endpoint_atom in endpoint_atoms:
                            net_endpoints_by_atom[0].append(
                                (endpoint_atom, endpoint_expr_id)
                            )
                    else:
                        for index, endpoint_atom in enumerate(endpoint_atoms):
                            net_endpoints_by_atom[index].append(
                                (endpoint_atom, endpoint_expr_id)
                            )

                if net_error:
                    continue

                for index, net_atom in enumerate(net_atoms):
                    net_literal = net_atom.literal
                    new_endpoints: List[EndpointOp] = []
                    for endpoint_atom, endpoint_expr_id in net_endpoints_by_atom[
                        index
                    ]:
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
                            )
                        )

                    if not new_endpoints:
                        continue

                    if net_literal not in net_endpoints:
                        net_endpoints[net_literal] = []
                        net_pattern_origin = None
                        if net_expr_id is not None:
                            net_pattern_origin = pattern_origin_from_atom(
                                net_expr_id, net_atom
                            )
                        net_pattern_origins[net_literal] = net_pattern_origin
                        net_order.append(net_literal)

                    net_endpoints[net_literal].extend(new_endpoints)
                    if is_port and net_literal not in port_order:
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
