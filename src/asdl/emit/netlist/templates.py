from __future__ import annotations

import re
import string
from typing import Dict, Optional

from xdsl.dialects.builtin import LocationAttr

from asdl.diagnostics import Diagnostic, Severity
from asdl.diagnostics.collector import DiagnosticCollector
from asdl.emit.backend_config import BackendConfig, REQUIRED_SYSTEM_DEVICES
from asdl.ir.ifir import BackendOp, DeviceOp

from .diagnostics import (
    MALFORMED_TEMPLATE,
    MISSING_PLACEHOLDER,
    UNKNOWN_REFERENCE,
    _diagnostic,
    _emit_diagnostic,
)
from .params import _dict_attr_to_strings

SYSTEM_DEVICE_REQUIRED_PLACEHOLDERS: Dict[str, set[str]] = {
    "__subckt_header__": {"name"},
    "__subckt_footer__": set(),
    "__subckt_call__": {"name", "ports", "ref"},
    "__netlist_header__": set(),
    "__netlist_footer__": set(),
}

SYSTEM_DEVICE_ALLOWED_PLACEHOLDERS: Dict[str, set[str]] = {
    "__subckt_header__": {"name", "ports", "file_id", "sym_name"},
    "__subckt_footer__": {"name", "sym_name"},
    "__subckt_call__": {"name", "ports", "ref", "file_id", "sym_name"},
    "__netlist_header__": {
        "backend",
        "top",
        "file_id",
        "top_sym_name",
        "emit_date",
        "emit_time",
    },
    "__netlist_footer__": {
        "backend",
        "top",
        "file_id",
        "top_sym_name",
        "emit_date",
        "emit_time",
    },
}

_BRACED_ENV_VAR_PATTERN = re.compile(r"\$\{[^}]+\}")


def _escape_braced_env_vars(template: str) -> tuple[str, dict[str, str]]:
    env_vars: dict[str, str] = {}

    def replace(match: re.Match[str]) -> str:
        placeholder = f"__ASDL_ENVVAR_{len(env_vars)}__"
        env_vars[placeholder] = match.group(0)
        return f"${placeholder}"

    escaped = _BRACED_ENV_VAR_PATTERN.sub(replace, template)
    return escaped, env_vars


def _restore_braced_env_vars(rendered: str, env_vars: dict[str, str]) -> str:
    for placeholder, token in env_vars.items():
        rendered = rendered.replace(f"${placeholder}", token)
    return rendered


def _validate_template(
    template: str,
    device_name: str,
    diagnostics: DiagnosticCollector | list[Diagnostic],
    *,
    loc: LocationAttr | None = None,
) -> Optional[set[str]]:
    try:
        placeholders = _template_field_roots(template)
    except ValueError as exc:
        _emit_diagnostic(
            diagnostics,
            _diagnostic(
                MALFORMED_TEMPLATE,
                f"Backend template for '{device_name}' is malformed: {exc}",
                Severity.ERROR,
                loc,
            ),
        )
        return None
    return placeholders


def _template_field_roots(template: str) -> set[str]:
    template, _ = _escape_braced_env_vars(template)
    formatter = string.Formatter()
    fields: set[str] = set()
    for _, field_name, _, _ in formatter.parse(template):
        if not field_name:
            continue
        root = field_name.split(".", 1)[0].split("[", 1)[0]
        if root:
            fields.add(root)
    return fields


def _validate_system_device_templates(
    config: BackendConfig, diagnostics: DiagnosticCollector
) -> None:
    for device_name in REQUIRED_SYSTEM_DEVICES:
        template = config.templates.get(device_name)
        if template is None:
            continue
        try:
            placeholders = _template_field_roots(template.template)
        except ValueError as exc:
            diagnostics.emit(
                _diagnostic(
                    MALFORMED_TEMPLATE,
                    f"System device '{device_name}' template is malformed: {exc}",
                    Severity.ERROR,
                )
            )
            continue

        required = SYSTEM_DEVICE_REQUIRED_PLACEHOLDERS.get(device_name, set())
        missing = required - placeholders
        if missing:
            missing_list = ", ".join(sorted(missing))
            diagnostics.emit(
                _diagnostic(
                    MISSING_PLACEHOLDER,
                    (
                        f"System device '{device_name}' template is missing required "
                        f"placeholders: {missing_list}"
                    ),
                    Severity.ERROR,
                )
            )

        allowed = SYSTEM_DEVICE_ALLOWED_PLACEHOLDERS.get(device_name, set())
        unknown = placeholders - allowed
        if unknown:
            unknown_name = sorted(unknown)[0]
            diagnostics.emit(
                _diagnostic(
                    UNKNOWN_REFERENCE,
                    (
                        f"System device '{device_name}' template references "
                        f"unknown placeholder '{unknown_name}'"
                    ),
                    Severity.ERROR,
                )
            )


def _allowed_backend_placeholders(device: DeviceOp, backend: BackendOp) -> set[str]:
    device_params = _dict_attr_to_strings(device.params)
    backend_params = _dict_attr_to_strings(backend.params)
    props = _dict_attr_to_strings(backend.props)

    allowed = {"name", "ports", "params"}
    allowed.update(device_params.keys())
    allowed.update(backend_params.keys())
    allowed.update(props.keys())
    return allowed
