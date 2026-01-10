from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple

from xdsl.dialects.builtin import DictionaryAttr, FileLineColLoc, IntAttr, LocationAttr, StringAttr

from asdl.ast import AsdlDocument, DeviceBackendDecl, DeviceDecl, ModuleDecl
from asdl.ast.location import Locatable
from asdl.diagnostics import Diagnostic, Severity, format_code
from asdl.imports import NameEnv, ProgramDB
from asdl.ir.nfir import (
    BackendOp,
    DesignOp,
    DeviceOp,
    EndpointAttr,
    InstanceOp,
    ModuleOp,
    NetOp,
)

INVALID_INSTANCE_EXPR = format_code("IR", 1)
INVALID_ENDPOINT_EXPR = format_code("IR", 2)
UNRESOLVED_QUALIFIED = format_code("IR", 10)
UNRESOLVED_UNQUALIFIED = format_code("IR", 11)
INVALID_PATTERN_DEF = format_code("IR", 12)
UNDEFINED_NAMED_PATTERN = format_code("IR", 13)
UNUSED_IMPORT = format_code("LINT", 1)
DEFAULT_OVERRIDE = format_code("LINT", 2)
NO_SPAN_NOTE = "No source span available."
NAMED_PATTERN_REF = re.compile(r"<@([^>]+)>")


def convert_document(
    document: AsdlDocument,
    *,
    name_env: Optional[NameEnv] = None,
    program_db: Optional[ProgramDB] = None,
) -> Tuple[Optional[DesignOp], List[Diagnostic]]:
    diagnostics: List[Diagnostic] = []
    had_error = False
    modules: List[ModuleOp] = []
    devices: List[DeviceOp] = []
    used_namespaces: Set[str] = set()
    local_symbols = _collect_local_symbols(document, name_env, program_db)
    entry_file_id = str(name_env.file_id) if name_env is not None else None

    if document.modules:
        for name, module in document.modules.items():
            module_op, module_diags, module_error = _convert_module(
                name,
                module,
                file_id=entry_file_id,
                local_symbols=local_symbols,
                used_namespaces=used_namespaces,
                name_env=name_env,
                program_db=program_db,
            )
            diagnostics.extend(module_diags)
            had_error = had_error or module_error
            modules.append(module_op)

    if document.devices:
        for name, device in document.devices.items():
            devices.append(_convert_device(name, device, file_id=entry_file_id))

    if name_env is not None:
        diagnostics.extend(_unused_import_diagnostics(name_env, used_namespaces))

    design = DesignOp(
        region=modules + devices,
        top=document.top,
        entry_file_id=entry_file_id,
    )
    if had_error:
        return None, diagnostics
    return design, diagnostics


