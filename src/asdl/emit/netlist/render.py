from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Optional, Tuple

from asdl.diagnostics import Diagnostic, Severity
from asdl.diagnostics.collector import DiagnosticCollector
from asdl.emit.backend_config import BackendConfig
from asdl.ir.ifir import DeviceOp, InstanceOp, ModuleOp, NetOp
from asdl.ir.patterns.expr_table import (
    PatternExpressionTable,
    decode_pattern_expression_table,
)
from asdl.ir.patterns.origin import render_pattern_origin

from .diagnostics import (
    MALFORMED_TEMPLATE,
    MISSING_BACKEND,
    MISSING_TOP,
    MISSING_CONN,
    UNKNOWN_CONN_PORT,
    UNKNOWN_REFERENCE,
    UNRESOLVED_ENV_VAR,
    _diagnostic,
    _emit_diagnostic,
)
from .ir_utils import _collect_design_ops, _select_backend, _select_symbol
from .params import _dict_attr_to_strings, _merge_params, _merge_variables
from .templates import (
    _escape_braced_env_vars,
    _restore_braced_env_vars,
    _template_field_roots,
    _validate_template,
)


@dataclass(frozen=True)
class _SymbolMaps:
    modules_by_name: Dict[str, List[ModuleOp]]
    module_index: Dict[Tuple[str, Optional[str]], ModuleOp]
    module_emitted_names: Dict[Tuple[str, Optional[str]], str]
    devices_by_name: Dict[str, List[DeviceOp]]
    device_index: Dict[Tuple[str, Optional[str]], DeviceOp]


_ENV_VAR_PATTERN = re.compile(r"\$(\w+|\{[^}]+\})")

def _emit_design(
    design: "DesignOp", options: "EmitOptions"
) -> Tuple[Optional[str], List[Diagnostic]]:
    diagnostics: List[Diagnostic] = []
    modules_by_name, devices_by_name, module_ops = _collect_design_ops(design)
    module_index = _build_module_index(modules_by_name)
    device_index = _build_device_index(devices_by_name)
    module_emitted_names = _build_module_emitted_names(module_ops, modules_by_name)

    top_name = design.top.data if design.top is not None else None
    entry_file_id = _entry_file_id(design)
    top_module: Optional[ModuleOp] = None
    if top_name is None:
        if len(module_ops) == 1:
            top_module = module_ops[0]
            module_file_id = _module_file_id(top_module)
            if entry_file_id is not None and module_file_id != entry_file_id:
                diagnostics.append(
                    _diagnostic(
                        MISSING_TOP,
                        "Top module is required when entry file has no local modules",
                        Severity.ERROR,
                    )
                )
                return None, diagnostics
            top_name = top_module.sym_name.data
        else:
            diagnostics.append(
                _diagnostic(
                    MISSING_TOP,
                    "Top module is required when multiple modules exist",
                    Severity.ERROR,
                )
            )
            return None, diagnostics
    if top_name not in modules_by_name:
        diagnostics.append(
            _diagnostic(
                MISSING_TOP,
                f"Top module '{top_name}' is not defined",
                Severity.ERROR,
            )
        )
        return None, diagnostics
    if top_module is None:
        top_module = _select_symbol(
            modules_by_name, module_index, top_name, entry_file_id
        )
    if top_module is None:
        diagnostics.append(
            _diagnostic(
                MISSING_TOP,
                f"Top module '{top_name}' is not defined in entry file",
                Severity.ERROR,
            )
        )
        return None, diagnostics

    lines: List[str] = []
    had_error = False

    top_emitted_name = _module_emitted_name(top_module, module_emitted_names)
    emit_context = _emit_timestamp_context(options.emit_timestamp)
    header_context = {
        "backend": options.backend_name,
        "top": top_emitted_name,
        "top_sym_name": top_name,
        "file_id": _entry_file_id_value(entry_file_id, top_module),
    }
    header_context.update(emit_context)
    header, header_error = _render_system_device(
        "__netlist_header__",
        options.backend_config,
        header_context,
        diagnostics,
    )
    if header:
        lines.append(header)
    had_error = had_error or header_error

    symbol_maps = _SymbolMaps(
        modules_by_name=modules_by_name,
        module_index=module_index,
        module_emitted_names=module_emitted_names,
        devices_by_name=devices_by_name,
        device_index=device_index,
    )
    for module in module_ops:
        is_top = module is top_module
        module_lines, module_error = _emit_module(
            module,
            symbol_maps,
            is_top=is_top,
            options=options,
            diagnostics=diagnostics,
        )
        lines.extend(module_lines)
        had_error = had_error or module_error

    footer_context = {
        "backend": options.backend_name,
        "top": top_emitted_name,
        "top_sym_name": top_name,
        "file_id": _entry_file_id_value(entry_file_id, top_module),
    }
    footer_context.update(emit_context)
    footer, footer_error = _render_system_device(
        "__netlist_footer__",
        options.backend_config,
        footer_context,
        diagnostics,
    )
    if footer:
        lines.append(footer)
    had_error = had_error or footer_error

    if had_error:
        return None, diagnostics
    return "\n".join(lines), diagnostics


