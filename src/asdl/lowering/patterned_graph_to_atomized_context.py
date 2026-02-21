"""Shared context and diagnostics helpers for PatternedGraph atomization."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Optional

from asdl.core.atomized_graph import AtomizedModuleGraph
from asdl.core.graph import ModuleGraph
from asdl.core.registries import PatternExpressionRegistry, SourceSpanIndex
from asdl.diagnostics import Diagnostic, Severity, SourceSpan, format_code

PATTERN_EXPANSION_ERROR = format_code("IR", 3)
INVALID_ENDPOINT_EXPR = format_code("IR", 2)
UNDEFINED_MODULE_VARIABLE = format_code("IR", 12)
RECURSIVE_MODULE_VARIABLE = format_code("IR", 13)
NO_SPAN_NOTE = "No source span available."
_VAR_PLACEHOLDER_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


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


@dataclass
class ModuleAtomizationContext:
    """Shared per-module state used during atomization.

    Attributes:
        module: Source PatternedGraph module graph.
        atomized_module: Target atomized module graph.
        expr_registry: Registry of parsed pattern expressions.
        source_spans: Optional source span registry.
        allocator: ID allocator for atomized entities.
        diagnostics: Diagnostic collection to append to.
        inst_name_to_id: Map of instance atom names to atomized IDs.
        duplicate_inst_names: Instance names with duplicate atoms.
        endpoint_keys: Instance-port pairs already bound to a net.
        net_name_to_id: Map of net atom names to atomized IDs.
        net_spans: Net atom IDs to source span (if available).
    """

    module: ModuleGraph
    atomized_module: AtomizedModuleGraph
    expr_registry: PatternExpressionRegistry
    source_spans: Optional[SourceSpanIndex]
    allocator: _IdAllocator
    diagnostics: list[Diagnostic]
    inst_name_to_id: Dict[str, str] = field(default_factory=dict)
    duplicate_inst_names: set[str] = field(default_factory=set)
    endpoint_keys: set[tuple[str, str]] = field(default_factory=set)
    net_name_to_id: Dict[str, str] = field(default_factory=dict)
    net_spans: Dict[str, Optional[SourceSpan]] = field(default_factory=dict)
    resolved_module_variables: Dict[str, str] = field(default_factory=dict)
    reported_recursive_chains: set[tuple[str, ...]] = field(default_factory=set)


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


def _substitute_module_variables(
    context: ModuleAtomizationContext,
    value: str,
    *,
    param_name: str,
    param_span: Optional[SourceSpan],
) -> Optional[str]:
    """Substitute module variable placeholders in an instance parameter value.

    Args:
        context: Shared module atomization context.
        value: Raw instance parameter expression value.
        param_name: Instance parameter name for diagnostics.
        param_span: Optional source span for the parameter expression.

    Returns:
        Substituted parameter value, or None when diagnostics were emitted.
    """
    module_vars = context.module.variables or {}
    if "{" not in value:
        return value

    module_span = _entity_span(context.source_spans, context.module.module_id)
    had_error = False

    class _SubstitutionError(Exception):
        """Sentinel exception to abort regex substitution on diagnostics."""

    def resolve_variable(name: str, chain: tuple[str, ...]) -> str:
        nonlocal had_error
        cached = context.resolved_module_variables.get(name)
        if cached is not None:
            return cached

        if name in chain:
            cycle = chain + (name,)
            if cycle not in context.reported_recursive_chains:
                context.reported_recursive_chains.add(cycle)
                context.diagnostics.append(
                    _diagnostic(
                        RECURSIVE_MODULE_VARIABLE,
                        (
                            "Recursive module variable substitution in module "
                            f"'{context.module.name}': {' -> '.join(cycle)}."
                        ),
                        module_span or param_span,
                    )
                )
            had_error = True
            raise _SubstitutionError

        raw_value = module_vars.get(name)
        if raw_value is None:
            context.diagnostics.append(
                _diagnostic(
                    UNDEFINED_MODULE_VARIABLE,
                    (
                        f"Instance param '{param_name}' in module "
                        f"'{context.module.name}' references undefined module "
                        f"variable '{name}'."
                    ),
                    param_span or module_span,
                )
            )
            had_error = True
            raise _SubstitutionError

        raw_text = str(raw_value)
        try:
            resolved = _VAR_PLACEHOLDER_RE.sub(
                lambda match: resolve_variable(match.group(1), chain + (name,)),
                raw_text,
            )
        except _SubstitutionError as exc:
            raise exc

        context.resolved_module_variables[name] = resolved
        return resolved

    try:
        substituted = _VAR_PLACEHOLDER_RE.sub(
            lambda match: resolve_variable(match.group(1), ()),
            value,
        )
    except _SubstitutionError:
        return None

    return None if had_error else substituted
