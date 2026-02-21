"""Instance lowering for AST -> PatternedGraph."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Mapping, Optional, Set, Tuple

from asdl.ast import ModuleDecl
from asdl.ast.instance_expr import parse_inline_instance_expr
from asdl.ast.location import Locatable
from asdl.core.graph_builder import PatternedGraphBuilder
from asdl.core.registries import PatternExprKind
from asdl.diagnostics import Diagnostic
from asdl.imports import NameEnv, ProgramDB
from asdl.patterns_refactor.parser import NamedPattern

from .ast_to_patterned_graph_diagnostics import (
    INVALID_INSTANCE_EXPR,
    QUALIFIED_REFERENCE_ERROR,
    UNQUALIFIED_REFERENCE_ERROR,
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
    name_env: Optional[NameEnv] = None,
    program_db: Optional[ProgramDB] = None,
    module_ids_by_file: Optional[Mapping[Path, Mapping[str, str]]] = None,
    device_ids_by_file: Optional[Mapping[Path, Mapping[str, str]]] = None,
    expr_cache: Dict[tuple[PatternExprKind, str], str],
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
        name_env: Optional name environment for import namespaces.
        program_db: Optional program database for qualified references.
        module_ids_by_file: Optional per-file module ID mapping for imports.
        device_ids_by_file: Optional per-file device ID mapping for imports.
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
            kind="inst",
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
            name_env=name_env,
            program_db=program_db,
            module_ids_by_file=module_ids_by_file,
            device_ids_by_file=device_ids_by_file,
        )
        if resolved is None:
            continue

        instance_refs.add(ref)
        param_expr_ids: Dict[str, str] = {}
        if params:
            for param_name, param_expr in params.items():
                param_expr_id = _register_expression(
                    param_expr,
                    kind="param",
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
    ref, parsed_params, error = parse_inline_instance_expr(expr, strict_params=True)
    if error is not None:
        return None, {}, error
    params: Dict[str, str] = dict(parsed_params)
    return ref, params, None


def _resolve_reference(
    ref: str,
    *,
    module_ids: Mapping[str, str],
    device_ids: Mapping[str, str],
    module_name: str,
    loc: Optional[Locatable],
    diagnostics: List[Diagnostic],
    name_env: Optional[NameEnv] = None,
    program_db: Optional[ProgramDB] = None,
    module_ids_by_file: Optional[Mapping[Path, Mapping[str, str]]] = None,
    device_ids_by_file: Optional[Mapping[Path, Mapping[str, str]]] = None,
) -> Optional[Tuple[str, str]]:
    """Resolve instance references against module and device symbols.

    Args:
        ref: Reference token from the instance expression.
        module_ids: Mapping of module names to IDs.
        device_ids: Mapping of device names to IDs.
        module_name: Module name for diagnostics.
        loc: Source location for diagnostics.
        diagnostics: Diagnostic collection to append to.
        name_env: Optional name environment for qualified references.
        program_db: Optional program database for qualified references.
        module_ids_by_file: Optional per-file module ID map for qualified references.
        device_ids_by_file: Optional per-file device ID map for qualified references.

    Returns:
        Tuple of (ref_kind, ref_id) or None on failure.
    """
    if "." in ref:
        return _resolve_qualified_reference(
            ref,
            module_name=module_name,
            loc=loc,
            diagnostics=diagnostics,
            name_env=name_env,
            program_db=program_db,
            module_ids_by_file=module_ids_by_file,
            device_ids_by_file=device_ids_by_file,
        )
    module_id = module_ids.get(ref)
    device_id = device_ids.get(ref)
    if module_id and device_id:
        diagnostics.append(
            _diagnostic(
                UNQUALIFIED_REFERENCE_ERROR,
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
            UNQUALIFIED_REFERENCE_ERROR,
            f"Unresolved instance reference '{ref}' in module '{module_name}'",
            loc,
        )
    )
    return None


def _resolve_qualified_reference(
    ref: str,
    *,
    module_name: str,
    loc: Optional[Locatable],
    diagnostics: List[Diagnostic],
    name_env: Optional[NameEnv],
    program_db: Optional[ProgramDB],
    module_ids_by_file: Optional[Mapping[Path, Mapping[str, str]]],
    device_ids_by_file: Optional[Mapping[Path, Mapping[str, str]]],
) -> Optional[Tuple[str, str]]:
    """Resolve a qualified reference using import metadata.

    Args:
        ref: Qualified reference token from the instance expression.
        module_name: Module name for diagnostics.
        loc: Source location for diagnostics.
        diagnostics: Diagnostic collection to append to.
        name_env: Name environment for import namespaces.
        program_db: Program database for symbol lookup.
        module_ids_by_file: Per-file module ID mapping.
        device_ids_by_file: Per-file device ID mapping.

    Returns:
        Tuple of (ref_kind, ref_id) or None on failure.
    """
    if (
        name_env is None
        or program_db is None
        or module_ids_by_file is None
        or device_ids_by_file is None
    ):
        diagnostics.append(
            _diagnostic(
                QUALIFIED_REFERENCE_ERROR,
                (
                    f"Qualified reference '{ref}' requires imports in module "
                    f"'{module_name}'"
                ),
                loc,
            )
        )
        return None
    namespace, symbol = ref.split(".", 1)
    if not namespace or not symbol:
        diagnostics.append(
            _diagnostic(
                QUALIFIED_REFERENCE_ERROR,
                (
                    f"Qualified reference '{ref}' must be in 'ns.symbol' form in "
                    f"module '{module_name}'"
                ),
                loc,
            )
        )
        return None
    resolved_file = name_env.resolve(namespace)
    if resolved_file is None:
        diagnostics.append(
            _diagnostic(
                QUALIFIED_REFERENCE_ERROR,
                (
                    f"Unknown import namespace '{namespace}' for '{ref}' in module "
                    f"'{module_name}'"
                ),
                loc,
            )
        )
        return None
    symbol_def = program_db.lookup(resolved_file, symbol)
    if symbol_def is None:
        diagnostics.append(
            _diagnostic(
                QUALIFIED_REFERENCE_ERROR,
                f"Unresolved instance reference '{ref}' in module '{module_name}'",
                loc,
            )
        )
        return None
    if symbol_def.kind == "module":
        ref_id = module_ids_by_file.get(resolved_file, {}).get(symbol)
    else:
        ref_id = device_ids_by_file.get(resolved_file, {}).get(symbol)
    if ref_id is None:
        diagnostics.append(
            _diagnostic(
                QUALIFIED_REFERENCE_ERROR,
                f"Unresolved instance reference '{ref}' in module '{module_name}'",
                loc,
            )
        )
        return None
    return symbol_def.kind, ref_id
