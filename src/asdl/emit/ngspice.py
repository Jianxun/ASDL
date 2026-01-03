from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import string
from typing import Dict, Iterable, List, Optional, Tuple

import yaml
from xdsl.dialects.builtin import DictionaryAttr, LocationAttr, StringAttr

from asdl.diagnostics import Diagnostic, Severity, format_code
from asdl.emit.backend_config import BackendConfig, load_backend_config, validate_system_devices
from asdl.ir.ifir import BackendOp, DesignOp, DeviceOp, InstanceOp, ModuleOp
from asdl.ir.location import location_attr_to_span

NO_SPAN_NOTE = "No source span available."

MISSING_TOP = format_code("EMIT", 1)
UNKNOWN_INSTANCE_PARAM = format_code("EMIT", 2)
UNKNOWN_REFERENCE = format_code("EMIT", 3)
MISSING_BACKEND = format_code("EMIT", 4)
MISSING_CONN = format_code("EMIT", 5)
UNKNOWN_CONN_PORT = format_code("EMIT", 6)
MISSING_PLACEHOLDER = format_code("EMIT", 7)
MALFORMED_TEMPLATE = format_code("EMIT", 8)

REQUIRED_PLACEHOLDERS = {"name"}


@dataclass(frozen=True)
class EmitOptions:
    top_as_subckt: bool = False
    backend_name: str = "ngspice"
    backend_config: Optional[BackendConfig] = None


def emit_ngspice(
    design: DesignOp,
    *,
    top_as_subckt: bool = False,
    backend_config_path: Optional[Path] = None,
) -> Tuple[Optional[str], List[Diagnostic]]:
    diagnostics: List[Diagnostic] = []

    # Load backend config
    try:
        config = load_backend_config("ngspice", backend_config_path)
    except (FileNotFoundError, KeyError, yaml.YAMLError) as exc:
        # Emit diagnostic for config loading failure
        diagnostics.append(
            _diagnostic(
                MISSING_BACKEND,
                f"Failed to load backend config: {exc}",
                Severity.ERROR,
            )
        )
        return None, diagnostics

    # Validate system devices
    validation_diags = validate_system_devices(config)
    diagnostics.extend(validation_diags)
    if any(d.severity == Severity.ERROR for d in validation_diags):
        return None, diagnostics

    options = EmitOptions(
        top_as_subckt=top_as_subckt,
        backend_name="ngspice",
        backend_config=config,
    )
    netlist, emit_diags = _emit_design(design, options)
    diagnostics.extend(emit_diags)
    return netlist, diagnostics


def _emit_design(
    design: DesignOp, options: EmitOptions
) -> Tuple[Optional[str], List[Diagnostic]]:
    diagnostics: List[Diagnostic] = []
    modules: Dict[str, ModuleOp] = {}
    devices: Dict[str, DeviceOp] = {}
    module_ops: List[ModuleOp] = []

    for op in design.body.block.ops:
        if isinstance(op, ModuleOp):
            name = op.sym_name.data
            modules[name] = op
            module_ops.append(op)
            continue
        if isinstance(op, DeviceOp):
            devices[op.sym_name.data] = op

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

    # Render netlist header (required)
    header_context = {"backend": options.backend_name, "top": top_name}
    header, header_error = _render_system_device(
        "__netlist_header__",
        options.backend_config,
        header_context,
        diagnostics,
    )
    if header:  # Only add non-empty headers
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

    # Render netlist footer (required)
    footer_context = {"backend": options.backend_name, "top": top_name}
    footer, footer_error = _render_system_device(
        "__netlist_footer__",
        options.backend_config,
        footer_context,
        diagnostics,
    )
    if footer:  # Only add non-empty footers
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
    options: EmitOptions,
    diagnostics: List[Diagnostic],
) -> Tuple[List[str], bool]:
    lines: List[str] = []
    had_error = False

    ports = [attr.data for attr in module.port_order.data]

    # Only emit wrapper if NOT (top without top_as_subckt)
    # When top without top_as_subckt, comment out the wrapper
    if is_top and not options.top_as_subckt:
        # Comment out wrapper for top module when top_as_subckt is False
        # Inline the subckt line format
        if ports:
            header = f".subckt {module.sym_name.data} {' '.join(ports)}"
        else:
            header = f".subckt {module.sym_name.data}"
        footer = f".ends {module.sym_name.data}"
        lines.append(f"*{header}")
    else:
        # Use system device templates for wrapper
        header_context = {"name": module.sym_name.data, "ports": " ".join(ports)}
        header, header_error = _render_system_device(
            "__subckt_header__",
            options.backend_config,
            header_context,
            diagnostics,
        )
        if header is not None and header:  # Skip empty templates
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

    # Emit footer
    if is_top and not options.top_as_subckt:
        # Comment out footer for top module when top_as_subckt is False
        lines.append(f"*{footer}")
    else:
        # Use system device template for footer
        footer_context = {"name": module.sym_name.data}
        footer, footer_error = _render_system_device(
            "__subckt_footer__",
            options.backend_config,
            footer_context,
            diagnostics,
        )
        if footer is not None and footer:  # Skip empty templates
            lines.append(footer)
        had_error = had_error or footer_error

    return lines, had_error


