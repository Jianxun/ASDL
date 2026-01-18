"""Instance lowering helpers for AST to GraphIR conversion."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from xdsl.dialects.builtin import DictionaryAttr

from asdl.ast import ModuleDecl
from asdl.ast.location import Locatable
from asdl.diagnostics import Diagnostic, format_code
from asdl.imports import NameEnv, ProgramDB
from asdl.ir.converters.ast_to_graphir_context import GraphIrDocumentContext
from asdl.ir.converters.ast_to_graphir_parsing import parse_instance_expr
from asdl.ir.converters.ast_to_graphir_symbols import ResolvedSymbol
from asdl.ir.converters.ast_to_graphir_utils import (
    diagnostic,
    maybe_src_annotations,
    to_string_dict_attr,
)
from asdl.ir.graphir import InstanceOp
from asdl.ir.patterns import (
    AtomizedEndpoint,
    AtomizedPattern,
    PatternExpressionTable,
    atomize_pattern,
    register_pattern_expression,
)
from asdl.ir.patterns.origin import PatternOrigin, encode_pattern_origin

INVALID_INSTANCE_EXPR = format_code("IR", 1)
INVALID_ENDPOINT_EXPR = format_code("IR", 2)
PATTERN_LENGTH_MISMATCH = format_code("IR", 3)
PATTERN_COLLISION = format_code("IR", 4)
UNRESOLVED_QUALIFIED = format_code("IR", 10)
UNRESOLVED_UNQUALIFIED = format_code("IR", 11)
UNDEFINED_MODULE_VARIABLE = format_code("IR", 12)
RECURSIVE_MODULE_VARIABLE = format_code("IR", 13)


_PATTERN_DELIMITERS = set("<>;|")
_VARIABLE_PLACEHOLDER_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


def is_pattern_expression(expression: str) -> bool:
    """Check whether a token includes pattern delimiter characters.

    Args:
        expression: Token to inspect.

    Returns:
        True if any pattern delimiter characters are present.
    """
    return any(char in _PATTERN_DELIMITERS for char in expression)


def register_pattern_entry(
    table: PatternExpressionTable,
    cache: Dict[Tuple[str, str], str],
    *,
    expression: str,
    kind: str,
    loc: Optional[Locatable],
) -> str:
    """Register a pattern expression entry, caching by kind/expression.

    Args:
        table: Pattern expression table to populate.
        cache: Cache of (kind, expression) to expression IDs.
        expression: Pattern expression string.
        kind: Pattern expression kind string.
        loc: Optional source location for span metadata.

    Returns:
        Assigned expression ID for the entry.
    """
    cache_key = (kind, expression)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    span = loc.to_source_span() if loc is not None else None
    expr_id = register_pattern_expression(
        table,
        expression=expression,
        kind=kind,
        span=span,
    )
    cache[cache_key] = expr_id
    return expr_id


def pattern_origin_from_atom(
    expression_id: str,
    atom: AtomizedPattern | AtomizedEndpoint,
):
    """Build a GraphIR pattern origin attribute from an atomized pattern.

    Args:
        expression_id: Expression table ID for the originating expression.
        atom: Atomized pattern metadata.

    Returns:
        Encoded GraphIR pattern origin attribute.
    """
    return encode_pattern_origin(
        PatternOrigin(
            expression_id=expression_id,
            segment_index=atom.segment_index,
            base_name=atom.base_name,
            pattern_parts=atom.pattern_parts,
        )
    )


def _format_param_value(value: object) -> str:
    """Format parameter values as strings.

    Args:
        value: Parameter value to format.

    Returns:
        Serialized string representation.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


