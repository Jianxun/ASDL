"""Instance lowering for AST -> PatternedGraph."""

from __future__ import annotations

from typing import Dict, List, Mapping, Optional, Set, Tuple

from asdl.ast import ModuleDecl
from asdl.ast.location import Locatable
from asdl.core.graph_builder import PatternedGraphBuilder
from asdl.diagnostics import Diagnostic
from asdl.patterns_refactor.parser import NamedPattern

from .ast_to_patterned_graph_diagnostics import (
    AMBIGUOUS_REFERENCE,
    INVALID_INSTANCE_EXPR,
    UNKNOWN_REFERENCE,
)
from .ast_to_patterned_graph_diagnostics import _diagnostic, _register_span
from .ast_to_patterned_graph_expressions import _register_expression


def _lower_instances(
    module_name: str,
    module: ModuleDecl,
    *,
    module_id: str,
    module_ids: Mapping[str, str],
    device_ids: Mapping[str, str],
    expr_cache: Dict[str, str],
    named_patterns: Mapping[str, NamedPattern],
    diagnostics: List[Diagnostic],
    builder: PatternedGraphBuilder,
) -> Set[str]:
    """Lower instance declarations into a module graph.

    Args:
        module_name: Module name.
        module: Module declaration.
        module_id: Stable module identifier.
        module_ids: Mapping of module names to IDs.
        device_ids: Mapping of device names to IDs.
        expr_cache: Module-local cache of raw expressions to IDs.
        named_patterns: Named pattern definitions for parsing.
        diagnostics: Diagnostics list to append to.
        builder: PatternedGraph builder instance.

    Returns:
        Set of instance reference names used by the module.
    """
    instance_refs: Set[str] = set()

    for inst_name, inst_expr in (module.instances or {}).items():
        inst_loc = module._instances_loc.get(inst_name)
        inst_expr_loc = module._instance_expr_loc.get(inst_name)
        inst_expr_id = _register_expression(
            inst_name,
            builder=builder,
            expr_cache=expr_cache,
            named_patterns=named_patterns,
            loc=inst_loc,
            diagnostics=diagnostics,
            module_name=module_name,
            context="instance name",
        )
        if inst_expr_id is None:
            continue

        ref, params, parse_error = _parse_instance_expr(inst_expr)
        if parse_error is not None or ref is None:
            diagnostics.append(
                _diagnostic(
                    INVALID_INSTANCE_EXPR,
                    (
                        f"{parse_error or 'Instance expression missing reference'} "
                        f"in module '{module_name}'"
                    ),
                    inst_loc or getattr(module, "_loc", None),
                )
            )
            continue

        resolved = _resolve_reference(
            ref,
            module_ids=module_ids,
            device_ids=device_ids,
            module_name=module_name,
            loc=inst_loc,
            diagnostics=diagnostics,
        )
        if resolved is None:
            continue

        instance_refs.add(ref)
        param_expr_ids: Dict[str, str] = {}
        if params:
            for param_name, param_expr in params.items():
                param_expr_id = _register_expression(
                    param_expr,
                    builder=builder,
                    expr_cache=expr_cache,
                    named_patterns=named_patterns,
                    loc=inst_expr_loc or inst_loc,
                    diagnostics=diagnostics,
                    module_name=module_name,
                    context=f"instance param '{param_name}'",
                )
                if param_expr_id is None:
                    continue
                param_expr_ids[param_name] = param_expr_id

        inst_id = builder.add_instance(
            module_id,
            inst_expr_id,
            ref_kind=resolved[0],
            ref_id=resolved[1],
            ref_raw=ref,
            param_expr_ids=param_expr_ids or None,
        )
        builder.register_pattern_origin(inst_id, inst_expr_id, 0, 0)
        if params:
            for param_name, param_expr_id in param_expr_ids.items():
                builder.register_param_origin(inst_id, param_name, param_expr_id, 0)
        _register_span(builder, inst_id, inst_loc)

    return instance_refs


def _parse_instance_expr(expr: str) -> Tuple[Optional[str], Dict[str, str], Optional[str]]:
    """Parse instance expressions into a reference and params.

    Args:
        expr: Instance expression string.

    Returns:
        Tuple of (reference, params, error message).
    """
    tokens = expr.split()
    if not tokens:
        return None, {}, "Instance expression must start with a model name"
    ref = tokens[0]
    params: Dict[str, str] = {}
    for token in tokens[1:]:
        if "=" not in token:
            return None, {}, f"Invalid instance param token '{token}'; expected key=value"
        key, value = token.split("=", 1)
        if not key or not value:
            return None, {}, f"Invalid instance param token '{token}'; expected key=value"
        params[key] = value
    return ref, params, None


def _resolve_reference(
    ref: str,
    *,
    module_ids: Mapping[str, str],
    device_ids: Mapping[str, str],
    module_name: str,
    loc: Optional[Locatable],
    diagnostics: List[Diagnostic],
) -> Optional[Tuple[str, str]]:
    """Resolve instance references against module and device symbols.

    Args:
        ref: Reference token from the instance expression.
        module_ids: Mapping of module names to IDs.
        device_ids: Mapping of device names to IDs.
        module_name: Module name for diagnostics.
        loc: Source location for diagnostics.
        diagnostics: Diagnostic collection to append to.

    Returns:
        Tuple of (ref_kind, ref_id) or None on failure.
    """
    module_id = module_ids.get(ref)
    device_id = device_ids.get(ref)
    if module_id and device_id:
        diagnostics.append(
            _diagnostic(
                AMBIGUOUS_REFERENCE,
                (
                    f"Reference '{ref}' is ambiguous between module and device "
                    f"in module '{module_name}'"
                ),
                loc,
            )
        )
        return None
    if module_id:
        return "module", module_id
    if device_id:
        return "device", device_id
    diagnostics.append(
        _diagnostic(
            UNKNOWN_REFERENCE,
            f"Unresolved instance reference '{ref}' in module '{module_name}'",
            loc,
        )
    )
    return None
