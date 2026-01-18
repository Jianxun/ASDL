"""Named pattern macro elaboration for AST documents."""

from __future__ import annotations

import re
from typing import Dict, List, Mapping, Optional, Tuple

from asdl.diagnostics import Diagnostic, Severity, format_code

from .location import Locatable
from .models import AsdlDocument, InstanceDefaultsDecl, ModuleDecl, PatternDecl

AST_NAMED_PATTERN_INVALID = format_code("AST", 20)
AST_NAMED_PATTERN_UNDEFINED = format_code("AST", 21)
AST_NAMED_PATTERN_RECURSIVE = format_code("AST", 22)

_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_REF_RE = re.compile(r"<@([^>]+)>")
_NO_SPAN_NOTE = "No source span available."


def elaborate_named_patterns(
    document: AsdlDocument,
) -> Tuple[List[Diagnostic], bool]:
    """Replace named pattern references with their module-local group tokens.

    Args:
        document: AST document to mutate in-place with substitutions.

    Returns:
        Tuple of (diagnostics, had_error).
    """
    diagnostics: List[Diagnostic] = []
    had_error = False

    for module_name, module in (document.modules or {}).items():
        pattern_map: Dict[str, str] = {}
        if module.patterns:
            for pattern_name, pattern_value in module.patterns.items():
                pattern_expr = _pattern_expr_value(pattern_value)
                name_loc = module._patterns_loc.get(pattern_name)
                value_loc = module._pattern_value_loc.get(pattern_name)
                if not _NAME_RE.fullmatch(pattern_name):
                    diagnostics.append(
                        _diagnostic(
                            AST_NAMED_PATTERN_INVALID,
                            (
                                f"Invalid named pattern '{pattern_name}' in module "
                                f"'{module_name}'."
                            ),
                            name_loc or module._loc,
                        )
                    )
                    had_error = True
                    continue
                if "<@" in pattern_expr:
                    diagnostics.append(
                        _diagnostic(
                            AST_NAMED_PATTERN_RECURSIVE,
                            (
                                f"Named pattern '{pattern_name}' in module '{module_name}' "
                                "must not reference other named patterns."
                            ),
                            value_loc or name_loc or module._loc,
                        )
                    )
                    had_error = True
                    continue
                pattern_map[pattern_name] = pattern_expr

        had_error |= _expand_module_instances(
            module,
            module_name,
            pattern_map,
            diagnostics,
        )
        had_error |= _expand_module_nets(
            module,
            module_name,
            pattern_map,
            diagnostics,
        )
        had_error |= _expand_module_instance_defaults(
            module,
            module_name,
            pattern_map,
            diagnostics,
        )

    return diagnostics, had_error


def _expand_module_instances(
    module: ModuleDecl,
    module_name: str,
    patterns: Mapping[str, str],
    diagnostics: List[Diagnostic],
) -> bool:
    """Apply named pattern substitution to instance names and params."""
    if not module.instances:
        return False

    had_error = False
    new_instances: Dict[str, str] = {}
    new_instances_loc: Dict[str, Locatable] = {}
    new_instance_expr_loc: Dict[str, Locatable] = {}

    for inst_name, inst_expr in module.instances.items():
        inst_loc = module._instances_loc.get(inst_name)
        expr_loc = module._instance_expr_loc.get(inst_name)
        new_name, name_error = _replace_named_patterns(
            inst_name,
            patterns,
            diagnostics=diagnostics,
            loc=inst_loc,
            module_name=module_name,
            context="instance name",
        )
        new_expr, expr_error = _replace_instance_params(
            inst_expr,
            patterns,
            diagnostics=diagnostics,
            loc=expr_loc,
            module_name=module_name,
        )
        had_error = had_error or name_error or expr_error
        if new_name in new_instances:
            diagnostics.append(
                _diagnostic(
                    AST_NAMED_PATTERN_INVALID,
                    (
                        f"Named pattern substitution produces duplicate instance name "
                        f"'{new_name}' in module '{module_name}'."
                    ),
                    inst_loc or module._loc,
                )
            )
            had_error = True
            continue
        new_instances[new_name] = new_expr
        if inst_loc is not None:
            new_instances_loc[new_name] = inst_loc
        if expr_loc is not None:
            new_instance_expr_loc[new_name] = expr_loc

    module.instances = new_instances
    module._instances_loc = new_instances_loc
    module._instance_expr_loc = new_instance_expr_loc
    return had_error


