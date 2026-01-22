"""Lower AST documents into PatternedGraph bundles."""

from __future__ import annotations

from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from asdl.ast import AsdlDocument, ModuleDecl, PatternDecl
from asdl.ast.location import Locatable
from asdl.core.graph import ProgramGraph
from asdl.core.graph_builder import PatternedGraphBuilder
from asdl.core.registries import GroupSlice
from asdl.diagnostics import Diagnostic, Severity, SourceSpan, format_code
from asdl.patterns_refactor.parser import (
    NamedPattern,
    PatternError,
    parse_pattern_expr,
)

PATTERN_PARSE_ERROR = format_code("IR", 3)
INVALID_INSTANCE_EXPR = format_code("IR", 1)
INVALID_ENDPOINT_EXPR = format_code("IR", 2)
UNKNOWN_REFERENCE = INVALID_INSTANCE_EXPR
AMBIGUOUS_REFERENCE = INVALID_INSTANCE_EXPR

NO_SPAN_NOTE = "No source span available."


def build_patterned_graph(
    document: AsdlDocument,
    *,
    file_id: Optional[str] = None,
) -> Tuple[ProgramGraph, List[Diagnostic]]:
    """Lower a parsed AST document into a PatternedGraph program.

    Args:
        document: Parsed AST document.
        file_id: Optional file identifier to attach to module graphs.

    Returns:
        Tuple of (ProgramGraph, diagnostics).
    """
    diagnostics: List[Diagnostic] = []
    builder = PatternedGraphBuilder()

    module_graphs: Dict[str, str] = {}
    for name, module in (document.modules or {}).items():
        module_graph = builder.add_module(name, _resolve_file_id(file_id, module))
        module_graphs[name] = module_graph.module_id
        _register_span(builder, module_graph.module_id, getattr(module, "_loc", None))

    device_ids = _allocate_ids((document.devices or {}).keys(), "d")

    for name, module in (document.modules or {}).items():
        module_id = module_graphs[name]
        _lower_module(
            name,
            module,
            module_id=module_id,
            module_ids=module_graphs,
            device_ids=device_ids,
            diagnostics=diagnostics,
            builder=builder,
        )

    return builder.build(), diagnostics


def _allocate_ids(names: Iterable[str], prefix: str) -> Dict[str, str]:
    """Allocate deterministic identifiers for named symbols.

    Args:
        names: Ordered sequence of names.
        prefix: Prefix for the identifiers.

    Returns:
        Mapping of name to allocated identifier.
    """
    return {name: f"{prefix}{index}" for index, name in enumerate(names, start=1)}


def _resolve_file_id(file_id: Optional[str], module: ModuleDecl) -> str:
    """Resolve a module file identifier with best-effort fallbacks.

    Args:
        file_id: Optional explicit file identifier.
        module: Module declaration for span fallback.

    Returns:
        File identifier string.
    """
    if file_id:
        return file_id
    module_loc = getattr(module, "_loc", None)
    if module_loc is not None and module_loc.file:
        return module_loc.file
    return "<unknown>"