def _convert_module(
    name: str,
    module: ModuleDecl,
    *,
    file_id: str | None,
    local_symbols: Set[str],
    used_namespaces: Set[str],
    name_env: Optional[NameEnv],
    program_db: Optional[ProgramDB],
) -> Tuple[ModuleOp, List[Diagnostic], bool]:
    diagnostics: List[Diagnostic] = []
    had_error = False
    instances: List[InstanceOp] = []
    nets_by_name: Dict[str, List[EndpointAttr]] = {}
    net_order: List[str] = []
    net_locs: Dict[str, Locatable] = {}
    port_order: List[str] = []
    explicit_endpoints: Dict[Tuple[str, str], Tuple[str, bool, Optional[Locatable]]] = {}
    instance_refs: Dict[str, str] = {}
    local_file_id = name_env.file_id if name_env is not None else None
    patterns, invalid_patterns, patterns_error = _collect_named_patterns(module, diagnostics)
    had_error = had_error or patterns_error

    def substitute_token(token: str, loc: Optional[Locatable]) -> str:
        nonlocal had_error
        updated, token_error = _substitute_named_patterns(
            token, patterns, invalid_patterns, diagnostics, loc
        )
        had_error = had_error or token_error
        return updated

    if module.nets:
        for net_name, endpoint_expr in module.nets.items():
            net_loc = module._nets_loc.get(net_name)
            net_name = substitute_token(net_name, net_loc or module._loc)
            is_port = net_name.startswith("$")
            if is_port:
                stripped_name = net_name[1:]
                if stripped_name not in port_order:
                    port_order.append(stripped_name)
                net_name = stripped_name
            substituted_expr = endpoint_expr
            if isinstance(endpoint_expr, list):
                updated_tokens: List[str] = []
                for token in endpoint_expr:
                    prefix = "!" if isinstance(token, str) and token.startswith("!") else ""
                    body = token[1:] if prefix else token
                    if isinstance(body, str):
                        body = substitute_token(body, net_loc or module._loc)
                    updated_tokens.append(f"{prefix}{body}")
                substituted_expr = updated_tokens
            endpoints, suppressed_endpoints, endpoint_error = _parse_endpoints(substituted_expr)
            if endpoint_error is not None:
                diagnostics.append(
                    _diagnostic(
                        INVALID_ENDPOINT_EXPR,
                        f"{endpoint_error} in module '{name}'",
                        net_loc or module._loc,
                    )
                )
                had_error = True
                continue
            if net_name not in nets_by_name:
                nets_by_name[net_name] = []
                net_order.append(net_name)
                if net_loc is not None:
                    net_locs[net_name] = net_loc
            for endpoint in endpoints:
                nets_by_name[net_name].append(endpoint)
                key = (endpoint.inst.data, endpoint.pin.data)
                suppressed = key in suppressed_endpoints
                if key not in explicit_endpoints:
                    explicit_endpoints[key] = (net_name, suppressed, net_loc)
                else:
                    existing_net, existing_suppressed, existing_loc = explicit_endpoints[key]
                    if existing_suppressed and not suppressed:
                        explicit_endpoints[key] = (existing_net, False, existing_loc)

    if module.instances:
        for inst_name, expr in module.instances.items():
            inst_loc = module._instances_loc.get(inst_name)
            inst_name = substitute_token(inst_name, inst_loc or module._loc)
            ref, params, instance_error = _parse_instance_expr(expr)
            if instance_error is not None:
                diagnostics.append(
                    _diagnostic(
                        INVALID_INSTANCE_EXPR,
                        f"{instance_error} in module '{name}'",
                        inst_loc or module._loc,
                    )
                )
                had_error = True
                continue
            for key, value in list(params.items()):
                params[key] = substitute_token(value, inst_loc or module._loc)
            raw_ref = ref
            ref_file_id = None
            resolved_qualified = False
            if ref is not None and "." in ref:
                namespace, symbol = ref.split(".", 1)
                if namespace and name_env is not None and namespace in name_env.bindings:
                    used_namespaces.add(namespace)
                if name_env is None or program_db is None:
                    diagnostics.append(
                        _diagnostic(
                            UNRESOLVED_QUALIFIED,
                            f"Unresolved symbol '{ref}' in module '{name}'",
                            inst_loc or module._loc,
                        )
                    )
                    had_error = True
                    continue
                if not namespace or not symbol:
                    diagnostics.append(
                        _diagnostic(
                            UNRESOLVED_QUALIFIED,
                            f"Unresolved symbol '{ref}' in module '{name}'",
                            inst_loc or module._loc,
                        )
                    )
                    had_error = True
                    continue
                resolved_file_id = name_env.resolve(namespace)
                symbol_def = (
                    program_db.lookup(resolved_file_id, symbol)
                    if resolved_file_id is not None
                    else None
                )
                if resolved_file_id is None or symbol_def is None:
                    diagnostics.append(
                        _diagnostic(
                            UNRESOLVED_QUALIFIED,
                            f"Unresolved symbol '{ref}' in module '{name}'",
                            inst_loc or module._loc,
                        )
                    )
                    had_error = True
                    continue
                ref = symbol
                ref_file_id = resolved_file_id
                resolved_qualified = True
            if ref is not None and not resolved_qualified and "." not in ref and ref not in local_symbols:
                diagnostics.append(
                    _diagnostic(
                        UNRESOLVED_UNQUALIFIED,
                        f"Unresolved symbol '{ref}' in module '{name}'",
                        inst_loc or module._loc,
                    )
                )
                had_error = True
                continue
            if ref is not None and not resolved_qualified and "." not in ref and local_file_id is not None:
                ref_file_id = local_file_id
            instances.append(
                InstanceOp(
                    name=inst_name,
                    ref=ref,
                    ref_file_id=str(ref_file_id) if ref_file_id is not None else None,
                    params=_to_string_dict_attr(params),
                    src=_loc_attr(inst_loc),
                )
            )
            if raw_ref is not None:
                instance_refs[inst_name] = raw_ref

    if module.instance_defaults and instance_refs:
        instances_by_ref: Dict[str, List[str]] = {}
        for inst_name, ref in instance_refs.items():
            instances_by_ref.setdefault(ref, []).append(inst_name)

        for ref, defaults in module.instance_defaults.items():
            inst_names = instances_by_ref.get(ref)
            if not inst_names:
                continue
            for port_name, net_token in defaults.bindings.items():
                net_token = substitute_token(net_token, module._loc)
                net_name, is_port = _split_net_token(net_token)
                if not is_port or net_name in port_order:
                    continue
                if any(
                    (inst_name, port_name) not in explicit_endpoints
                    for inst_name in inst_names
                ):
                    port_order.append(net_name)

        for ref, defaults in module.instance_defaults.items():
            inst_names = instances_by_ref.get(ref)
            if not inst_names:
                continue
            for inst_name in inst_names:
                for port_name, net_token in defaults.bindings.items():
                    net_token = substitute_token(net_token, module._loc)
                    net_name, _is_port = _split_net_token(net_token)
                    key = (inst_name, port_name)
                    explicit = explicit_endpoints.get(key)
                    if explicit is not None:
                        explicit_net, suppressed, explicit_loc = explicit
                        if explicit_net != net_name and not suppressed:
                            diagnostics.append(
                                _diagnostic(
                                    DEFAULT_OVERRIDE,
                                    (
                                        "Default binding for"
                                        f" '{inst_name}.{port_name}' to '{net_name}'"
                                        f" overridden by explicit net '{explicit_net}'."
                                    ),
                                    explicit_loc or module._loc,
                                    severity=Severity.WARNING,
                                )
                            )
                        continue
                    if net_name not in nets_by_name:
                        nets_by_name[net_name] = []
                        net_order.append(net_name)
                    nets_by_name[net_name].append(
                        EndpointAttr(StringAttr(inst_name), StringAttr(port_name))
                    )

    nets: List[NetOp] = []
    for net_name in net_order:
        nets.append(
            NetOp(
                name=net_name,
                endpoints=nets_by_name.get(net_name, []),
                src=_loc_attr(net_locs.get(net_name)),
            )
        )

    ops: List[object] = []
    ops.extend(nets)
    ops.extend(instances)
    return (
        ModuleOp(
            name=name,
            port_order=port_order,
            region=ops,
            file_id=file_id,
            src=_loc_attr(module._loc),
        ),
        diagnostics,
        had_error,
    )


