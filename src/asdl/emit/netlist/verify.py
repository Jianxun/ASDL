from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

from asdl.diagnostics import Diagnostic, Severity
from asdl.diagnostics.collector import DiagnosticCollector
from asdl.emit.backend_config import BackendConfig, validate_system_devices
from asdl.emit.netlist_ir import (
    NetlistBackend,
    NetlistDesign,
    NetlistDevice,
    NetlistInstance,
)
from asdl.emit.verify_netlist_ir import verify_netlist_ir

from .diagnostics import (
    MISSING_BACKEND,
    MISSING_CONN,
    UNKNOWN_CONN_PORT,
    UNKNOWN_REFERENCE,
    _diagnostic,
    _emit_diagnostic,
)
from .ir_utils import (
    _build_netlist_ir_index,
    _select_netlist_ir_symbol,
)
from .params import _dict_attr_to_strings, _merge_variables
from .templates import _validate_system_device_templates, _validate_template


_MAX_PORT_PREVIEW = 8
_MAX_PORT_MATCH_SCAN = 200


def _preview_names(names: Iterable[str], limit: int) -> Tuple[List[str], bool]:
    """Collect a preview list of names up to a limit.

    Args:
        names: Iterable of names to preview.
        limit: Maximum number of names to return.

    Returns:
        Tuple of previewed names and a flag indicating remaining items.
    """
    preview: List[str] = []
    iterator = iter(names)
    for _ in range(limit):
        try:
            preview.append(next(iterator))
        except StopIteration:
            return preview, False
    has_more = next(iterator, None) is not None
    return preview, has_more


def _case_insensitive_match(
    target: str, candidates: Iterable[str], *, max_scan: int
) -> Optional[str]:
    """Find a unique case-insensitive match for a target.

    Args:
        target: Name to match.
        candidates: Candidate names to scan.
        max_scan: Maximum number of candidates to scan.

    Returns:
        Matching candidate if unique, otherwise None.
    """
    target_lower = target.lower()
    match: Optional[str] = None
    scanned = 0
    for candidate in candidates:
        scanned += 1
        if scanned > max_scan:
            return None
        if candidate == target:
            continue
        if candidate.lower() == target_lower:
            if match is not None and match != candidate:
                return None
            match = candidate
    return match


def _ordered_conns_netlist_ir(
    instance: NetlistInstance,
    port_order: Iterable[str],
    diagnostics: DiagnosticCollector | List[Diagnostic],
) -> Tuple[List[str], bool]:
    """Order NetlistIR conns by port list while validating port usage.

    Args:
        instance: NetlistIR instance to validate.
        port_order: Declared port order to enforce.
        diagnostics: Collector or list to append diagnostics.

    Returns:
        Tuple of ordered net names and an error flag.
    """
    port_list = list(port_order)
    conn_map = {conn.port: conn.net for conn in instance.conns}
    had_error = False

    missing_ports = [port for port in port_list if port not in conn_map]
    if missing_ports:
        missing_str = ", ".join(missing_ports)
        _emit_diagnostic(
            diagnostics,
            _diagnostic(
                MISSING_CONN,
                (
                    f"Instance '{instance.name}' is missing conns for ports: "
                    f"{missing_str}"
                ),
                Severity.ERROR,
                None,
            ),
        )
        had_error = True

    port_set = set(port_list)
    unknown_ports = [port for port in conn_map if port not in port_set]
    if unknown_ports:
        unknown_str = ", ".join(unknown_ports)
        notes: List[str] = []
        preview, truncated = _preview_names(port_list, _MAX_PORT_PREVIEW)
        if preview:
            notes.append(f"Valid ports are: {', '.join(preview)}")
            if truncated:
                notes.append("See the symbol definition for the full port list.")
        for port in unknown_ports:
            case_match = _case_insensitive_match(
                port,
                port_list,
                max_scan=_MAX_PORT_MATCH_SCAN,
            )
            if case_match:
                notes.append(
                    f"Port names are case-sensitive; did you mean '{case_match}'?"
                )
                break
        _emit_diagnostic(
            diagnostics,
            _diagnostic(
                UNKNOWN_CONN_PORT,
                (
                    f"Instance '{instance.name}' has conns for unknown ports: "
                    f"{unknown_str}"
                ),
                Severity.ERROR,
                None,
                notes=notes or None,
                help="Update endpoint names to match the device/module port list.",
            ),
        )
        had_error = True

    if had_error:
        return [], True

    return [conn_map[port] for port in port_list], False