def _decode_pattern_table(module: ModuleOp) -> Optional[PatternExpressionTable]:
    """Decode the pattern expression table for a module, if available.

    Args:
        module: IFIR module to inspect.

    Returns:
        Decoded pattern expression table, or None if unavailable/invalid.
    """
    table_attr = module.pattern_expression_table
    if table_attr is None:
        return None
    try:
        return decode_pattern_expression_table(table_attr)
    except (TypeError, ValueError):
        return None


def _render_pattern_name(
    literal_name: str,
    origin: object,
    pattern_table: Optional[PatternExpressionTable],
    expected_kind: str,
    pattern_rendering: str,
) -> str:
    """Render a pattern-origin name when metadata is valid.

    Args:
        literal_name: Fallback literal name.
        origin: Pattern origin attribute or None.
        pattern_table: Decoded expression table for the module.
        expected_kind: Expected expression kind ("net" or "inst").
        pattern_rendering: Backend numeric formatting policy.

    Returns:
        Rendered name if metadata is valid, otherwise the literal name.
    """
    if origin is None or pattern_table is None:
        return literal_name
    expression_id = getattr(origin, "expression_id", None)
    if expression_id is None:
        return literal_name
    entry = pattern_table.get(expression_id.data)
    if entry is None or entry.kind != expected_kind:
        return literal_name
    try:
        return render_pattern_origin(origin, pattern_rendering=pattern_rendering)
    except (TypeError, ValueError):
        return literal_name


def _build_net_name_map(
    module: ModuleOp,
    pattern_table: Optional[PatternExpressionTable],
    pattern_rendering: str,
) -> Dict[str, str]:
    """Build a mapping of literal net names to rendered display names.

    Args:
        module: IFIR module containing net ops.
        pattern_table: Decoded pattern expression table.
        pattern_rendering: Backend numeric formatting policy.

    Returns:
        Mapping of literal net names to rendered display names.
    """
    name_map: Dict[str, str] = {}
    for op in module.body.block.ops:
        if not isinstance(op, NetOp):
            continue
        literal = op.name_attr.data
        name_map[literal] = _render_pattern_name(
            literal,
            op.pattern_origin,
            pattern_table,
            "net",
            pattern_rendering,
        )
    return name_map


def _emit_module(
    module: ModuleOp,
    symbols: _SymbolMaps,
    *,
    is_top: bool,
    options: "EmitOptions",
    diagnostics: List[Diagnostic],
) -> Tuple[List[str], bool]:
    lines: List[str] = []
    had_error = False

    pattern_table = _decode_pattern_table(module)
    pattern_rendering = options.backend_config.pattern_rendering
    net_name_map = _build_net_name_map(module, pattern_table, pattern_rendering)
    ports = [
        net_name_map.get(attr.data, attr.data) for attr in module.port_order.data
    ]

    module_name = _module_emitted_name(module, symbols.module_emitted_names)
    module_file_id = _module_file_id(module) or ""
    if not (is_top and not options.top_as_subckt):
        header_context = {
            "name": module_name,
            "sym_name": module.sym_name.data,
            "ports": " ".join(ports),
            "file_id": module_file_id,
        }
        header, header_error = _render_system_device(
            "__subckt_header__",
            options.backend_config,
            header_context,
            diagnostics,
        )
        if header:
            lines.append(header)
        had_error = had_error or header_error

    for op in module.body.block.ops:
        if not isinstance(op, InstanceOp):
            continue
        line, inst_error = _emit_instance(
            op,
            symbols,
            options=options,
            diagnostics=diagnostics,
            net_name_map=net_name_map,
            pattern_table=pattern_table,
        )
        if line is not None:
            lines.append(line)
        had_error = had_error or inst_error

    if not (is_top and not options.top_as_subckt):
        footer_context = {
            "name": module_name,
            "sym_name": module.sym_name.data,
            "file_id": module_file_id,
        }
        footer, footer_error = _render_system_device(
            "__subckt_footer__",
            options.backend_config,
            footer_context,
            diagnostics,
        )
        if footer:
            lines.append(footer)
        had_error = had_error or footer_error

    return lines, had_error