def _emit_instance(
    instance: InstanceOp,
    devices: Dict[str, DeviceOp],
    modules: Dict[str, ModuleOp],
    *,
    options: EmitOptions,
    diagnostics: List[Diagnostic],
) -> Tuple[Optional[str], bool]:
    ref_name = instance.ref.root_reference.data
    if ref_name in modules:
        port_order = [attr.data for attr in modules[ref_name].port_order.data]
        conns, had_error = _ordered_conns(instance, port_order, diagnostics)
        if had_error:
            return None, True

        # Use __subckt_call__ system device
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
                f"Instance '{instance.name_attr.data}' references unknown symbol '{ref_name}'",
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
                f"Backend template for '{ref_name}' references unknown placeholder '{exc.args[0]}'",
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
    diagnostics: List[Diagnostic],
) -> Tuple[List[str], bool]:
    port_list = list(port_order)
    conn_map = {conn.port.data: conn.net.data for conn in instance.conns.data}
    had_error = False

    missing_ports = [port for port in port_list if port not in conn_map]
    if missing_ports:
        missing_str = ", ".join(missing_ports)
        diagnostics.append(
            _diagnostic(
                MISSING_CONN,
                f"Instance '{instance.name_attr.data}' is missing conns for ports: {missing_str}",
                Severity.ERROR,
                instance.src,
            )
        )
        had_error = True

    port_set = set(port_list)
    unknown_ports = [port for port in conn_map if port not in port_set]
    if unknown_ports:
        unknown_str = ", ".join(unknown_ports)
        diagnostics.append(
            _diagnostic(
                UNKNOWN_CONN_PORT,
                f"Instance '{instance.name_attr.data}' has conns for unknown ports: {unknown_str}",
                Severity.ERROR,
                instance.src,
            )
        )
        had_error = True

    if had_error:
        return [], True

    return [conn_map[port] for port in port_list], False


def _select_backend(device: DeviceOp, backend_name: str) -> Optional[BackendOp]:
    for op in device.body.block.ops:
        if isinstance(op, BackendOp) and op.name_attr.data == backend_name:
            return op
    return None


def _validate_template(
    template: str,
    device_name: str,
    diagnostics: List[Diagnostic],
    *,
    loc: LocationAttr | None = None,
) -> Optional[set[str]]:
    try:
        placeholders = _template_field_roots(template)
    except ValueError as exc:
        diagnostics.append(
            _diagnostic(
                MALFORMED_TEMPLATE,
                f"Backend template for '{device_name}' is malformed: {exc}",
                Severity.ERROR,
                loc,
            )
        )
        return None
    missing = REQUIRED_PLACEHOLDERS - placeholders
    if missing:
        missing_list = ", ".join(sorted(missing))
        diagnostics.append(
            _diagnostic(
                MISSING_PLACEHOLDER,
                (
                    f"Backend template for '{device_name}' is missing required "
                    f"placeholders: {missing_list}"
                ),
                Severity.ERROR,
                loc,
            )
        )
        return None
    return placeholders