def _expand_module_nets(
    module: ModuleDecl,
    module_name: str,
    patterns: Mapping[str, str],
    diagnostics: List[Diagnostic],
) -> bool:
    """Apply named pattern substitution to net names and endpoints."""
    if not module.nets:
        return False

    had_error = False
    new_nets: Dict[str, object] = {}
    new_nets_loc: Dict[str, Locatable] = {}
    new_endpoint_locs: Dict[str, List[Optional[Locatable]]] = {}

    for net_name, endpoint_exprs in module.nets.items():
        net_loc = module._nets_loc.get(net_name)
        new_net_name, name_error = _replace_named_patterns(
            net_name,
            patterns,
            diagnostics=diagnostics,
            loc=net_loc,
            module_name=module_name,
            context="net name",
        )
        had_error = had_error or name_error

        endpoint_locs = module._net_endpoint_locs.get(net_name, [])
        if isinstance(endpoint_exprs, list):
            if len(endpoint_locs) < len(endpoint_exprs):
                endpoint_locs = [
                    *endpoint_locs,
                    *([None] * (len(endpoint_exprs) - len(endpoint_locs))),
                ]

            new_endpoints: List[object] = []
            for index, endpoint in enumerate(endpoint_exprs):
                if not isinstance(endpoint, str):
                    new_endpoints.append(endpoint)
                    continue
                endpoint_loc = endpoint_locs[index] if index < len(endpoint_locs) else None
                new_endpoint, endpoint_error = _replace_named_patterns(
                    endpoint,
                    patterns,
                    diagnostics=diagnostics,
                    loc=endpoint_loc,
                    module_name=module_name,
                    context="endpoint expression",
                )
                had_error = had_error or endpoint_error
                new_endpoints.append(new_endpoint)
            updated_endpoints: object = new_endpoints
        elif isinstance(endpoint_exprs, str):
            updated_endpoints, endpoint_error = _replace_named_patterns(
                endpoint_exprs,
                patterns,
                diagnostics=diagnostics,
                loc=endpoint_locs[0] if endpoint_locs else None,
                module_name=module_name,
                context="endpoint expression",
            )
            had_error = had_error or endpoint_error
        else:
            updated_endpoints = endpoint_exprs

        if new_net_name in new_nets:
            diagnostics.append(
                _diagnostic(
                    AST_NAMED_PATTERN_INVALID,
                    (
                        f"Named pattern substitution produces duplicate net name "
                        f"'{new_net_name}' in module '{module_name}'."
                    ),
                    net_loc or module._loc,
                )
            )
            had_error = True
            continue

        new_nets[new_net_name] = updated_endpoints
        if net_loc is not None:
            new_nets_loc[new_net_name] = net_loc
        new_endpoint_locs[new_net_name] = endpoint_locs

    module.nets = new_nets
    module._nets_loc = new_nets_loc
    module._net_endpoint_locs = new_endpoint_locs
    return had_error


def _expand_module_instance_defaults(
    module: ModuleDecl,
    module_name: str,
    patterns: Mapping[str, str],
    diagnostics: List[Diagnostic],
) -> bool:
    """Apply named pattern substitution to instance default bindings."""
    if not module.instance_defaults:
        return False

    had_error = False
    for defaults in module.instance_defaults.values():
        had_error |= _expand_instance_default_bindings(
            defaults,
            module_name,
            patterns,
            diagnostics,
        )
    return had_error


