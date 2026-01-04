from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Tuple

from asdl.diagnostics import Diagnostic, Severity
from asdl.diagnostics.collector import DiagnosticCollector
from asdl.emit.backend_config import BackendConfig
from asdl.ir.ifir import DeviceOp, InstanceOp, ModuleOp

from .diagnostics import (
    MALFORMED_TEMPLATE,
    MISSING_BACKEND,
    MISSING_TOP,
    MISSING_CONN,
    UNKNOWN_CONN_PORT,
    UNKNOWN_REFERENCE,
    _diagnostic,
    _emit_diagnostic,
)
from .ir_utils import _collect_design_ops, _select_backend
from .params import _dict_attr_to_strings, _merge_params
from .templates import _template_field_roots, _validate_template


def _emit_design(
    design: "DesignOp", options: "EmitOptions"
) -> Tuple[Optional[str], List[Diagnostic]]:
    diagnostics: List[Diagnostic] = []
    modules, devices, module_ops = _collect_design_ops(design)

    top_name = design.top.data if design.top is not None else None
    if top_name is None:
        if len(module_ops) == 1:
            top_name = module_ops[0].sym_name.data
        else:
            diagnostics.append(
                _diagnostic(
                    MISSING_TOP,
                    "Top module is required when multiple modules exist",
                    Severity.ERROR,
                )
            )
            return None, diagnostics
    if top_name not in modules:
        diagnostics.append(
            _diagnostic(
                MISSING_TOP,
                f"Top module '{top_name}' is not defined",
                Severity.ERROR,
            )
        )
        return None, diagnostics

    lines: List[str] = []
    had_error = False

    header_context = {"backend": options.backend_name, "top": top_name}
    header, header_error = _render_system_device(
        "__netlist_header__",
        options.backend_config,
        header_context,
        diagnostics,
    )
    if header:
        lines.append(header)
    had_error = had_error or header_error

    for module in module_ops:
        is_top = module.sym_name.data == top_name
        module_lines, module_error = _emit_module(
            module,
            devices,
            modules,
            is_top=is_top,
            options=options,
            diagnostics=diagnostics,
        )
        lines.extend(module_lines)
        had_error = had_error or module_error

    footer_context = {"backend": options.backend_name, "top": top_name}
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


def _emit_module(
    module: ModuleOp,
    devices: Dict[str, DeviceOp],
    modules: Dict[str, ModuleOp],
    *,
    is_top: bool,
    options: "EmitOptions",
    diagnostics: List[Diagnostic],
) -> Tuple[List[str], bool]:
    lines: List[str] = []
    had_error = False

    ports = [attr.data for attr in module.port_order.data]

    if not (is_top and not options.top_as_subckt):
        header_context = {"name": module.sym_name.data, "ports": " ".join(ports)}
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
            devices,
            modules,
            options=options,
            diagnostics=diagnostics,
        )
        if line is not None:
            lines.append(line)
        had_error = had_error or inst_error

    if not (is_top and not options.top_as_subckt):
        footer_context = {"name": module.sym_name.data}
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
    devices: Dict[str, DeviceOp],
    modules: Dict[str, ModuleOp],
    *,
    options: "EmitOptions",
    diagnostics: List[Diagnostic],
) -> Tuple[Optional[str], bool]:
    ref_name = instance.ref.root_reference.data
    if ref_name in modules:
        port_order = [attr.data for attr in modules[ref_name].port_order.data]
        conns, had_error = _ordered_conns(instance, port_order, diagnostics)
        if had_error:
            return None, True

        call_context = {
            "name": instance.name_attr.data,
            "ports": " ".join(conns),
            "ref": ref_name,
        }
        return _render_system_device(
            "__subckt_call__",
            options.backend_config,
            call_context,
            diagnostics,
        )

    if ref_name not in devices:
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

    device = devices[ref_name]
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
    conns, had_error = _ordered_conns(instance, port_order, diagnostics)
    if had_error:
        return None, True
    ports_str = " ".join(conns)

    device_params = _dict_attr_to_strings(device.params)
    backend_params = _dict_attr_to_strings(backend.params)
    inst_params = _dict_attr_to_strings(instance.params)
    merged_params, params_str, param_diags = _merge_params(
        device_params,
        backend_params,
        inst_params,
        instance_name=instance.name_attr.data,
        device_name=ref_name,
        loc=instance.src,
    )
    diagnostics.extend(param_diags)

    template = backend.template.data
    placeholders = _validate_template(template, ref_name, diagnostics, loc=backend.src)
    if placeholders is None:
        return None, True

    props = _dict_attr_to_strings(backend.props)
    props.setdefault("params", params_str)
    template_values = {
        "name": instance.name_attr.data,
        "ports": ports_str,
    }
    template_values.update(merged_params)
    template_values.update(props)
    try:
        rendered = template.format_map(template_values)
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

    should_collapse = False
    if "ports" in placeholders and not ports_str:
        should_collapse = True
    if "params" in placeholders and not params_str:
        should_collapse = True
    if should_collapse:
        rendered = " ".join(rendered.split())
    return rendered, False


def _ordered_conns(
    instance: InstanceOp,
    port_order: Iterable[str],
    diagnostics: DiagnosticCollector | List[Diagnostic],
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

    return [conn_map[port] for port in port_list], False


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
        rendered = template.format_map(context)
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

    should_collapse = False
    if "ports" in placeholders and context.get("ports", "") == "":
        should_collapse = True
    if should_collapse:
        rendered = " ".join(rendered.split())

    return rendered, False
