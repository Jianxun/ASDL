from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Optional, Tuple

from asdl.diagnostics import Diagnostic, Severity
from asdl.diagnostics.collector import DiagnosticCollector
from asdl.emit.backend_config import BackendConfig
from asdl.emit.netlist_ir import (
    NetlistBackend,
    NetlistDesign,
    NetlistDevice,
    NetlistInstance,
    NetlistModule,
    PatternExpressionTable as NetlistPatternExpressionTable,
    PatternOrigin as NetlistPatternOrigin,
)

from .diagnostics import (
    EMISSION_NAME_COLLISION,
    MALFORMED_TEMPLATE,
    MISSING_BACKEND,
    MISSING_TOP,
    MISSING_CONN,
    PROVENANCE_METADATA_WARNING,
    UNKNOWN_CONN_PORT,
    UNKNOWN_REFERENCE,
    UNRESOLVED_ENV_VAR,
    _diagnostic,
    _emit_diagnostic,
)
from .ir_utils import (
    _build_netlist_ir_index,
    _select_netlist_ir_symbol,
)
from .params import _dict_attr_to_strings, _merge_params, _merge_variables
from .templates import (
    _escape_braced_env_vars,
    _restore_braced_env_vars,
    _template_field_roots,
    _validate_template,
)


@dataclass(frozen=True)
class _NetlistIRSymbolMaps:
    index: "NetlistIRIndex"
    module_emitted_names: Dict[int, str]


@dataclass(frozen=True)
class EmissionNameMapEntry:
    """Deterministic logical-to-emitted module name mapping entry."""

    symbol: str
    file_id: Optional[str]
    base_name: str
    emitted_name: str
    renamed: bool


_ENV_VAR_PATTERN = re.compile(r"\$(\w+|\{[^}]+\})")
_MODULE_SYMBOL_PATTERN = re.compile(
    r"^(?P<cell>[A-Za-z_][A-Za-z0-9_]*)(?:@(?P<view>[A-Za-z_][A-Za-z0-9_]*))?$"
)
_SANITIZE_TOKEN_PATTERN = re.compile(r"[^A-Za-z0-9_]+")
_MAX_PORT_PREVIEW = 8
_MAX_PORT_MATCH_SCAN = 200


def _has_known_file_id(file_id: Optional[str]) -> bool:
    """Return whether provenance file_id metadata is present and non-empty."""
    return isinstance(file_id, str) and bool(file_id.strip())


def _preview_names(names: Iterable[str], limit: int) -> Tuple[List[str], bool]:
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

def _emit_design(
    design: NetlistDesign, options: "EmitOptions"
) -> Tuple[Optional[str], List[Diagnostic]]:
    """Render a NetlistIR design into a netlist string."""
    return _emit_netlist_ir_design(design, options)