def _template_field_roots(template: str) -> set[str]:
    formatter = string.Formatter()
    fields: set[str] = set()
    for _, field_name, _, _ in formatter.parse(template):
        if not field_name:
            continue
        root = field_name.split(".", 1)[0].split("[", 1)[0]
        if root:
            fields.add(root)
    return fields


def _render_system_device(
    device_name: str,
    config: BackendConfig,
    context: Dict[str, str],
    diagnostics: List[Diagnostic],
) -> Tuple[Optional[str], bool]:
    """Render a system device template with the given context.

    Args:
        device_name: System device name (e.g., "__subckt_header__")
        config: Backend configuration containing system device templates
        context: Template placeholder values (e.g., {"name": "amp", "ports": "in out"})
        diagnostics: List to append any diagnostics

    Returns:
        (rendered_string, had_error) tuple
    """
    if device_name not in config.system_devices:
        diagnostics.append(
            _diagnostic(
                MISSING_BACKEND,
                f"System device '{device_name}' not defined in backend config",
                Severity.ERROR,
            )
        )
        return None, True

    sys_device = config.system_devices[device_name]
    template = sys_device.template

    # Validate template placeholders
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

    # Render template
    try:
        rendered = template.format_map(context)
    except KeyError as exc:
        diagnostics.append(
            _diagnostic(
                UNKNOWN_REFERENCE,
                f"System device '{device_name}' template references unknown placeholder '{exc.args[0]}'",
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

    # Whitespace collapsing: if {ports} is in placeholders and context["ports"] is empty, collapse whitespace
    should_collapse = False
    if "ports" in placeholders and context.get("ports", "") == "":
        should_collapse = True
    if should_collapse:
        rendered = " ".join(rendered.split())

    return rendered, False


def _dict_attr_to_strings(values: Optional[DictionaryAttr]) -> Dict[str, str]:
    if values is None:
        return {}
    return {key: _stringify_attr(value) for key, value in values.data.items()}


def _stringify_attr(value: object) -> str:
    if isinstance(value, StringAttr):
        return value.data
    if hasattr(value, "data"):
        return str(value.data)
    return str(value)


def _merge_params(
    device_params: Dict[str, str],
    backend_params: Dict[str, str],
    inst_params: Dict[str, str],
    *,
    instance_name: str,
    device_name: str,
    loc: LocationAttr | None = None,
) -> Tuple[Dict[str, str], str, List[Diagnostic]]:
    diagnostics: List[Diagnostic] = []
    order: List[str] = list(device_params.keys())
    for key in backend_params.keys():
        if key not in order:
            order.append(key)
    allowed = set(order)

    merged: Dict[str, str] = {}
    merged.update(device_params)
    merged.update(backend_params)

    for key, value in inst_params.items():
        if key not in allowed:
            diagnostics.append(
                _diagnostic(
                    UNKNOWN_INSTANCE_PARAM,
                    (
                        f"Instance '{instance_name}' overrides unknown param '{key}' "
                        f"on device '{device_name}'"
                    ),
                    Severity.WARNING,
                    loc,
                )
            )
            continue
        merged[key] = value

    tokens = [f"{key}={merged[key]}" for key in order if key in merged]
    return merged, " ".join(tokens), diagnostics


def _diagnostic(
    code: str, message: str, severity: Severity, loc: LocationAttr | None = None
) -> Diagnostic:
    span = location_attr_to_span(loc)
    notes = None if span is not None else [NO_SPAN_NOTE]
    return Diagnostic(
        code=code,
        severity=severity,
        message=message,
        primary_span=span,
        notes=notes,
        source="emit",
    )


__all__ = ["EmitOptions", "emit_ngspice"]