class _ModuleVariableResolver:
    """Resolve module variable placeholders for instance parameter values.

    Args:
        module_name: Name of the module providing variables.
        variables: Module variable mapping.
        diagnostics: Diagnostic collection to append errors to.
        module_loc: Optional source location for module-level diagnostics.
    """

    def __init__(
        self,
        *,
        module_name: str,
        variables: Optional[Dict[str, object]],
        diagnostics: List[Diagnostic],
        module_loc: Optional[Locatable],
    ) -> None:
        self._module_name = module_name
        self._variables = variables or {}
        self._diagnostics = diagnostics
        self._module_loc = module_loc
        self._resolved: Dict[str, str] = {}
        self._resolving: set[str] = set()
        self._failed: set[str] = set()
        self.had_error = False

    def substitute(self, value: str, loc: Optional[Locatable]) -> Optional[str]:
        """Substitute `{var}` placeholders in a string.

        Args:
            value: Raw parameter value string.
            loc: Optional source location to use for diagnostics.

        Returns:
            Substituted string or None when resolution fails.
        """
        if "{" not in value:
            return value
        return self._substitute(value, loc)

    def _substitute(self, value: str, loc: Optional[Locatable]) -> Optional[str]:
        """Substitute placeholders using module variable resolution.

        Args:
            value: Raw string that may include `{var}` placeholders.
            loc: Optional source location for diagnostic attribution.

        Returns:
            Substituted string or None when substitution fails.
        """
        matches = list(_VARIABLE_PLACEHOLDER_RE.finditer(value))
        if not matches:
            return value
        parts: List[str] = []
        last_end = 0
        had_error = False
        for match in matches:
            parts.append(value[last_end:match.start()])
            var_name = match.group(1)
            resolved = self._resolve_variable(var_name, loc)
            if resolved is None:
                parts.append(match.group(0))
                had_error = True
            else:
                parts.append(resolved)
            last_end = match.end()
        parts.append(value[last_end:])
        if had_error:
            return None
        return "".join(parts)

    def _resolve_variable(self, name: str, loc: Optional[Locatable]) -> Optional[str]:
        """Resolve a module variable by name.

        Args:
            name: Variable name to resolve.
            loc: Optional source location to use for undefined variable diagnostics.

        Returns:
            Resolved string value or None when resolution fails.
        """
        if name in self._resolved:
            return self._resolved[name]
        if name in self._failed:
            return None
        if name in self._resolving:
            self._emit_recursive_variable(name)
            self._failed.add(name)
            self.had_error = True
            return None
        if name not in self._variables:
            self._emit_undefined_variable(name, loc)
            self._failed.add(name)
            self.had_error = True
            return None

        self._resolving.add(name)
        raw_value = self._variables[name]
        if isinstance(raw_value, str):
            resolved = self._substitute(raw_value, self._module_loc or loc)
            if resolved is None:
                self._failed.add(name)
                self._resolving.remove(name)
                self.had_error = True
                return None
        else:
            resolved = _format_param_value(raw_value)
        self._resolving.remove(name)
        self._resolved[name] = resolved
        return resolved

    def _emit_undefined_variable(self, name: str, loc: Optional[Locatable]) -> None:
        """Emit a diagnostic for an undefined module variable reference.

        Args:
            name: Variable name that was not defined.
            loc: Optional source location for the diagnostic.
        """
        diag_loc = loc or self._module_loc
        self._diagnostics.append(
            diagnostic(
                UNDEFINED_MODULE_VARIABLE,
                f"Undefined module variable '{name}' in module '{self._module_name}'.",
                diag_loc,
            )
        )

    def _emit_recursive_variable(self, name: str) -> None:
        """Emit a diagnostic for recursive module variable references.

        Args:
            name: Variable name participating in a recursion.
        """
        self._diagnostics.append(
            diagnostic(
                RECURSIVE_MODULE_VARIABLE,
                (
                    f"Recursive module variable '{name}' detected in module "
                    f"'{self._module_name}'."
                ),
                self._module_loc,
            )
        )