def _pattern_expr_value(pattern_value: object) -> str:
    """Extract the expression string from a named pattern entry.

    Args:
        pattern_value: Pattern entry value (string or PatternDecl).

    Returns:
        The pattern expression string.
    """
    if isinstance(pattern_value, PatternDecl):
        return pattern_value.expr
    if isinstance(pattern_value, str):
        return pattern_value
    raise TypeError(f"Unexpected named pattern value type: {type(pattern_value)!r}")


def _expand_instance_default_bindings(
    defaults: InstanceDefaultsDecl,
    module_name: str,
    patterns: Mapping[str, str],
    diagnostics: List[Diagnostic],
) -> bool:
    """Apply named pattern substitution to one instance default binding map."""
    if not defaults.bindings:
        return False

    had_error = False
    for binding_name, binding_value in defaults.bindings.items():
        binding_loc = defaults._bindings_loc.get(binding_name)
        new_value, value_error = _replace_named_patterns(
            binding_value,
            patterns,
            diagnostics=diagnostics,
            loc=binding_loc,
            module_name=module_name,
            context=f"instance_defaults binding '{binding_name}'",
        )
        defaults.bindings[binding_name] = new_value
        had_error = had_error or value_error
    return had_error


def _replace_instance_params(
    expr: str,
    patterns: Mapping[str, str],
    *,
    diagnostics: List[Diagnostic],
    loc: Optional[Locatable],
    module_name: str,
) -> Tuple[str, bool]:
    """Replace named pattern references in instance param values."""
    if "<@" not in expr:
        return expr, False

    tokens = expr.split()
    if not tokens:
        return expr, False

    new_tokens = [tokens[0]]
    had_error = False
    for token in tokens[1:]:
        if "=" not in token:
            new_token, token_error = _replace_named_patterns(
                token,
                patterns,
                diagnostics=diagnostics,
                loc=loc,
                module_name=module_name,
                context="instance param",
            )
            had_error = had_error or token_error
            new_tokens.append(new_token)
            continue
        key, value = token.split("=", 1)
        new_value, value_error = _replace_named_patterns(
            value,
            patterns,
            diagnostics=diagnostics,
            loc=loc,
            module_name=module_name,
            context=f"instance param '{key}'",
        )
        had_error = had_error or value_error
        new_tokens.append(f"{key}={new_value}")

    return " ".join(new_tokens), had_error


def _replace_named_patterns(
    expression: str,
    patterns: Mapping[str, str],
    *,
    diagnostics: List[Diagnostic],
    loc: Optional[Locatable],
    module_name: str,
    context: str,
) -> Tuple[str, bool]:
    """Replace named pattern references in a single expression."""
    if "<@" not in expression:
        return expression, False

    had_error = False

    def _replace(match: re.Match[str]) -> str:
        nonlocal had_error
        name = match.group(1)
        if not _NAME_RE.fullmatch(name):
            diagnostics.append(
                _diagnostic(
                    AST_NAMED_PATTERN_INVALID,
                    (
                        f"Invalid named pattern reference '<@{name}>' in {context} "
                        f"of module '{module_name}'."
                    ),
                    loc,
                )
            )
            had_error = True
            return match.group(0)
        value = patterns.get(name)
        if value is None:
            diagnostics.append(
                _diagnostic(
                    AST_NAMED_PATTERN_UNDEFINED,
                    (
                        f"Undefined named pattern '<@{name}>' in {context} of module "
                        f"'{module_name}'."
                    ),
                    loc,
                )
            )
            had_error = True
            return match.group(0)
        return value

    return _REF_RE.sub(_replace, expression), had_error


def _diagnostic(code: str, message: str, loc: Optional[Locatable]) -> Diagnostic:
    """Build a named pattern diagnostic with optional source span."""
    span = loc.to_source_span() if loc is not None else None
    notes = None if span is not None else [_NO_SPAN_NOTE]
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        message=message,
        primary_span=span,
        notes=notes,
        source="ast",
    )


__all__ = [
    "AST_NAMED_PATTERN_INVALID",
    "AST_NAMED_PATTERN_UNDEFINED",
    "AST_NAMED_PATTERN_RECURSIVE",
    "elaborate_named_patterns",
]