def _convert_device(name: str, device: DeviceDecl, *, file_id: str | None) -> DeviceOp:
    backends: List[BackendOp] = []
    for backend_name, backend in device.backends.items():
        backends.append(_convert_backend(backend_name, backend))

    ports = device.ports or []
    return DeviceOp(
        name=name,
        ports=ports,
        file_id=file_id,
        params=_to_string_dict_attr(device.params),
        region=backends,
        src=_loc_attr(device._loc),
    )


def _convert_backend(name: str, backend: DeviceBackendDecl) -> BackendOp:
    props = backend.model_extra or None
    return BackendOp(
        name=name,
        template=backend.template,
        params=_to_string_dict_attr(backend.params),
        props=_to_string_dict_attr(props),
        src=_loc_attr(backend._loc),
    )


def _collect_named_patterns(
    module: ModuleDecl,
    diagnostics: List[Diagnostic],
) -> Tuple[Dict[str, str], Set[str], bool]:
    patterns: Dict[str, str] = {}
    invalid: Set[str] = set()
    had_error = False
    for name, value in (module.patterns or {}).items():
        if not isinstance(value, str):
            diagnostics.append(
                _diagnostic(
                    INVALID_PATTERN_DEF,
                    f"Named pattern '{name}' must be a string group token like <...> or [...].",
                    module._loc,
                )
            )
            invalid.add(name)
            had_error = True
            continue
        if value.startswith("<@") and value.endswith(">"):
            diagnostics.append(
                _diagnostic(
                    INVALID_PATTERN_DEF,
                    (
                        f"Named pattern '{name}' must not reference other named patterns;"
                        " expected a group token like <...> or [...]."
                    ),
                    module._loc,
                )
            )
            invalid.add(name)
            had_error = True
            continue
        if not _is_group_token(value):
            diagnostics.append(
                _diagnostic(
                    INVALID_PATTERN_DEF,
                    f"Named pattern '{name}' must be a single group token like <...> or [...].",
                    module._loc,
                )
            )
            invalid.add(name)
            had_error = True
            continue
        patterns[name] = value
    return patterns, invalid, had_error