def resolve_symbol_reference(
    ref: str,
    symbol_table: Dict[str, List[ResolvedSymbol]],
    diagnostics: List[Diagnostic],
    loc: Optional[Locatable],
    *,
    name_env: Optional[NameEnv] = None,
    program_db: Optional[ProgramDB] = None,
    global_symbols: Optional[Dict[Path, Dict[str, List[ResolvedSymbol]]]] = None,
) -> Optional[ResolvedSymbol]:
    """Resolve an instance reference to a symbol.

    Args:
        ref: Instance reference token.
        symbol_table: Mapping of local symbols.
        diagnostics: Diagnostic collection to append errors to.
        loc: Optional source location.
        name_env: Optional name environment for import resolution.
        program_db: Optional program database for qualified symbol resolution.
        global_symbols: Optional symbol tables keyed by file ID.

    Returns:
        Resolved symbol metadata or None if unresolved.
    """
    if "." in ref:
        if name_env is None or program_db is None or global_symbols is None:
            diagnostics.append(
                diagnostic(
                    UNRESOLVED_QUALIFIED,
                    f"Unresolved symbol '{ref}'.",
                    loc,
                )
            )
            return None
        namespace, symbol = ref.split(".", 1)
        if not namespace or not symbol:
            diagnostics.append(
                diagnostic(
                    UNRESOLVED_QUALIFIED,
                    f"Unresolved symbol '{ref}'.",
                    loc,
                )
            )
            return None
        resolved_file_id = name_env.resolve(namespace)
        if resolved_file_id is None:
            diagnostics.append(
                diagnostic(
                    UNRESOLVED_QUALIFIED,
                    f"Unresolved symbol '{ref}'.",
                    loc,
                )
            )
            return None
        if program_db.lookup(resolved_file_id, symbol) is None:
            diagnostics.append(
                diagnostic(
                    UNRESOLVED_QUALIFIED,
                    f"Unresolved symbol '{ref}'.",
                    loc,
                )
            )
            return None
        candidates = global_symbols.get(resolved_file_id, {}).get(symbol)
        if not candidates:
            diagnostics.append(
                diagnostic(
                    UNRESOLVED_QUALIFIED,
                    f"Unresolved symbol '{ref}'.",
                    loc,
                )
            )
            return None
        if len(candidates) > 1:
            diagnostics.append(
                diagnostic(
                    UNRESOLVED_QUALIFIED,
                    f"Ambiguous symbol '{ref}' refers to multiple definitions.",
                    loc,
                )
            )
            return None
        return candidates[0]
    candidates = symbol_table.get(ref)
    if not candidates:
        diagnostics.append(
            diagnostic(
                UNRESOLVED_UNQUALIFIED,
                f"Unresolved symbol '{ref}'.",
                loc,
            )
        )
        return None
    if len(candidates) > 1:
        diagnostics.append(
            diagnostic(
                UNRESOLVED_UNQUALIFIED,
                f"Ambiguous symbol '{ref}' refers to multiple definitions.",
                loc,
            )
        )
        return None
    return candidates[0]