def _emit_instance(
    instance: InstanceOp,
    symbols: _SymbolMaps,
    *,
    options: "EmitOptions",
    diagnostics: List[Diagnostic],
    net_name_map: Optional[Mapping[str, str]] = None,
    pattern_table: Optional[PatternExpressionTable] = None,
) -> Tuple[Optional[str], bool]:
    instance_name = _render_pattern_name(
        instance.name_attr.data,
        instance.pattern_origin,
        pattern_table,
        "inst",
        options.backend_config.pattern_rendering,
    )
    ref_name = instance.ref.root_reference.data
    ref_file_id = _instance_ref_file_id(instance)
    module = _select_symbol(
        symbols.modules_by_name,
        symbols.module_index,
        ref_name,
        ref_file_id,
    )
    if module is not None:
        port_order = [attr.data for attr in module.port_order.data]
        conns, had_error = _ordered_conns(
            instance,
            port_order,
            diagnostics,
            net_name_map=net_name_map,
        )
        if had_error:
            return None, True

        ref_name = _module_emitted_name(module, symbols.module_emitted_names)
        call_context = {
            "name": instance_name,
            "ports": " ".join(conns),
            "ref": ref_name,
            "sym_name": module.sym_name.data,
            "file_id": _module_file_id(module) or "",
        }
        return _render_system_device(
            "__subckt_call__",
            options.backend_config,
            call_context,
            diagnostics,
        )

    device = _select_symbol(
        symbols.devices_by_name,
        symbols.device_index,
        ref_name,
        ref_file_id,
    )
    if device is None:
        diagnostics.append(
            _diagnostic(
                UNKNOWN_REFERENCE,
                (
                    f"Instance '{instance.name_attr.data}' references unknown symbol "
                    f"'{ref_name}'"
                ),
                Severity.ERROR,
                instance.src,
            )
        )
        return None, True

    backend = _select_backend(device, options.backend_name)
    if backend is None:
        diagnostics.append(
            _diagnostic(
                MISSING_BACKEND,
                f"Device '{ref_name}' has no backend '{options.backend_name}'",
                Severity.ERROR,
                device.src,
            )
        )
        return None, True

    port_order = [attr.data for attr in device.ports.data]
    conns, had_error = _ordered_conns(
        instance,
        port_order,
        diagnostics,
        net_name_map=net_name_map,
    )
    if had_error:
        return None, True
    ports_str = " ".join(conns)

    device_params = _dict_attr_to_strings(device.params)
    backend_params = _dict_attr_to_strings(backend.params)
    inst_params = _dict_attr_to_strings(instance.params)
    props = _dict_attr_to_strings(backend.props)
    merged_params, params_str, param_diags = _merge_params(
        device_params,
        backend_params,
        inst_params,
        instance_name=instance.name_attr.data,
        device_name=ref_name,
        loc=instance.src,
    )
    diagnostics.extend(param_diags)

    device_vars = _dict_attr_to_strings(device.variables)
    backend_vars = _dict_attr_to_strings(backend.variables)
    merged_vars, variable_diags = _merge_variables(
        device_vars,
        backend_vars,
        device_param_keys=device_params.keys(),
        backend_param_keys=backend_params.keys(),
        backend_prop_keys=props.keys(),
        instance_params=inst_params,
        instance_name=instance.name_attr.data,
        device_name=ref_name,
        device_loc=device.src,
        backend_loc=backend.src,
        instance_loc=instance.src,
    )
    diagnostics.extend(variable_diags)
    if any(
        diag.severity in (Severity.ERROR, Severity.FATAL) for diag in variable_diags
    ):
        return None, True

    template = backend.template.data
    escaped_template, env_vars = _escape_braced_env_vars(template)
    placeholders = _validate_template(template, ref_name, diagnostics, loc=backend.src)
    if placeholders is None:
        return None, True

    props.setdefault("params", params_str)
    template_values = {
        "name": instance_name,
        "ports": ports_str,
    }
    template_values.update(merged_params)
    template_values.update(merged_vars)
    template_values.update(props)
    try:
        rendered = escaped_template.format_map(template_values)
    except KeyError as exc:
        diagnostics.append(
            _diagnostic(
                UNKNOWN_REFERENCE,
                (
                    f"Backend template for '{ref_name}' references unknown placeholder "
                    f"'{exc.args[0]}'"
                ),
                Severity.ERROR,
                backend.src,
            )
        )
        return None, True
    except ValueError as exc:
        diagnostics.append(
            _diagnostic(
                MALFORMED_TEMPLATE,
                f"Backend template for '{ref_name}' is malformed: {exc}",
                Severity.ERROR,
                backend.src,
            )
        )
        return None, True

    rendered = _restore_braced_env_vars(rendered, env_vars)

    should_collapse = False
    if "ports" in placeholders and not ports_str:
        should_collapse = True
    if "params" in placeholders and not params_str:
        should_collapse = True
    if should_collapse:
        rendered = _collapse_whitespace(rendered)
    rendered, unresolved = _expand_env_vars(rendered)
    if unresolved is not None:
        unresolved_list = ", ".join(unresolved)
        diagnostics.append(
            _diagnostic(
                UNRESOLVED_ENV_VAR,
                (
                    f"Backend template for '{ref_name}' contains unresolved "
                    f"environment variables: {unresolved_list}"
                ),
                Severity.ERROR,
                backend.src,
            )
        )
        return None, True
    return rendered, False