def _substitute_named_patterns(
    token: str,
    patterns: Dict[str, str],
    invalid_patterns: Set[str],
    diagnostics: List[Diagnostic],
    loc: Optional[Locatable],
) -> Tuple[str, bool]:
    if "<@" not in token:
        return token, False
    had_error = False

    def replace(match: re.Match[str]) -> str:
        nonlocal had_error
        name = match.group(1)
        if name in invalid_patterns:
            had_error = True
            return match.group(0)
        replacement = patterns.get(name)
        if replacement is None:
            diagnostics.append(
                _diagnostic(
                    UNDEFINED_NAMED_PATTERN,
                    f"Undefined named pattern '<@{name}>' in '{token}'.",
                    loc,
                )
            )
            had_error = True
            return match.group(0)
        return replacement

    return NAMED_PATTERN_REF.sub(replace, token), had_error


def _is_group_token(value: str) -> bool:
    if value.startswith("<") and value.endswith(">"):
        return _is_valid_group_content(value[1:-1])
    if value.startswith("[") and value.endswith("]"):
        return _is_valid_group_content(value[1:-1])
    return False


def _is_valid_group_content(content: str) -> bool:
    if not content:
        return False
    if any(char.isspace() for char in content):
        return False
    return not any(char in "<>[];" for char in content)


def _parse_instance_expr(expr: str) -> Tuple[Optional[str], Dict[str, str], Optional[str]]:
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


def _parse_endpoints(
    expr: List[str],
) -> Tuple[List[EndpointAttr], Set[Tuple[str, str]], Optional[str]]:
    endpoints: List[EndpointAttr] = []
    suppressed: Set[Tuple[str, str]] = set()
    if isinstance(expr, str):
        return [], suppressed, "Endpoint lists must be YAML lists of '<instance>.<pin>' strings"
    for token in expr:
        raw_token = token
        suppress_override = False
        if token.startswith("!"):
            suppress_override = True
            token = token[1:]
        if token.count(".") != 1:
            return [], suppressed, f"Invalid endpoint token '{raw_token}'; expected inst.pin"
        inst, pin = token.split(".", 1)
        if not inst or not pin:
            return [], suppressed, f"Invalid endpoint token '{raw_token}'; expected inst.pin"
        endpoints.append(EndpointAttr(StringAttr(inst), StringAttr(pin)))
        if suppress_override:
            suppressed.add((inst, pin))
    return endpoints, suppressed, None


def _split_net_token(net_token: str) -> Tuple[str, bool]:
    if net_token.startswith("$"):
        return net_token[1:], True
    return net_token, False


def _to_string_dict_attr(
    values: Optional[Dict[str, object]],
) -> Optional[DictionaryAttr]:
    if not values:
        return None
    items = {key: StringAttr(_format_param_value(value)) for key, value in values.items()}
    return DictionaryAttr(items)


def _format_param_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _loc_attr(loc: Optional[Locatable]) -> Optional[LocationAttr]:
    if loc is None or loc.start_line is None or loc.start_col is None:
        return None
    return FileLineColLoc(StringAttr(loc.file), IntAttr(loc.start_line), IntAttr(loc.start_col))


def _diagnostic(
    code: str,
    message: str,
    loc: Optional[Locatable],
    severity: Severity = Severity.ERROR,
) -> Diagnostic:
    span = loc.to_source_span() if loc is not None else None
    notes = None if span is not None else [NO_SPAN_NOTE]
    return Diagnostic(
        code=code,
        severity=severity,
        message=message,
        primary_span=span,
        notes=notes,
        source="ir",
    )


def _collect_local_symbols(
    document: AsdlDocument,
    name_env: Optional[NameEnv],
    program_db: Optional[ProgramDB],
) -> Set[str]:
    if name_env is not None and program_db is not None:
        return set(program_db.symbols.get(name_env.file_id, {}).keys())
    symbols: Set[str] = set()
    if document.modules:
        symbols.update(document.modules.keys())
    if document.devices:
        symbols.update(document.devices.keys())
    return symbols


def _unused_import_diagnostics(
    name_env: NameEnv, used_namespaces: Set[str]
) -> List[Diagnostic]:
    diagnostics: List[Diagnostic] = []
    unused = sorted(set(name_env.bindings.keys()) - used_namespaces)
    for namespace in unused:
        diagnostics.append(
            _diagnostic(
                UNUSED_IMPORT,
                f"Unused import namespace '{namespace}'.",
                None,
                severity=Severity.WARNING,
            )
        )
    return diagnostics


__all__ = ["convert_document"]
