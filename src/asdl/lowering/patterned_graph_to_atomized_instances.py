"""Instance and port-order atomization helpers."""

from __future__ import annotations

from typing import Dict, Iterable, Optional

from asdl.core.atomized_graph import AtomizedInstance
from asdl.core.graph import InstanceBundle, ModuleGraph
from asdl.core.registries import PatternExpressionRegistry
from asdl.diagnostics import Diagnostic, SourceSpan
from asdl.patterns_refactor import PatternError, PatternExpr, parse_pattern_expr

from .patterned_graph_to_atomized_context import (
    PATTERN_EXPANSION_ERROR,
    ModuleAtomizationContext,
    _diagnostic,
    _entity_span,
)
from .patterned_graph_to_atomized_patterns import (
    _expand_pattern,
    _find_expr_by_raw,
    _is_literal_expr,
    _lookup_expr,
    _pattern_error_diagnostics,
)


def _collect_module_expressions(
    module: ModuleGraph,
    expr_registry: PatternExpressionRegistry,
) -> Dict[str, PatternExpr]:
    """Collect raw pattern expressions referenced in a module.

    Args:
        module: Patterned module graph.
        expr_registry: Registry of parsed pattern expressions.

    Returns:
        Mapping of raw expression strings to parsed expressions.
    """
    expr_ids: set[str] = set()
    for net in module.nets.values():
        expr_ids.add(net.name_expr_id)
    for inst in module.instances.values():
        expr_ids.add(inst.name_expr_id)
        if inst.param_expr_ids:
            expr_ids.update(inst.param_expr_ids.values())
    for endpoint in module.endpoints.values():
        expr_ids.add(endpoint.port_expr_id)

    exprs_by_raw: Dict[str, PatternExpr] = {}
    for expr_id in expr_ids:
        expr = expr_registry.get(expr_id)
        if expr is not None:
            exprs_by_raw.setdefault(expr.raw, expr)
    for raw_name in module.port_order or []:
        if raw_name in exprs_by_raw:
            continue
        expr = _find_expr_by_raw(expr_registry, raw_name, module.file_id)
        if expr is not None:
            exprs_by_raw.setdefault(expr.raw, expr)
    return exprs_by_raw


def _expand_port_order(
    port_order: Optional[Iterable[str]],
    exprs_by_raw: Dict[str, PatternExpr],
    *,
    module_name: str,
) -> tuple[list[str], list[Diagnostic]]:
    """Expand port order expressions into literal port names.

    Args:
        port_order: Optional port order list from the PatternedGraph.
        exprs_by_raw: Parsed expressions keyed by raw string.
        module_name: Module name for diagnostics.

    Returns:
        Tuple of (expanded port order, diagnostics).
    """
    if not port_order:
        return [], []

    diagnostics: list[Diagnostic] = []
    expanded: list[str] = []
    for raw_name in port_order:
        expr = exprs_by_raw.get(raw_name)
        if expr is None:
            expr, errors = parse_pattern_expr(raw_name)
            if expr is None or errors:
                diagnostics.extend(
                    _pattern_error_diagnostics(
                        errors
                        or [PatternError(f"Failed to parse port '{raw_name}'.")],
                        context=(
                            f"port order entry '{raw_name}' in module '{module_name}'"
                        ),
                        fallback_span=None,
                    )
                )
                continue
            if not _is_literal_expr(expr):
                diagnostics.append(
                    _diagnostic(
                        PATTERN_EXPANSION_ERROR,
                        (
                            f"Port order entry '{raw_name}' in module '{module_name}' "
                            "is not a literal and is missing from the pattern "
                            "expression registry."
                        ),
                        expr.span,
                    )
                )
                continue
            expanded.append(raw_name)
            continue
        atoms = _expand_pattern(
            expr,
            diagnostics=diagnostics,
            context=f"port order entry '{raw_name}' in module '{module_name}'",
            fallback_span=expr.span,
        )
        if atoms is not None:
            expanded.extend(atoms)
    return expanded, diagnostics