def _entry_file_id(design: "DesignOp") -> Optional[str]:
    return design.entry_file_id.data if design.entry_file_id is not None else None


def _emit_timestamp_context(emit_timestamp) -> Dict[str, str]:
    return {
        "emit_date": emit_timestamp.strftime("%Y-%m-%d"),
        "emit_time": emit_timestamp.strftime("%H:%M:%S"),
    }


def _entry_file_id_value(entry_file_id: Optional[str], top_module: ModuleOp) -> str:
    if entry_file_id is not None:
        return entry_file_id
    module_file_id = _module_file_id(top_module)
    return module_file_id or ""


def _module_file_id(module: ModuleOp) -> Optional[str]:
    return module.file_id.data if module.file_id is not None else None


def _device_file_id(device: DeviceOp) -> Optional[str]:
    return device.file_id.data if device.file_id is not None else None


def _instance_ref_file_id(instance: InstanceOp) -> Optional[str]:
    return instance.ref_file_id.data if instance.ref_file_id is not None else None


def _module_key(module: ModuleOp) -> Tuple[str, Optional[str]]:
    return module.sym_name.data, _module_file_id(module)


def _device_key(device: DeviceOp) -> Tuple[str, Optional[str]]:
    return device.sym_name.data, _device_file_id(device)


def _build_module_index(
    modules_by_name: Dict[str, List[ModuleOp]],
) -> Dict[Tuple[str, Optional[str]], ModuleOp]:
    module_index: Dict[Tuple[str, Optional[str]], ModuleOp] = {}
    for modules in modules_by_name.values():
        for module in modules:
            module_index[_module_key(module)] = module
    return module_index


def _build_device_index(
    devices_by_name: Dict[str, List[DeviceOp]],
) -> Dict[Tuple[str, Optional[str]], DeviceOp]:
    device_index: Dict[Tuple[str, Optional[str]], DeviceOp] = {}
    for devices in devices_by_name.values():
        for device in devices:
            device_index[_device_key(device)] = device
    return device_index


def _hash_file_id(file_id: str) -> str:
    return hashlib.sha1(file_id.encode("utf-8")).hexdigest()[:8]


def _build_module_emitted_names(
    module_ops: List[ModuleOp],
    modules_by_name: Dict[str, List[ModuleOp]],
) -> Dict[Tuple[str, Optional[str]], str]:
    duplicate_names = {
        name for name, modules in modules_by_name.items() if len(modules) > 1
    }
    emitted_names: Dict[Tuple[str, Optional[str]], str] = {}
    for module in module_ops:
        name = module.sym_name.data
        file_id = _module_file_id(module)
        if name in duplicate_names and file_id is not None:
            emitted = f"{name}__{_hash_file_id(file_id)}"
        else:
            emitted = name
        emitted_names[_module_key(module)] = emitted
    return emitted_names


