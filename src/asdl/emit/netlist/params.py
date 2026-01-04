from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from xdsl.dialects.builtin import DictionaryAttr, LocationAttr, StringAttr

from asdl.diagnostics import Diagnostic, Severity

from .diagnostics import UNKNOWN_INSTANCE_PARAM, _diagnostic


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
    emit_warnings: bool = True,
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