def _expand_instance_params(
    inst_bundle: InstanceBundle,
    expr_registry: PatternExpressionRegistry,
    inst_atoms: list[str],
    *,
    diagnostics: list[Diagnostic],
    module_name: str,
    fallback_span: Optional[SourceSpan],
) -> Optional[list[dict[str, object]]]:
    """Expand instance parameter expressions.

    Args:
        inst_bundle: Patterned instance bundle.
        expr_registry: Pattern expression registry.
        inst_atoms: Expanded instance names.
        diagnostics: Diagnostic collection to append to.
        module_name: Module name for diagnostics.
        fallback_span: Fallback span for diagnostics.

    Returns:
        List of parameter dictionaries aligned with instance expansion order.
        Returns None when parameter expansion errors occur.
    """
    param_values: list[dict[str, object]] = [{} for _ in range(len(inst_atoms))]
    if not inst_bundle.param_expr_ids:
        return param_values

    had_error = False
    for param_name, expr_id in inst_bundle.param_expr_ids.items():
        param_expr = _lookup_expr(
            expr_id,
            expr_registry,
            span=fallback_span,
            diagnostics=diagnostics,
        )
        if param_expr is None:
            had_error = True
            continue
        param_atoms = _expand_pattern(
            param_expr,
            diagnostics=diagnostics,
            context=(
                f"instance param '{param_name}' in module '{module_name}'"
            ),
            fallback_span=fallback_span,
        )
        if param_atoms is None:
            had_error = True
            continue

        if len(param_atoms) == 1:
            for values in param_values:
                values[param_name] = param_atoms[0]
            continue
        if len(param_atoms) != len(inst_atoms):
            diagnostics.append(
                _diagnostic(
                    PATTERN_EXPANSION_ERROR,
                    (
                        "Instance param expansion length does not match instance "
                        f"count for '{param_name}' in module '{module_name}'."
                    ),
                    fallback_span or param_expr.span,
                )
            )
            had_error = True
            continue

        for index, value in enumerate(param_atoms):
            param_values[index][param_name] = value

    if had_error:
        return None
    return param_values


def atomize_instances(context: ModuleAtomizationContext) -> None:
    """Populate atomized instances for a module.

    Args:
        context: Shared atomization context.
    """
    module = context.module
    expr_registry = context.expr_registry
    diagnostics = context.diagnostics
    atomized_module = context.atomized_module
    allocator = context.allocator
    inst_name_to_id = context.inst_name_to_id
    duplicate_inst_names = context.duplicate_inst_names

    for inst_bundle in module.instances.values():
        inst_span = _entity_span(context.source_spans, inst_bundle.inst_id)
        inst_expr = _lookup_expr(
            inst_bundle.name_expr_id,
            expr_registry,
            span=inst_span,
            diagnostics=diagnostics,
        )
        if inst_expr is None:
            continue

        inst_atoms = _expand_pattern(
            inst_expr,
            diagnostics=diagnostics,
            context=f"instance '{inst_expr.raw}' in module '{module.name}'",
            fallback_span=inst_span,
        )
        if inst_atoms is None:
            continue

        param_values = _expand_instance_params(
            inst_bundle,
            expr_registry,
            inst_atoms,
            diagnostics=diagnostics,
            module_name=module.name,
            fallback_span=inst_span,
        )

        reported_duplicates: set[str] = set()
        for index, name in enumerate(inst_atoms):
            if name in inst_name_to_id:
                if name not in reported_duplicates:
                    diagnostics.append(
                        _diagnostic(
                            PATTERN_EXPANSION_ERROR,
                            (
                                "Pattern expansion for instance "
                                f"'{inst_expr.raw}' in module '{module.name}' "
                                f"produced duplicate atom '{name}'."
                            ),
                            inst_span or inst_expr.span,
                        )
                    )
                    reported_duplicates.add(name)
                    duplicate_inst_names.add(name)
                continue
            inst_id = allocator.next_inst()
            values = param_values[index] if param_values else None
            atomized_module.instances[inst_id] = AtomizedInstance(
                inst_id=inst_id,
                name=name,
                ref_kind=inst_bundle.ref_kind,
                ref_id=inst_bundle.ref_id,
                ref_raw=inst_bundle.ref_raw,
                param_values=values or None,
                patterned_inst_id=inst_bundle.inst_id,
                attrs=inst_bundle.attrs,
            )
            inst_name_to_id[name] = inst_id