def lower_module_instances(
    name: str,
    module: ModuleDecl,
    *,
    context: GraphIrDocumentContext,
    pattern_table: PatternExpressionTable,
    pattern_cache: Dict[Tuple[str, str], str],
    diagnostics: List[Diagnostic],
) -> Tuple[List[InstanceOp], Dict[str, str], Dict[str, List[str]], bool]:
    """Lower module instances into GraphIR ops.

    Args:
        name: Module name.
        module: Module declaration.
        context: Per-document conversion context.
        pattern_table: Pattern expression table to populate.
        pattern_cache: Cache of pattern expressions to IDs.
        diagnostics: Diagnostic collection to append errors to.

    Returns:
        Instance ops, instance name-to-id mapping, instance ref mapping, and error flag.
    """
    inst_ops: List[InstanceOp] = []
    inst_name_to_id: Dict[str, str] = {}
    inst_names_by_ref: Dict[str, List[str]] = {}
    if not module.instances:
        return inst_ops, inst_name_to_id, inst_names_by_ref, False

    had_error = False
    variable_resolver = _ModuleVariableResolver(
        module_name=name,
        variables=module.variables,
        diagnostics=diagnostics,
        module_loc=module._loc,
    )

    for inst_name, expr in module.instances.items():
        inst_loc = module._instances_loc.get(inst_name)
        inst_expr_loc = module._instance_expr_loc.get(inst_name)
        ref, params, parse_error = parse_instance_expr(expr)
        if parse_error is not None:
            diagnostics.append(
                diagnostic(
                    INVALID_INSTANCE_EXPR,
                    f"{parse_error} in module '{name}'",
                    inst_loc or module._loc,
                )
            )
            had_error = True
            continue
        if ref is None:
            diagnostics.append(
                diagnostic(
                    INVALID_INSTANCE_EXPR,
                    f"Instance expression missing reference in module '{name}'",
                    inst_loc or module._loc,
                )
            )
            had_error = True
            continue
        resolved = resolve_symbol_reference(
            ref,
            context.symbol_table,
            diagnostics,
            inst_loc or module._loc,
            name_env=context.name_env,
            program_db=context.program_db,
            global_symbols=context.global_symbols,
        )
        if resolved is None:
            had_error = True
            continue
        inst_atoms, atom_diags = atomize_pattern(inst_name)
        if inst_atoms is None:
            diagnostics.extend(atom_diags)
            had_error = True
            continue
        inst_is_pattern = is_pattern_expression(inst_name)
        inst_expr_id = None
        if inst_is_pattern:
            inst_expr_id = register_pattern_entry(
                pattern_table,
                pattern_cache,
                expression=inst_name,
                kind="inst",
                loc=inst_loc or module._loc,
            )


        inst_count = len(inst_atoms)
        param_values_by_inst = [dict() for _ in range(inst_count)]
        param_origins_by_inst: List[Dict[str, object]] = [
            dict() for _ in range(inst_count)
        ]
        param_error = False
        if params:
            for param_name, param_expr in params.items():
                param_loc = inst_expr_loc or inst_loc or module._loc
                resolved_expr = variable_resolver.substitute(param_expr, param_loc)
                if resolved_expr is None:
                    param_error = True
                    break
                param_is_pattern = is_pattern_expression(resolved_expr)
                if param_is_pattern:
                    param_atoms, param_diags = atomize_pattern(resolved_expr)
                    if param_atoms is None:
                        diagnostics.extend(param_diags)
                        param_error = True
                        break
                    param_count = len(param_atoms)
                    param_expr_id = register_pattern_entry(
                        pattern_table,
                        pattern_cache,
                        expression=resolved_expr,
                        kind="param",
                        loc=param_loc,
                    )
                else:
                    param_atoms = [resolved_expr]
                    param_count = 1
                    param_expr_id = None

                if param_count not in (1, inst_count):
                    diagnostics.append(
                        diagnostic(
                            PATTERN_LENGTH_MISMATCH,
                            (
                                f"Instance param '{param_name}' expands to {param_count} "
                                f"atoms but instance '{inst_name}' expands to {inst_count} "
                                f"atoms in module '{name}'"
                            ),
                            inst_loc or module._loc,
                        )
                    )
                    param_error = True
                    break

                for index in range(inst_count):
                    if param_is_pattern:
                        param_atom = (
                            param_atoms[0] if param_count == 1 else param_atoms[index]
                        )
                        param_values_by_inst[index][param_name] = param_atom.literal
                        param_origins_by_inst[index][param_name] = (
                            pattern_origin_from_atom(param_expr_id, param_atom)
                        )
                    else:
                        param_values_by_inst[index][param_name] = resolved_expr

        if param_error:
            had_error = True
            continue

        inst_names_by_ref.setdefault(ref, []).append(inst_name)

        for index, inst_atom in enumerate(inst_atoms):
            inst_literal = inst_atom.literal
            if inst_literal in inst_name_to_id:
                diagnostics.append(
                    diagnostic(
                        PATTERN_COLLISION,
                        (
                            f"Instance pattern expansion collides on '{inst_literal}' "
                            f"in module '{name}'"
                        ),
                        inst_loc or module._loc,
                    )
                )
                had_error = True
                continue
            inst_id = context.id_allocator.next("i")
            inst_name_to_id[inst_literal] = inst_id
            props = to_string_dict_attr(param_values_by_inst[index])
            param_pattern_origin = None
            if param_origins_by_inst[index]:
                param_pattern_origin = DictionaryAttr(param_origins_by_inst[index])
            inst_pattern_origin = None
            if inst_expr_id is not None:
                inst_pattern_origin = pattern_origin_from_atom(inst_expr_id, inst_atom)
            inst_ops.append(
                InstanceOp(
                    inst_id=inst_id,
                    name=inst_literal,
                    module_ref=(resolved.kind, resolved.sym_id),
                    module_ref_raw=ref,
                    pattern_origin=inst_pattern_origin,
                    props=props,
                    param_pattern_origin=param_pattern_origin,
                    annotations=maybe_src_annotations(inst_loc),
                )
            )

    return inst_ops, inst_name_to_id, inst_names_by_ref, had_error


__all__ = [
    "INVALID_ENDPOINT_EXPR",
    "INVALID_INSTANCE_EXPR",
    "PATTERN_COLLISION",
    "PATTERN_LENGTH_MISMATCH",
    "RECURSIVE_MODULE_VARIABLE",
    "UNDEFINED_MODULE_VARIABLE",
    "UNRESOLVED_QUALIFIED",
    "UNRESOLVED_UNQUALIFIED",
    "is_pattern_expression",
    "lower_module_instances",
    "pattern_origin_from_atom",
    "register_pattern_entry",
    "resolve_symbol_reference",
]
