"""Net and endpoint lowering helpers for AST to GraphIR conversion."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from asdl.ast import ModuleDecl
from asdl.diagnostics import Diagnostic
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


def lower_module_nets(
    name: str,
    module: ModuleDecl,
    *,
    context: GraphIrDocumentContext,
    pattern_table: PatternExpressionTable,
    pattern_cache: Dict[Tuple[str, str], str],
    diagnostics: List[Diagnostic],
    inst_name_to_id: Dict[str, str],
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

    Returns:
        Net ops, port order list, and error flag.
    """
    net_ops: List[NetOp] = []
    port_order: List[str] = []
    if not module.nets:
        return net_ops, port_order, False

    had_error = False
    for net_name, endpoint_expr in module.nets.items():
        net_loc = module._nets_loc.get(net_name)
        net_name, is_port = split_net_token(net_name)
        net_atoms, atom_diags = atomize_pattern(net_name, allow_splice=not is_port)
        if net_atoms is None:
            diagnostics.extend(atom_diags)
            had_error = True
            continue
        net_is_pattern = is_pattern_expression(net_name)
        net_expr_id = None
        if net_is_pattern:
            net_expr_id = register_pattern_entry(
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
            if is_pattern_expression(endpoint_expr):
                endpoint_expr_id = register_pattern_entry(
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
                    endpoint_pattern_origin = pattern_origin_from_atom(
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
                net_pattern_origin = pattern_origin_from_atom(net_expr_id, net_atom)
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

    return net_ops, port_order, had_error


__all__ = ["lower_module_nets"]