def _lower_module(
    name: str,
    module: ModuleDecl,
    *,
    module_id: str,
    module_ids: Mapping[str, str],
    device_ids: Mapping[str, str],
    diagnostics: List[Diagnostic],
    builder: PatternedGraphBuilder,
) -> None:
    """Lower a module declaration into a ModuleGraph.

    Args:
        name: Module name.
        module: Module declaration.
        module_id: Stable module identifier.
        module_ids: Mapping of module names to IDs.
        device_ids: Mapping of device names to IDs.
        diagnostics: Diagnostics list to append to.
        builder: PatternedGraph builder instance.
    """
    expr_cache: Dict[str, str] = {}
    named_patterns = _collect_named_patterns(module)

    port_order: List[str] = []
    instance_refs: set[str] = set()

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
            module_name=name,
            context="instance name",
        )
        if inst_expr_id is None:
            continue

        ref, params, parse_error = _parse_instance_expr(inst_expr)
        if parse_error is not None or ref is None:
            diagnostics.append(
                _diagnostic(
                    INVALID_INSTANCE_EXPR,
                    f"{parse_error or 'Instance expression missing reference'} in module '{name}'",
                    inst_loc or getattr(module, "_loc", None),
                )
            )
            continue

        resolved = _resolve_reference(
            ref,
            module_ids=module_ids,
            device_ids=device_ids,
            module_name=name,
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
                    module_name=name,
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

    for net_token, raw_endpoints in (module.nets or {}).items():
        net_loc = module._nets_loc.get(net_token)
        net_name, is_port = _split_net_token(net_token)
        net_expr_id = _register_expression(
            net_name,
            builder=builder,
            expr_cache=expr_cache,
            named_patterns=named_patterns,
            loc=net_loc,
            diagnostics=diagnostics,
            module_name=name,
            context="net name",
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
            module_name=name,
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
                        f"{endpoint_error} in module '{name}'",
                        endpoint_loc or net_loc or getattr(module, "_loc", None),
                    )
                )
                continue
            endpoint_expr_id = _register_expression(
                endpoint_expr,
                builder=builder,
                expr_cache=expr_cache,
                named_patterns=named_patterns,
                loc=endpoint_loc or net_loc,
                diagnostics=diagnostics,
                module_name=name,
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

    if module.instance_defaults and instance_refs:
        for ref, defaults in module.instance_defaults.items():
            if ref not in instance_refs:
                continue
            for net_token in defaults.bindings.values():
                net_name, is_port = _split_net_token(net_token)
                if is_port and net_name not in port_order:
                    port_order.append(net_name)

    builder.set_port_order(module_id, port_order or None)


def _collect_named_patterns(module: ModuleDecl) -> Dict[str, NamedPattern]:
    """Collect named pattern definitions from a module.

    Args:
        module: Module declaration with optional patterns block.

    Returns:
        Mapping of pattern names to NamedPattern definitions.
    """
    named_patterns: Dict[str, NamedPattern] = {}
    for name, value in (module.patterns or {}).items():
        if isinstance(value, PatternDecl):
            named_patterns[name] = NamedPattern(expr=value.expr, tag=value.tag)
        else:
            named_patterns[name] = NamedPattern(expr=str(value))
    return named_patterns


def _register_expression(
    expression: str,
    *,
    builder: PatternedGraphBuilder,
    expr_cache: Dict[str, str],
    named_patterns: Mapping[str, NamedPattern],
    loc: Optional[Locatable],
    diagnostics: List[Diagnostic],
    module_name: str,
    context: str,
) -> Optional[str]:
    """Register and parse a pattern expression.

    Args:
        expression: Raw expression string to parse.
        builder: PatternedGraph builder instance.
        expr_cache: Module-local cache of raw expressions to IDs.
        named_patterns: Named pattern definitions for parsing.
        loc: Optional source location for spans.
        diagnostics: Diagnostic collection to append to.
        module_name: Module name for context.
        context: Short string describing the expression context.

    Returns:
        Expression ID or None on parse failure.
    """
    cached = expr_cache.get(expression)
    if cached is not None:
        return cached

    span = loc.to_source_span() if loc is not None else None
    parsed, errors = parse_pattern_expr(
        expression,
        named_patterns=named_patterns,
        span=span,
    )
    if errors:
        diagnostics.extend(
            _pattern_error_diagnostics(
                errors,
                module_name=module_name,
                context=context,
                fallback_loc=loc,
            )
        )
        return None
    if parsed is None:
        diagnostics.append(
            _diagnostic(
                PATTERN_PARSE_ERROR,
                f"Failed to parse '{expression}' in module '{module_name}'",
                loc,
            )
        )
        return None

    expr_id = builder.add_expression(parsed)
    expr_cache[expression] = expr_id
    return expr_id


def _pattern_error_diagnostics(
    errors: Sequence[PatternError],
    *,
    module_name: str,
    context: str,
    fallback_loc: Optional[Locatable],
) -> List[Diagnostic]:
    """Convert pattern parse errors to diagnostics.

    Args:
        errors: Pattern parse errors.
        module_name: Module name for context.
        context: Expression context description.
        fallback_loc: Fallback location if the error span is missing.

    Returns:
        List of diagnostics for the errors.
    """
    diagnostics: List[Diagnostic] = []
    for error in errors:
        span = error.span
        if span is None and fallback_loc is not None:
            span = fallback_loc.to_source_span()
        notes = None
        if span is None:
            notes = [NO_SPAN_NOTE]
        diagnostics.append(
            Diagnostic(
                code=PATTERN_PARSE_ERROR,
                severity=Severity.ERROR,
                message=f"{error.message} in module '{module_name}' ({context}).",
                primary_span=span,
                notes=notes,
                source="core",
            )
        )
    return diagnostics


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


def _register_span(
    builder: PatternedGraphBuilder,
    entity_id: str,
    loc: Optional[Locatable],
) -> None:
    """Register a source span for an entity when available.

    Args:
        builder: PatternedGraph builder instance.
        entity_id: Graph entity identifier.
        loc: Optional location payload.
    """
    if loc is None:
        return
    span = loc.to_source_span()
    if span is not None:
        builder.register_source_span(entity_id, span)


def _diagnostic(
    code: str,
    message: str,
    loc: Optional[Locatable],
    *,
    severity: Severity = Severity.ERROR,
) -> Diagnostic:
    """Create a diagnostic with optional location metadata.

    Args:
        code: Diagnostic code.
        message: Diagnostic message.
        loc: Optional location payload.
        severity: Diagnostic severity.

    Returns:
        Diagnostic instance.
    """
    span: Optional[SourceSpan] = None
    if loc is not None:
        span = loc.to_source_span()
    notes = None
    if span is None:
        notes = [NO_SPAN_NOTE]
    return Diagnostic(
        code=code,
        severity=severity,
        message=message,
        primary_span=span,
        notes=notes,
        source="core",
    )


__all__ = ["build_patterned_graph"]