def _emit_netlist_ir_design(
    design: NetlistDesign, options: "EmitOptions"
) -> Tuple[Optional[str], List[Diagnostic]]:
    """Render a NetlistIR design into a netlist string."""
    diagnostics: List[Diagnostic] = []
    collector = DiagnosticCollector()

    entry_file_id = design.entry_file_id

    index = _build_netlist_ir_index(design, collector)
    diagnostics.extend(collector.to_list())
    if index is None:
        return None, diagnostics

    top_module = _select_netlist_ir_symbol(
        index.modules_by_name,
        index.modules_by_key,
        index.top_name,
        index.top_file_id,
    )
    if top_module is None:
        diagnostics.append(
            _diagnostic(
                MISSING_TOP,
                f"Top module '{index.top_name}' is not defined in entry file",
                Severity.ERROR,
            )
        )
        return None, diagnostics

    reachable_modules = _collect_reachable_modules_ir(design, index, top_module)

    _emit_provenance_diagnostics_ir(reachable_modules, design, index, top_module, diagnostics)
    module_emitted_names = _build_module_emitted_names_ir(reachable_modules, diagnostics)
    top_emitted_name = _module_emitted_name_ir(top_module, module_emitted_names)

    lines: List[str] = []
    had_error = False

    emit_context = _emit_timestamp_context(options.emit_timestamp)
    header_context = {
        "backend": options.backend_name,
        "top": top_emitted_name,
        "top_sym_name": index.top_name,
        "file_id": _entry_file_id_value_ir(entry_file_id, top_module),
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

    symbol_maps = _NetlistIRSymbolMaps(
        index=index, module_emitted_names=module_emitted_names
    )
    for module in reachable_modules:
        module_lines, module_error = _emit_netlist_ir_module(
            module,
            symbol_maps,
            is_top=module is top_module,
            options=options,
            diagnostics=diagnostics,
        )
        lines.extend(module_lines)
        had_error = had_error or module_error

    footer_context = {
        "backend": options.backend_name,
        "top": top_emitted_name,
        "top_sym_name": index.top_name,
        "file_id": _entry_file_id_value_ir(entry_file_id, top_module),
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


def _collect_reachable_modules_ir(
    design: NetlistDesign,
    index: "NetlistIRIndex",
    top_module: NetlistModule,
) -> List[NetlistModule]:
    """Collect modules transitively reachable from the selected top module.

    Traversal order is deterministic: depth-first by instance declaration order,
    with symbol lookup following existing NetlistIR resolution rules.
    """
    module_order = {_module_key_ir(module): idx for idx, module in enumerate(design.modules)}
    reachable_by_key: Dict[int, NetlistModule] = {}
    visited: set[int] = set()

    def _visit(module: NetlistModule) -> None:
        module_key = _module_key_ir(module)
        if module_key in visited:
            return
        visited.add(module_key)
        reachable_by_key[module_key] = module
        for instance in module.instances:
            child_module = _select_netlist_ir_symbol(
                index.modules_by_name,
                index.modules_by_key,
                instance.ref,
                instance.ref_file_id,
            )
            if child_module is not None:
                _visit(child_module)

    _visit(top_module)
    return sorted(
        reachable_by_key.values(),
        key=lambda module: module_order.get(_module_key_ir(module), len(design.modules)),
    )


def _emit_netlist_ir_module(
    module: NetlistModule,
    symbols: _NetlistIRSymbolMaps,
    *,
    is_top: bool,
    options: "EmitOptions",
    diagnostics: List[Diagnostic],
) -> Tuple[List[str], bool]:
    """Render a NetlistIR module definition."""
    lines: List[str] = []
    had_error = False

    pattern_table = module.pattern_expression_table
    pattern_rendering = options.backend_config.pattern_rendering
    net_name_map = _build_net_name_map_ir(module, pattern_table, pattern_rendering)
    ports = [net_name_map.get(port, port) for port in module.ports]

    module_name = _module_emitted_name_ir(module, symbols.module_emitted_names)
    module_params = _dict_attr_to_strings(module.parameters)
    module_params_str = _format_params_tokens(module_params)
    if not (is_top and not options.top_as_subckt):
        header_context = {
            "name": module_name,
            "sym_name": module.name,
            "ports": " ".join(ports),
            "params": module_params_str,
            "file_id": module.file_id or "",
        }
        header_template = (
            "__subckt_header_params__" if module_params_str else "__subckt_header__"
        )
        header, header_error = _render_system_device(
            header_template,
            options.backend_config,
            header_context,
            diagnostics,
        )
        if header:
            lines.append(header)
        had_error = had_error or header_error

    for instance in module.instances:
        line, inst_error = _emit_netlist_ir_instance(
            instance,
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
            "sym_name": module.name,
            "file_id": module.file_id or "",
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


def _emit_netlist_ir_instance(
    instance: NetlistInstance,
    symbols: _NetlistIRSymbolMaps,
    *,
    options: "EmitOptions",
    diagnostics: List[Diagnostic],
    net_name_map: Optional[Mapping[str, str]] = None,
    pattern_table: Optional[NetlistPatternExpressionTable] = None,
) -> Tuple[Optional[str], bool]:
    """Render a NetlistIR instance line."""
    instance_name = _render_pattern_name_ir(
        instance.name,
        instance.pattern_origin,
        pattern_table,
        "inst",
        options.backend_config.pattern_rendering,
    )
    ref_name = instance.ref
    ref_file_id = instance.ref_file_id
    module = _select_netlist_ir_symbol(
        symbols.index.modules_by_name,
        symbols.index.modules_by_key,
        ref_name,
        ref_file_id,
    )
    if module is not None:
        conns, had_error = _ordered_conns_netlist_ir(
            instance,
            module.ports,
            diagnostics,
            net_name_map=net_name_map,
        )
        if had_error:
            return None, True

        ref_name = _module_emitted_name_ir(module, symbols.module_emitted_names)
        call_context = {
            "name": instance_name,
            "ports": " ".join(conns),
            "ref": ref_name,
            "params": _format_params_tokens(_dict_attr_to_strings(instance.params)),
            "sym_name": module.name,
            "file_id": module.file_id or "",
        }
        call_template = (
            "__subckt_call_params__" if call_context["params"] else "__subckt_call__"
        )
        return _render_system_device(
            call_template,
            options.backend_config,
            call_context,
            diagnostics,
        )

    device = _select_netlist_ir_symbol(
        symbols.index.devices_by_name,
        symbols.index.devices_by_key,
        ref_name,
        ref_file_id,
    )
    if device is None:
        diagnostics.append(
            _diagnostic(
                UNKNOWN_REFERENCE,
                f"Instance '{instance.name}' references unknown symbol '{ref_name}'",
                Severity.ERROR,
                None,
                help=(
                    "Check that the symbol is defined or imported; use `ns.symbol` "
                    "for imported definitions."
                ),
            )
        )
        return None, True

    backend = _select_netlist_backend(device, options.backend_name)
    if backend is None:
        diagnostics.append(
            _diagnostic(
                MISSING_BACKEND,
                f"Device '{ref_name}' has no backend '{options.backend_name}'",
                Severity.ERROR,
                None,
            )
        )
        return None, True

    conns, had_error = _ordered_conns_netlist_ir(
        instance,
        device.ports,
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
        instance_name=instance.name,
        device_name=ref_name,
        loc=None,
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
        instance_name=instance.name,
        device_name=ref_name,
        device_loc=None,
        backend_loc=None,
        instance_loc=None,
    )
    diagnostics.extend(variable_diags)
    if any(
        diag.severity in (Severity.ERROR, Severity.FATAL) for diag in variable_diags
    ):
        return None, True

    template = backend.template
    escaped_template, env_vars = _escape_braced_env_vars(template)
    placeholders = _validate_template(template, ref_name, diagnostics, loc=None)
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
                None,
            )
        )
        return None, True
    except ValueError as exc:
        diagnostics.append(
            _diagnostic(
                MALFORMED_TEMPLATE,
                f"Backend template for '{ref_name}' is malformed: {exc}",
                Severity.ERROR,
                None,
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
                None,
            )
        )
        return None, True
    return rendered, False


def _select_netlist_backend(
    device: NetlistDevice, backend_name: str
) -> Optional[NetlistBackend]:
    """Select a NetlistIR backend definition by name."""
    for backend in device.backends:
        if backend.name == backend_name:
            return backend
    return None


def _render_pattern_origin_ir(
    origin: NetlistPatternOrigin, pattern_rendering: str
) -> str:
    """Render a NetlistIR pattern origin into a display name."""
    rendered_parts: list[str] = []
    for part in origin.pattern_parts:
        if isinstance(part, int):
            rendered_parts.append(_render_numeric_part(part, pattern_rendering))
        else:
            rendered_parts.append(str(part))
    return f"{origin.base_name}{''.join(rendered_parts)}"


def _render_numeric_part(value: int, pattern_rendering: str) -> str:
    """Render numeric pattern parts using the backend formatting policy."""
    if not isinstance(pattern_rendering, str):
        return str(value)
    if "{N" not in pattern_rendering:
        return str(value)
    try:
        return pattern_rendering.format_map({"N": value})
    except (KeyError, ValueError):
        return str(value)


def _render_pattern_name_ir(
    literal_name: str,
    origin: Optional[NetlistPatternOrigin],
    pattern_table: Optional[NetlistPatternExpressionTable],
    expected_kind: str,
    pattern_rendering: str,
) -> str:
    """Render a NetlistIR pattern-origin name when metadata is valid."""
    if origin is None or pattern_table is None:
        return literal_name
    entry = pattern_table.get(origin.expression_id)
    if entry is None or entry.kind != expected_kind:
        return literal_name
    try:
        return _render_pattern_origin_ir(origin, pattern_rendering)
    except (TypeError, ValueError):
        return literal_name


def _build_net_name_map_ir(
    module: NetlistModule,
    pattern_table: Optional[NetlistPatternExpressionTable],
    pattern_rendering: str,
) -> Dict[str, str]:
    """Build a mapping of literal net names to rendered display names."""
    name_map: Dict[str, str] = {}
    for net in module.nets:
        literal = net.name
        name_map[literal] = _render_pattern_name_ir(
            literal,
            net.pattern_origin,
            pattern_table,
            "net",
            pattern_rendering,
        )
    return name_map
def _emit_timestamp_context(emit_timestamp) -> Dict[str, str]:
    return {
        "emit_date": emit_timestamp.strftime("%Y-%m-%d"),
        "emit_time": emit_timestamp.strftime("%H:%M:%S"),
    }


def _entry_file_id_value_ir(
    entry_file_id: Optional[str], top_module: NetlistModule
) -> str:
    if _has_known_file_id(entry_file_id):
        return entry_file_id
    if _has_known_file_id(top_module.file_id):
        return top_module.file_id
    return ""


def _format_params_tokens(params: Mapping[str, str]) -> str:
    """Render deterministic `key=value` params using existing token ordering."""
    tokens = [f"{key}={params[key]}" for key in params]
    return " ".join(tokens)


def _module_key_ir(module: NetlistModule) -> int:
    return id(module)


def _realization_name_from_symbol(symbol: str) -> str:
    """Map a module symbol (`cell` or `cell@view`) to emitted realization name."""
    match = _MODULE_SYMBOL_PATTERN.fullmatch(symbol)
    if match is not None:
        cell = match.group("cell")
        view = match.group("view")
        if view is None or view == "default":
            return cell
        return f"{cell}_{_sanitize_realization_token(view)}"
    if symbol.count("@") == 1:
        cell, _, view = symbol.partition("@")
        cell_token = _sanitize_realization_token(cell)
        if view == "" or view == "default":
            return cell_token
        return f"{cell_token}_{_sanitize_realization_token(view)}"
    return _sanitize_realization_token(symbol.replace("@", "_"))


def _sanitize_realization_token(value: str) -> str:
    """Sanitize one realization token for simulator-facing symbol names."""
    sanitized = _SANITIZE_TOKEN_PATTERN.sub("_", value).strip("_")
    if sanitized:
        return sanitized
    return "view"


def _build_module_emitted_names_ir(
    modules: List[NetlistModule],
    diagnostics: Optional[List[Diagnostic]] = None,
) -> Dict[int, str]:
    used_names: set[str] = set()
    next_suffix_by_base: Dict[str, int] = {}
    emitted_names: Dict[int, str] = {}
    for module in modules:
        module_key = _module_key_ir(module)
        base_name = _realization_name_from_symbol(module.name)
        emitted = base_name
        if emitted in used_names:
            next_suffix = next_suffix_by_base.get(base_name, 2)
            while f"{base_name}__{next_suffix}" in used_names:
                next_suffix += 1
            emitted = f"{base_name}__{next_suffix}"
            next_suffix_by_base[base_name] = next_suffix + 1
            if diagnostics is not None:
                file_id_suffix = f" (file '{module.file_id}')" if module.file_id else ""
                diagnostics.append(
                    _diagnostic(
                        EMISSION_NAME_COLLISION,
                        (
                            f"Module symbol '{module.name}'{file_id_suffix} emits as "
                            f"'{emitted}' after collision on base name '{base_name}'."
                        ),
                        Severity.WARNING,
                    )
                )
        else:
            next_suffix_by_base.setdefault(base_name, 2)
        used_names.add(emitted)
        emitted_names[module_key] = emitted
    return emitted_names


def _module_emitted_name_ir(
    module: NetlistModule, emitted_names: Dict[int, str]
) -> str:
    return emitted_names.get(_module_key_ir(module), module.name)


def _emit_provenance_diagnostics_ir(
    modules: List[NetlistModule],
    design: NetlistDesign,
    index: "NetlistIRIndex",
    top_module: NetlistModule,
    diagnostics: List[Diagnostic],
) -> None:
    """Warn when module/file provenance metadata is missing or unknown."""
    if not _has_known_file_id(design.entry_file_id):
        fallback = _entry_file_id_value_ir(design.entry_file_id, top_module)
        if fallback:
            fallback_desc = f"top module file_id '{fallback}'"
        else:
            fallback_desc = "empty string"
        diagnostics.append(
            _diagnostic(
                PROVENANCE_METADATA_WARNING,
                (
                    "Design entry_file_id is missing; __netlist_header__/__netlist_footer__ "
                    f"{{file_id}} uses {fallback_desc}."
                ),
                Severity.WARNING,
            )
        )

    for module in modules:
        if _has_known_file_id(module.file_id):
            continue
        diagnostics.append(
            _diagnostic(
                PROVENANCE_METADATA_WARNING,
                (
                    f"Module symbol '{module.name}' has missing file_id provenance; "
                    "__subckt_header__ {file_id} emits as empty string."
                ),
                Severity.WARNING,
            )
        )

    for module in modules:
        for instance in module.instances:
            ref_name = instance.ref
            ref_file_id = instance.ref_file_id
            module_candidates = index.modules_by_name.get(ref_name, [])
            device_candidates = index.devices_by_name.get(ref_name, [])
            if _has_known_file_id(ref_file_id):
                has_exact = (ref_file_id, ref_name) in index.modules_by_key or (
                    ref_file_id,
                    ref_name,
                ) in index.devices_by_key
                if has_exact or (not module_candidates and not device_candidates):
                    continue
                diagnostics.append(
                    _diagnostic(
                        PROVENANCE_METADATA_WARNING,
                        (
                            f"Instance '{module.name}.{instance.name}' declares unknown "
                            f"ref_file_id '{ref_file_id}' for symbol '{ref_name}'."
                        ),
                        Severity.WARNING,
                    )
                )
                continue

            if not module_candidates and not device_candidates:
                diagnostics.append(
                    _diagnostic(
                        PROVENANCE_METADATA_WARNING,
                        (
                            f"Instance '{module.name}.{instance.name}' is missing "
                            f"ref_file_id for symbol '{ref_name}'."
                        ),
                        Severity.WARNING,
                    )
                )
                continue

            candidate_count = len(module_candidates) + len(device_candidates)
            if candidate_count > 1:
                diagnostics.append(
                    _diagnostic(
                        PROVENANCE_METADATA_WARNING,
                        (
                            f"Instance '{module.name}.{instance.name}' is missing "
                            f"ref_file_id for symbol '{ref_name}'; "
                            "name-only fallback is ambiguous and resolves "
                            "deterministically by declaration order."
                        ),
                        Severity.WARNING,
                    )
                )


def build_emission_name_map(design: NetlistDesign) -> List[EmissionNameMapEntry]:
    """Build deterministic logical/base/emitted module-name mapping entries."""
    modules_for_mapping = _collect_reachable_modules_for_mapping_ir(design)
    emitted_names = _build_module_emitted_names_ir(modules_for_mapping, diagnostics=None)
    entries: List[EmissionNameMapEntry] = []
    for module in modules_for_mapping:
        base_name = _realization_name_from_symbol(module.name)
        emitted_name = emitted_names[_module_key_ir(module)]
        entries.append(
            EmissionNameMapEntry(
                symbol=module.name,
                file_id=module.file_id,
                base_name=base_name,
                emitted_name=emitted_name,
                renamed=emitted_name != base_name,
            )
        )
    return entries


def _collect_reachable_modules_for_mapping_ir(design: NetlistDesign) -> List[NetlistModule]:
    """Collect modules to include in compile-log emission-name mapping.

    This mirrors emission scoping: map entries and collision allocation are
    based on modules reachable from the final resolved top realization.
    """
    collector = DiagnosticCollector()
    index = _build_netlist_ir_index(design, collector)
    if index is None:
        return list(design.modules)

    top_module = _select_netlist_ir_symbol(
        index.modules_by_name,
        index.modules_by_key,
        index.top_name,
        index.top_file_id,
    )
    if top_module is None:
        return list(design.modules)

    return _collect_reachable_modules_ir(design, index, top_module)


def _ordered_conns_netlist_ir(
    instance: NetlistInstance,
    port_order: Iterable[str],
    diagnostics: DiagnosticCollector | List[Diagnostic],
    *,
    net_name_map: Optional[Mapping[str, str]] = None,
) -> Tuple[List[str], bool]:
    """Order NetlistIR conns by port list while validating port usage."""
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

    placeholders = _validate_template(template, device_name, diagnostics)
    if placeholders is None:
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
    if "params" in placeholders and context.get("params", "") == "":
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