def _select_netlist_backend(
    device: NetlistDevice, backend_name: str
) -> Optional[NetlistBackend]:
    """Return the NetlistIR backend definition for a device.

    Args:
        device: NetlistIR device definition.
        backend_name: Backend name to match.

    Returns:
        Matching backend or None.
    """
    for backend in device.backends:
        if backend.name == backend_name:
            return backend
    return None


def _string_dict(values: Optional[dict[str, str]]) -> dict[str, str]:
    """Normalize optional NetlistIR dict values to a new dict.

    Args:
        values: Optional dict of string values.

    Returns:
        Copy of the dict or an empty dict when None.
    """
    return dict(values) if values else {}


def _allowed_backend_placeholders_ir(
    device: NetlistDevice, backend: NetlistBackend
) -> set[str]:
    """Return allowed template placeholders for a NetlistIR backend template.

    Args:
        device: NetlistIR device definition.
        backend: NetlistIR backend definition.

    Returns:
        Set of allowed placeholder names.
    """
    device_params = _string_dict(device.params)
    backend_params = _string_dict(backend.params)
    device_vars = _string_dict(device.variables)
    backend_vars = _string_dict(backend.variables)
    props = _string_dict(backend.props)

    allowed = {"name", "ports", "params"}
    allowed.update(device_params.keys())
    allowed.update(backend_params.keys())
    allowed.update(device_vars.keys())
    allowed.update(backend_vars.keys())
    allowed.update(props.keys())
    return allowed


def _run_netlist_verification(
    design: NetlistDesign,
    *,
    backend_name: str,
    backend_config: BackendConfig,
) -> List[Diagnostic]:
    """Verify NetlistIR designs with backend/template validation.

    Args:
        design: NetlistIR design to verify.
        backend_name: Backend identifier to validate against.
        backend_config: Backend configuration for system device checks.

    Returns:
        List of diagnostics produced during verification.
    """
    diagnostics = DiagnosticCollector()
    diagnostics.extend(verify_netlist_ir(design))

    index = _build_netlist_ir_index(design, diagnostics)
    if index is None:
        return diagnostics.to_list()

    diagnostics.extend(validate_system_devices(backend_config))
    _validate_system_device_templates(backend_config, diagnostics)

    for module in design.modules:
        for instance in module.instances:
            ref_name = instance.ref
            ref_file_id = instance.ref_file_id
            target_module = _select_netlist_ir_symbol(
                index.modules_by_name, index.modules_by_key, ref_name, ref_file_id
            )
            if target_module is not None:
                _ordered_conns_netlist_ir(
                    instance, target_module.ports, diagnostics
                )
                continue
            target_device = _select_netlist_ir_symbol(
                index.devices_by_name, index.devices_by_key, ref_name, ref_file_id
            )
            if target_device is None:
                diagnostics.emit(
                    _diagnostic(
                        UNKNOWN_REFERENCE,
                        (
                            f"Instance '{instance.name}' references unknown "
                            f"symbol '{ref_name}'"
                        ),
                        Severity.ERROR,
                        None,
                    )
                )
                continue

            backend = _select_netlist_backend(target_device, backend_name)
            if backend is None:
                diagnostics.emit(
                    _diagnostic(
                        MISSING_BACKEND,
                        (
                            f"Device '{ref_name}' has no backend "
                            f"'{backend_name}'"
                        ),
                        Severity.ERROR,
                        None,
                    )
                )
                continue

            _ordered_conns_netlist_ir(instance, target_device.ports, diagnostics)

            device_params = _string_dict(target_device.params)
            backend_params = _string_dict(backend.params)
            instance_params = _string_dict(instance.params)
            device_vars = _string_dict(target_device.variables)
            backend_vars = _string_dict(backend.variables)
            props = _string_dict(backend.props)
            _, variable_diags = _merge_variables(
                device_vars,
                backend_vars,
                device_param_keys=device_params.keys(),
                backend_param_keys=backend_params.keys(),
                backend_prop_keys=props.keys(),
                instance_params=instance_params,
                instance_name=instance.name,
                device_name=ref_name,
                device_loc=None,
                backend_loc=None,
                instance_loc=None,
            )
            diagnostics.extend(variable_diags)

            placeholders = _validate_template(
                backend.template,
                ref_name,
                diagnostics,
                loc=None,
            )
            if placeholders is None:
                continue

            unknown = placeholders - _allowed_backend_placeholders_ir(
                target_device, backend
            )
            if unknown:
                unknown_name = sorted(unknown)[0]
                diagnostics.emit(
                    _diagnostic(
                        UNKNOWN_REFERENCE,
                        (
                            f"Backend template for '{ref_name}' references "
                            f"unknown placeholder '{unknown_name}'"
                        ),
                        Severity.ERROR,
                        None,
                    )
                )

    return diagnostics.to_list()
