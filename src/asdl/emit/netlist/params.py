from __future__ import annotations

from typing import Dict, Iterable, List, Mapping, Optional, Tuple

from xdsl.dialects.builtin import DictionaryAttr, LocationAttr, StringAttr

from asdl.diagnostics import Diagnostic, Severity

from .diagnostics import (
    INSTANCE_VARIABLE_OVERRIDE,
    UNKNOWN_INSTANCE_PARAM,
    VARIABLE_KEY_COLLISION,
    _diagnostic,
)


def _dict_attr_to_strings(
    values: Optional[DictionaryAttr | Mapping[str, object]]
) -> Dict[str, str]:
    if values is None:
        return {}
    if isinstance(values, DictionaryAttr):
        items = values.data.items()
    else:
        items = values.items()
    return {key: _stringify_attr(value) for key, value in items}


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
    emit_warnings: bool = True,
) -> Tuple[Dict[str, str], str, List[Diagnostic]]:
    """Merge device/backend/instance parameters for emission.

    Args:
        device_params: Device-level parameter defaults.
        backend_params: Backend-level parameter overrides.
        inst_params: Instance parameter overrides.
        instance_name: Instance name for diagnostics.
        device_name: Device name for diagnostics.
        loc: Optional location for diagnostics.
        emit_warnings: Whether to emit warnings for unknown instance params.

    Returns:
        Merged parameters, formatted params string, and diagnostics.
    """
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
            if emit_warnings:
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


def _merge_variables(
    device_vars: Dict[str, str],
    backend_vars: Dict[str, str],
    *,
    device_param_keys: Iterable[str],
    backend_param_keys: Iterable[str],
    backend_prop_keys: Iterable[str],
    instance_params: Dict[str, str],
    instance_name: str,
    device_name: str,
    device_loc: LocationAttr | None = None,
    backend_loc: LocationAttr | None = None,
    instance_loc: LocationAttr | None = None,
) -> Tuple[Dict[str, str], List[Diagnostic]]:
    """Merge device/backend variables and emit collision diagnostics.

    Args:
        device_vars: Device-level variables.
        backend_vars: Backend-level variables.
        device_param_keys: Parameter keys defined on the device.
        backend_param_keys: Parameter keys defined on the backend.
        backend_prop_keys: Backend prop keys.
        instance_params: Instance params to check for variable overrides.
        instance_name: Instance name for diagnostics.
        device_name: Device name for diagnostics.
        device_loc: Optional device location for diagnostics.
        backend_loc: Optional backend location for diagnostics.
        instance_loc: Optional instance location for diagnostics.

    Returns:
        Merged variables and diagnostics.
    """
    diagnostics: List[Diagnostic] = []
    param_keys = set(device_param_keys) | set(backend_param_keys)
    prop_keys = set(backend_prop_keys)

    variable_sources: Dict[str, str] = {}
    for key in device_vars:
        variable_sources.setdefault(key, "device")
    for key in backend_vars:
        variable_sources[key] = "backend"

    for key, source in variable_sources.items():
        loc = backend_loc if source == "backend" else device_loc
        source_label = "Backend variable" if source == "backend" else "Variable"
        scope_label = "for device" if source == "backend" else "on device"
        if key in param_keys:
            diagnostics.append(
                _diagnostic(
                    VARIABLE_KEY_COLLISION,
                    (
                        f"{source_label} '{key}' {scope_label} '{device_name}' "
                        f"collides with parameter key '{key}'"
                    ),
                    Severity.ERROR,
                    loc,
                )
            )
        if key in prop_keys:
            diagnostics.append(
                _diagnostic(
                    VARIABLE_KEY_COLLISION,
                    (
                        f"{source_label} '{key}' {scope_label} '{device_name}' "
                        f"collides with backend prop '{key}'"
                    ),
                    Severity.ERROR,
                    backend_loc or loc,
                )
            )

    overrides = set(instance_params) & set(variable_sources)
    for key in sorted(overrides):
        diagnostics.append(
            _diagnostic(
                INSTANCE_VARIABLE_OVERRIDE,
                (
                    f"Instance '{instance_name}' overrides variable '{key}' on "
                    f"device '{device_name}'"
                ),
                Severity.ERROR,
                instance_loc,
            )
        )

    merged = dict(device_vars)
    merged.update(backend_vars)
    return merged, diagnostics