def _module_emitted_name(
    module: ModuleOp, emitted_names: Dict[Tuple[str, Optional[str]], str]
) -> str:
    return emitted_names.get(_module_key(module), module.sym_name.data)


def _ordered_conns(
    instance: InstanceOp,
    port_order: Iterable[str],
    diagnostics: DiagnosticCollector | List[Diagnostic],
    *,
    net_name_map: Optional[Mapping[str, str]] = None,
) -> Tuple[List[str], bool]:
    port_list = list(port_order)
    conn_map = {conn.port.data: conn.net.data for conn in instance.conns.data}
    had_error = False

    missing_ports = [port for port in port_list if port not in conn_map]
    if missing_ports:
        missing_str = ", ".join(missing_ports)
        _emit_diagnostic(
            diagnostics,
            _diagnostic(
                MISSING_CONN,
                (
                    f"Instance '{instance.name_attr.data}' is missing conns for ports: "
                    f"{missing_str}"
                ),
                Severity.ERROR,
                instance.src,
            ),
        )
        had_error = True

    port_set = set(port_list)
    unknown_ports = [port for port in conn_map if port not in port_set]
    if unknown_ports:
        unknown_str = ", ".join(unknown_ports)
        _emit_diagnostic(
            diagnostics,
            _diagnostic(
                UNKNOWN_CONN_PORT,
                (
                    f"Instance '{instance.name_attr.data}' has conns for unknown ports: "
                    f"{unknown_str}"
                ),
                Severity.ERROR,
                instance.src,
            ),
        )
        had_error = True

    if had_error:
        return [], True

    rendered = []
    for port in port_list:
        net_name = conn_map[port]
        if net_name_map is not None:
            net_name = net_name_map.get(net_name, net_name)
        rendered.append(net_name)
    return rendered, False


def _render_system_device(
    device_name: str,
    config: BackendConfig,
    context: Dict[str, str],
    diagnostics: List[Diagnostic],
) -> Tuple[Optional[str], bool]:
    if device_name not in config.templates:
        diagnostics.append(
            _diagnostic(
                MISSING_BACKEND,
                f"System device '{device_name}' not defined in backend config",
                Severity.ERROR,
            )
        )
        return None, True

    sys_device = config.templates[device_name]
    template = sys_device.template
    escaped_template, env_vars = _escape_braced_env_vars(template)

    try:
        placeholders = _template_field_roots(template)
    except ValueError as exc:
        diagnostics.append(
            _diagnostic(
                MALFORMED_TEMPLATE,
                f"System device '{device_name}' template is malformed: {exc}",
                Severity.ERROR,
            )
        )
        return None, True

    try:
        rendered = escaped_template.format_map(context)
    except KeyError as exc:
        diagnostics.append(
            _diagnostic(
                UNKNOWN_REFERENCE,
                (
                    f"System device '{device_name}' template references unknown "
                    f"placeholder '{exc.args[0]}'"
                ),
                Severity.ERROR,
            )
        )
        return None, True
    except ValueError as exc:
        diagnostics.append(
            _diagnostic(
                MALFORMED_TEMPLATE,
                f"System device '{device_name}' template is malformed: {exc}",
                Severity.ERROR,
            )
        )
        return None, True

    rendered = _restore_braced_env_vars(rendered, env_vars)

    should_collapse = False
    if "ports" in placeholders and context.get("ports", "") == "":
        should_collapse = True
    if should_collapse:
        rendered = _collapse_whitespace(rendered)

    rendered, unresolved = _expand_env_vars(rendered)
    if unresolved is not None:
        unresolved_list = ", ".join(unresolved)
        diagnostics.append(
            _diagnostic(
                UNRESOLVED_ENV_VAR,
                (
                    f"System device '{device_name}' template contains unresolved "
                    f"environment variables: {unresolved_list}"
                ),
                Severity.ERROR,
            )
        )
        return None, True

    return rendered, False


def _collapse_whitespace(rendered: str) -> str:
    return "\n".join(" ".join(line.split()) for line in rendered.splitlines())


def _expand_env_vars(rendered: str) -> Tuple[Optional[str], Optional[List[str]]]:
    expanded = os.path.expandvars(rendered)
    if _ENV_VAR_PATTERN.search(rendered) and _ENV_VAR_PATTERN.search(expanded):
        unresolved = sorted(
            {match.group(0) for match in _ENV_VAR_PATTERN.finditer(expanded)}
        )
        return None, unresolved
    return expanded, None
