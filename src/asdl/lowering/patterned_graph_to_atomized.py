"""Lower PatternedGraph programs into AtomizedGraph representations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional

from asdl.core.atomized_graph import (
    AtomizedEndpoint,
    AtomizedInstance,
    AtomizedModuleGraph,
    AtomizedNet,
    AtomizedProgramGraph,
)
from asdl.core.graph import (
    InstanceBundle,
    ModuleGraph,
    NetBundle,
    ProgramGraph,
)
from asdl.core.registries import PatternExpressionRegistry, SourceSpanIndex
from asdl.diagnostics import Diagnostic, Severity, SourceSpan, format_code
from asdl.patterns_refactor import (
    BindingPlan,
    PatternError,
    PatternExpr,
    bind_patterns,
    expand_endpoint,
    expand_pattern,
    parse_pattern_expr,
)

PATTERN_EXPANSION_ERROR = format_code("IR", 3)
INVALID_ENDPOINT_EXPR = format_code("IR", 2)
NO_SPAN_NOTE = "No source span available."


@dataclass
class _IdAllocator:
    """Deterministic ID allocator for atomized entities.

    Attributes:
        net_count: Counter for atomized nets.
        inst_count: Counter for atomized instances.
        endpoint_count: Counter for atomized endpoints.
    """

    net_count: int = 0
    inst_count: int = 0
    endpoint_count: int = 0

    def next_net(self) -> str:
        """Return the next atomized net identifier.

        Returns:
            New atomized net identifier.
        """
        self.net_count += 1
        return f"an{self.net_count}"

    def next_inst(self) -> str:
        """Return the next atomized instance identifier.

        Returns:
            New atomized instance identifier.
        """
        self.inst_count += 1
        return f"ai{self.inst_count}"

    def next_endpoint(self) -> str:
        """Return the next atomized endpoint identifier.

        Returns:
            New atomized endpoint identifier.
        """
        self.endpoint_count += 1
        return f"ae{self.endpoint_count}"


def build_atomized_graph(
    graph: ProgramGraph,
) -> tuple[AtomizedProgramGraph, list[Diagnostic]]:
    """Lower a PatternedGraph program into an AtomizedGraph program.

    Args:
        graph: PatternedGraph program to atomize.

    Returns:
        Tuple of (atomized program graph, diagnostics).
    """
    diagnostics: list[Diagnostic] = []
    expr_registry = graph.registries.pattern_expressions
    if expr_registry is None:
        diagnostics.append(
            _diagnostic(
                PATTERN_EXPANSION_ERROR,
                "Pattern expression registry missing for atomization.",
                None,
            )
        )
        return AtomizedProgramGraph(), diagnostics

    source_spans = graph.registries.source_spans
    atomized = AtomizedProgramGraph()

    for module_id, module in graph.modules.items():
        allocator = _IdAllocator()
        atomized_module = AtomizedModuleGraph(
            module_id=module_id,
            name=module.name,
            file_id=module.file_id,
            port_order=None,
            patterned_module_id=module.module_id,
        )
        atomized.modules[module_id] = atomized_module

        module_exprs = _collect_module_expressions(module, expr_registry)
        port_order, port_diags = _expand_port_order(
            module.port_order,
            module_exprs,
            module_name=module.name,
        )
        diagnostics.extend(port_diags)
        atomized_module.port_order = port_order or None

        inst_name_to_ids: Dict[str, list[str]] = {}
        for inst_bundle in module.instances.values():
            inst_span = _entity_span(source_spans, inst_bundle.inst_id)
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
                if name in inst_name_to_ids:
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
                inst_name_to_ids.setdefault(name, []).append(inst_id)

        net_name_to_id: Dict[str, str] = {}
        for net_bundle in module.nets.values():
            net_span = _entity_span(source_spans, net_bundle.net_id)
            net_expr = _lookup_expr(
                net_bundle.name_expr_id,
                expr_registry,
                span=net_span,
                diagnostics=diagnostics,
            )
            if net_expr is None:
                continue

            net_atoms = _expand_pattern(
                net_expr,
                diagnostics=diagnostics,
                context=f"net '{net_expr.raw}' in module '{module.name}'",
                fallback_span=net_span,
            )
            if net_atoms is None:
                continue

            net_atom_ids: list[str] = []
            reported_duplicates: set[str] = set()
            for name in net_atoms:
                existing_id = net_name_to_id.get(name)
                if existing_id is not None:
                    if name not in reported_duplicates:
                        diagnostics.append(
                            _diagnostic(
                                PATTERN_EXPANSION_ERROR,
                                (
                                    "Pattern expansion for net "
                                    f"'{net_expr.raw}' in module '{module.name}' "
                                    f"produced duplicate atom '{name}'."
                                ),
                                net_span or net_expr.span,
                            )
                        )
                        reported_duplicates.add(name)
                    net_atom_ids.append(existing_id)
                    continue
                net_id = allocator.next_net()
                atomized_module.nets[net_id] = AtomizedNet(
                    net_id=net_id,
                    name=name,
                    endpoint_ids=[],
                    patterned_net_id=net_bundle.net_id,
                    attrs=net_bundle.attrs,
                )
                net_name_to_id[name] = net_id
                net_atom_ids.append(net_id)

            _expand_endpoints_for_net(
                net_bundle,
                module,
                net_expr,
                net_atom_ids,
                inst_name_to_ids,
                expr_registry,
                source_spans=source_spans,
                allocator=allocator,
                atomized_module=atomized_module,
                diagnostics=diagnostics,
            )

    return atomized, diagnostics


def _expand_endpoints_for_net(
    net_bundle: NetBundle,
    module: ModuleGraph,
    net_expr: PatternExpr,
    net_atom_ids: list[str],
    inst_name_to_ids: Dict[str, list[str]],
    expr_registry: PatternExpressionRegistry,
    *,
    source_spans: Optional[SourceSpanIndex],
    allocator: _IdAllocator,
    atomized_module: AtomizedModuleGraph,
    diagnostics: list[Diagnostic],
) -> None:
    """Expand endpoint expressions for a net bundle.

    Args:
        net_bundle: Patterned net bundle with endpoint references.
        module: Patterned module graph containing the endpoint bundles.
        net_expr: Parsed net name expression.
        net_atom_ids: Ordered atomized net identifiers.
        inst_name_to_ids: Mapping of instance names to atomized IDs.
        expr_registry: Registry of parsed pattern expressions.
        source_spans: Optional source span registry.
        allocator: ID allocator for atomized entities.
        atomized_module: Target atomized module to populate.
        diagnostics: Diagnostic collection to append to.
    """
    for endpoint_id in net_bundle.endpoint_ids:
        endpoint_bundle = module.endpoints.get(endpoint_id)
        if endpoint_bundle is None:
            continue
        endpoint_expr = _lookup_expr(
            endpoint_bundle.port_expr_id,
            expr_registry,
            span=_entity_span(source_spans, endpoint_bundle.endpoint_id),
            diagnostics=diagnostics,
        )
        if endpoint_expr is None:
            continue

        endpoint_atoms = _expand_endpoint(
            endpoint_expr,
            diagnostics=diagnostics,
            context=f"endpoint '{endpoint_expr.raw}' in module '{module.name}'",
            fallback_span=_entity_span(source_spans, endpoint_bundle.endpoint_id),
        )
        if endpoint_atoms is None:
            continue

        plan = _bind_patterns(
            net_expr,
            endpoint_expr,
            net_expr_id=net_bundle.name_expr_id,
            endpoint_expr_id=endpoint_bundle.port_expr_id,
            diagnostics=diagnostics,
            context=(
                f"net '{net_expr.raw}' to endpoint '{endpoint_expr.raw}' in "
                f"module '{module.name}'"
            ),
            fallback_span=_entity_span(source_spans, endpoint_bundle.endpoint_id),
        )
        if plan is None:
            continue

        for endpoint_index, (inst_name, port) in enumerate(endpoint_atoms):
            inst_ids = inst_name_to_ids.get(inst_name)
            if inst_ids is None:
                diagnostics.append(
                    _diagnostic(
                        INVALID_ENDPOINT_EXPR,
                        (
                            f"Endpoint '{endpoint_expr.raw}' references unknown "
                            f"instance '{inst_name}' in module '{module.name}'."
                        ),
                        _entity_span(source_spans, endpoint_bundle.endpoint_id),
                    )
                )
                continue
            if len(inst_ids) > 1:
                diagnostics.append(
                    _diagnostic(
                        INVALID_ENDPOINT_EXPR,
                        (
                            f"Endpoint '{endpoint_expr.raw}' references non-unique "
                            f"instance '{inst_name}' in module '{module.name}'."
                        ),
                        _entity_span(source_spans, endpoint_bundle.endpoint_id),
                    )
                )
                continue

            net_index = plan.map_index(0, endpoint_index)
            if net_index >= len(net_atom_ids):
                diagnostics.append(
                    _diagnostic(
                        PATTERN_EXPANSION_ERROR,
                        (
                            "Endpoint binding produced an out-of-range net index "
                            f"for '{net_expr.raw}' in module '{module.name}'."
                        ),
                        _entity_span(source_spans, endpoint_bundle.endpoint_id),
                    )
                )
                continue

            net_id = net_atom_ids[net_index]
            endpoint_atom_id = allocator.next_endpoint()
            atomized_module.endpoints[endpoint_atom_id] = AtomizedEndpoint(
                endpoint_id=endpoint_atom_id,
                net_id=net_id,
                inst_id=inst_ids[0],
                port=port,
                patterned_endpoint_id=endpoint_bundle.endpoint_id,
                attrs=endpoint_bundle.attrs,
            )
            atomized_module.nets[net_id].endpoint_ids.append(endpoint_atom_id)


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


def _lookup_expr(
    expr_id: str,
    expr_registry: PatternExpressionRegistry,
    *,
    span: Optional[SourceSpan],
    diagnostics: list[Diagnostic],
) -> Optional[PatternExpr]:
    """Lookup a pattern expression by ID and emit a diagnostic on miss.

    Args:
        expr_id: Pattern expression identifier.
        expr_registry: Registry of parsed pattern expressions.
        span: Optional source span for diagnostics.
        diagnostics: Diagnostic collection to append to.

    Returns:
        Parsed pattern expression or None when missing.
    """
    expr = expr_registry.get(expr_id)
    if expr is None:
        diagnostics.append(
            _diagnostic(
                PATTERN_EXPANSION_ERROR,
                f"Missing pattern expression '{expr_id}'.",
                span,
            )
        )
    return expr


def _expand_pattern(
    expr: PatternExpr,
    *,
    diagnostics: list[Diagnostic],
    context: str,
    fallback_span: Optional[SourceSpan],
) -> Optional[list[str]]:
    """Expand a pattern expression to atoms with diagnostics.

    Args:
        expr: Pattern expression to expand.
        diagnostics: Diagnostic collection to append to.
        context: Context string for error messages.
        fallback_span: Fallback span when the error lacks location data.

    Returns:
        List of literal atoms or None on failure.
    """
    atoms, errors = expand_pattern(expr)
    if atoms is None:
        diagnostics.extend(
            _pattern_error_diagnostics(
                errors,
                context=context,
                fallback_span=fallback_span,
            )
        )
        return None
    return atoms


def _expand_endpoint(
    expr: PatternExpr,
    *,
    diagnostics: list[Diagnostic],
    context: str,
    fallback_span: Optional[SourceSpan],
) -> Optional[list[tuple[str, str]]]:
    """Expand an endpoint expression to (inst, pin) atoms.

    Args:
        expr: Pattern expression to expand.
        diagnostics: Diagnostic collection to append to.
        context: Context string for error messages.
        fallback_span: Fallback span when the error lacks location data.

    Returns:
        List of (instance, port) atoms or None on failure.
    """
    atoms, errors = expand_endpoint(expr)
    if atoms is None:
        diagnostics.extend(
            _pattern_error_diagnostics(
                errors,
                context=context,
                fallback_span=fallback_span,
            )
        )
        return None
    return atoms


def _bind_patterns(
    net_expr: PatternExpr,
    endpoint_expr: PatternExpr,
    *,
    net_expr_id: str,
    endpoint_expr_id: str,
    diagnostics: list[Diagnostic],
    context: str,
    fallback_span: Optional[SourceSpan],
) -> Optional[BindingPlan]:
    """Bind net and endpoint expressions with diagnostics.

    Args:
        net_expr: Parsed net expression.
        endpoint_expr: Parsed endpoint expression.
        net_expr_id: Net expression identifier.
        endpoint_expr_id: Endpoint expression identifier.
        diagnostics: Diagnostic collection to append to.
        context: Context string for error messages.
        fallback_span: Fallback span when the error lacks location data.

    Returns:
        Binding plan or None on failure.
    """
    plan, errors = bind_patterns(
        net_expr,
        endpoint_expr,
        net_expr_id=net_expr_id,
        endpoint_expr_id=endpoint_expr_id,
    )
    if plan is None:
        diagnostics.extend(
            _pattern_error_diagnostics(
                errors,
                context=context,
                fallback_span=fallback_span,
            )
        )
    return plan


def _pattern_error_diagnostics(
    errors: Iterable[PatternError],
    *,
    context: str,
    fallback_span: Optional[SourceSpan],
) -> list[Diagnostic]:
    """Convert pattern errors to diagnostics with context.

    Args:
        errors: Pattern errors to convert.
        context: Context string for error messages.
        fallback_span: Fallback span when the error lacks location data.

    Returns:
        List of diagnostics derived from pattern errors.
    """
    diagnostics: list[Diagnostic] = []
    for error in errors:
        diagnostics.append(
            _diagnostic(
                PATTERN_EXPANSION_ERROR,
                f"{error.message} ({context}).",
                error.span or fallback_span,
            )
        )
    return diagnostics


def _diagnostic(
    code: str,
    message: str,
    span: Optional[SourceSpan],
) -> Diagnostic:
    """Create a diagnostic with a fallback no-span note.

    Args:
        code: Diagnostic code.
        message: Diagnostic message.
        span: Optional source span.

    Returns:
        Diagnostic object with severity set to error.
    """
    notes = None
    if span is None:
        notes = [NO_SPAN_NOTE]
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        message=message,
        primary_span=span,
        notes=notes,
        source="core",
    )


def _entity_span(
    source_spans: Optional[SourceSpanIndex],
    entity_id: str,
) -> Optional[SourceSpan]:
    """Lookup a source span for a graph entity.

    Args:
        source_spans: Optional source span registry.
        entity_id: Graph entity identifier.

    Returns:
        Source span when available, otherwise None.
    """
    if source_spans is None:
        return None
    return source_spans.get(entity_id)


__all__ = ["build_atomized_graph"]
