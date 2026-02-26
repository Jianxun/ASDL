"""Net and endpoint lowering for AST -> PatternedGraph."""

from __future__ import annotations

from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from asdl.ast import ModuleDecl
from asdl.ast.location import Locatable
from asdl.core.graph_builder import PatternedGraphBuilder
from asdl.core.registries import GroupSlice, PatternExprKind
from asdl.diagnostics import Diagnostic
from asdl.patterns.parser import NamedPattern

from .ast_to_patterned_graph_diagnostics import INVALID_ENDPOINT_EXPR
from .ast_to_patterned_graph_diagnostics import _diagnostic, _register_span
from .ast_to_patterned_graph_expressions import _register_expression


def _lower_nets(
    module_name: str,
    module: ModuleDecl,
    *,
    module_id: str,
    expr_cache: Dict[tuple[PatternExprKind, str], str],
    named_patterns: Mapping[str, NamedPattern],
    diagnostics: List[Diagnostic],
    builder: PatternedGraphBuilder,
) -> List[str]:
    """Lower net declarations into a module graph.

    Args:
        module_name: Module name.
        module: Module declaration.
        module_id: Stable module identifier.
        expr_cache: Module-local cache of raw expressions to IDs.
        named_patterns: Named pattern definitions for parsing.
        diagnostics: Diagnostics list to append to.
        builder: PatternedGraph builder instance.

    Returns:
        List of port names discovered from `$` nets.
    """
    port_order: List[str] = []

    for net_token, raw_endpoints in (module.nets or {}).items():
        net_loc = module._nets_loc.get(net_token)
        net_name, is_port = _split_net_token(net_token)
        net_expr_id = _register_expression(
            net_name,
            kind="net",
            builder=builder,
            expr_cache=expr_cache,
            named_patterns=named_patterns,
            loc=net_loc,
            diagnostics=diagnostics,
            module_name=module_name,
            context="net name",
            require_single_segment=True,
        )
        if net_expr_id is None:
            continue

        if is_port:
            port_order.append(net_name)

        endpoint_locs = module._net_endpoint_locs.get(net_token, [])
        endpoints, endpoint_loc_map, group_slices = _flatten_endpoints(
            raw_endpoints,
            endpoint_locs,
            diagnostics=diagnostics,
            module_name=module_name,
            net_name=net_name,
            net_loc=net_loc or getattr(module, "_loc", None),
        )

        net_id = builder.add_net(module_id, net_expr_id)

        for token, endpoint_loc in zip(endpoints, endpoint_loc_map):
            endpoint_expr, endpoint_error = _normalize_endpoint_token(token)
            if endpoint_error is not None:
                diagnostics.append(
                    _diagnostic(
                        INVALID_ENDPOINT_EXPR,
                        f"{endpoint_error} in module '{module_name}'",
                        endpoint_loc or net_loc or getattr(module, "_loc", None),
                    )
                )
                continue
            endpoint_expr_id = _register_expression(
                endpoint_expr,
                kind="endpoint",
                builder=builder,
                expr_cache=expr_cache,
                named_patterns=named_patterns,
                loc=endpoint_loc or net_loc,
                diagnostics=diagnostics,
                module_name=module_name,
                context="endpoint expression",
            )
            if endpoint_expr_id is None:
                continue
            endpoint_id = builder.add_endpoint(module_id, net_id, endpoint_expr_id)
            builder.register_pattern_origin(endpoint_id, endpoint_expr_id, 0, 0)
            _register_span(builder, endpoint_id, endpoint_loc)

        builder.register_pattern_origin(net_id, net_expr_id, 0, 0)
        _register_span(builder, net_id, net_loc)
        builder.register_net_groups(net_id, group_slices)

    return port_order


def _split_net_token(token: str) -> Tuple[str, bool]:
    """Split a net token into name and port flag.

    Args:
        token: Raw net token.

    Returns:
        Tuple of (net name, is_port).
    """
    if token.startswith("$"):
        return token[1:], True
    return token, False


def _flatten_endpoints(
    raw_endpoints: object,
    endpoint_locs: Sequence[Optional[Locatable]],
    *,
    diagnostics: List[Diagnostic],
    module_name: str,
    net_name: str,
    net_loc: Optional[Locatable],
) -> Tuple[List[str], List[Optional[Locatable]], List[GroupSlice]]:
    """Flatten endpoint groups while preserving group slices.

    Args:
        raw_endpoints: Raw endpoints payload from the AST.
        endpoint_locs: Location entries for top-level endpoint items.
        diagnostics: Diagnostic collection to append to.
        module_name: Module name for diagnostics.
        net_name: Net name for diagnostics.
        net_loc: Net location for diagnostics.

    Returns:
        Tuple of (flattened endpoints, flattened locs, group slices).
    """
    if not isinstance(raw_endpoints, list):
        diagnostics.append(
            _diagnostic(
                INVALID_ENDPOINT_EXPR,
                (
                    "Endpoint lists must be YAML lists of '<instance>.<pin>' strings "
                    f"for net '{net_name}' in module '{module_name}'"
                ),
                net_loc,
            )
        )
        return [], [], []

    has_groups = any(isinstance(item, list) for item in raw_endpoints)
    flattened: List[str] = []
    flattened_locs: List[Optional[Locatable]] = []
    group_slices: List[GroupSlice] = []

    for index, item in enumerate(raw_endpoints):
        item_loc = endpoint_locs[index] if index < len(endpoint_locs) else None
        group_start = len(flattened)
        group_count = 0
        if isinstance(item, list):
            for entry in item:
                if not isinstance(entry, str):
                    diagnostics.append(
                        _diagnostic(
                            INVALID_ENDPOINT_EXPR,
                            (
                                f"Endpoint tokens must be strings in net '{net_name}' "
                                f"of module '{module_name}'"
                            ),
                            item_loc or net_loc,
                        )
                    )
                    continue
                flattened.append(entry)
                flattened_locs.append(item_loc)
                group_count += 1
        elif isinstance(item, str):
            flattened.append(item)
            flattened_locs.append(item_loc)
            group_count = 1
        else:
            diagnostics.append(
                _diagnostic(
                    INVALID_ENDPOINT_EXPR,
                    (
                        f"Endpoint tokens must be strings in net '{net_name}' "
                        f"of module '{module_name}'"
                    ),
                    item_loc or net_loc,
                )
            )
        if has_groups and group_count:
            group_slices.append(
                GroupSlice(start=group_start, count=group_count, label=None)
            )

    return flattened, flattened_locs, group_slices


def _normalize_endpoint_token(token: str) -> Tuple[Optional[str], Optional[str]]:
    """Normalize a raw endpoint token and validate its structure.

    Args:
        token: Raw endpoint token string.

    Returns:
        Tuple of (normalized token, error message).
    """
    raw_token = token
    if token.startswith("!"):
        token = token[1:]
    if token.count(".") != 1:
        return None, f"Invalid endpoint token '{raw_token}'; expected inst.pin"
    inst, pin = token.split(".", 1)
    if not inst or not pin:
        return None, f"Invalid endpoint token '{raw_token}'; expected inst.pin"
    return token, None
