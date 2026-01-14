"""AST to GraphIR conversion for a single ASDL document."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Set, Tuple

from xdsl.dialects.builtin import DictionaryAttr, StringAttr

from asdl.ast import AsdlDocument, DeviceDecl, ModuleDecl
from asdl.ast.location import Locatable
from asdl.diagnostics import Diagnostic, Severity, format_code
from asdl.imports import NameEnv, ProgramDB
from asdl.ir.graphir import DeviceOp, EndpointOp, InstanceOp, ModuleOp, NetOp, ProgramOp

INVALID_INSTANCE_EXPR = format_code("IR", 1)
INVALID_ENDPOINT_EXPR = format_code("IR", 2)
UNRESOLVED_QUALIFIED = format_code("IR", 10)
UNRESOLVED_UNQUALIFIED = format_code("IR", 11)
NO_SPAN_NOTE = "No source span available."


@dataclass(frozen=True)
class _ResolvedSymbol:
    """Resolved symbol metadata for GraphIR instance references.

    Args:
        kind: Symbol kind ("module" or "device").
        sym_id: Stable symbol identifier.
    """

    kind: str
    sym_id: str


class _GraphIdAllocator:
    """Deterministic ID generator for GraphIR entities.

    IDs are scoped by a prefix to preserve readability while keeping string
    values stable across a single conversion.
    """

    def __init__(self) -> None:
        self._counts: Dict[str, int] = {}

    def next(self, prefix: str) -> str:
        """Return the next ID for a given prefix.

        Args:
            prefix: Prefix indicating the entity type.

        Returns:
            The next stable ID string.
        """
        count = self._counts.get(prefix, 0) + 1
        self._counts[prefix] = count
        return f"{prefix}{count}"


def convert_document(
    document: AsdlDocument,
    *,
    name_env: Optional[NameEnv] = None,
    program_db: Optional[ProgramDB] = None,
) -> Tuple[Optional[ProgramOp], List[Diagnostic]]:
    """Convert a single ASDL document into GraphIR.

    Args:
        document: Parsed AST document.
        name_env: Optional name environment for file identity.
        program_db: Optional program database (unused for local-only resolution).

    Returns:
        The GraphIR program op (or None on error) and diagnostics.
    """
    _ = program_db
    diagnostics: List[Diagnostic] = []
    had_error = False

    file_id = _resolve_file_id(document, name_env)
    id_allocator = _GraphIdAllocator()
    module_ids = {
        name: id_allocator.next("m") for name in (document.modules or {}).keys()
    }
    device_ids = {
        name: id_allocator.next("d") for name in (document.devices or {}).keys()
    }
    symbol_table = _build_symbol_table(module_ids, device_ids)

    modules: List[ModuleOp] = []
    for name, module in (document.modules or {}).items():
        module_op, module_diags, module_error = _convert_module(
            name,
            module,
            module_id=module_ids[name],
            file_id=file_id,
            symbol_table=symbol_table,
            id_allocator=id_allocator,
        )
        modules.append(module_op)
        diagnostics.extend(module_diags)
        had_error = had_error or module_error

    devices: List[DeviceOp] = []
    for name, device in (document.devices or {}).items():
        devices.append(
            _convert_device(
                name,
                device,
                device_id=device_ids[name],
                file_id=file_id,
            )
        )

    entry_id: Optional[str] = None
    if document.top is not None:
        entry_id = module_ids.get(document.top)
        if entry_id is None:
            diagnostics.append(
                _diagnostic(
                    UNRESOLVED_UNQUALIFIED,
                    f"Unresolved top module '{document.top}'.",
                    getattr(document, "_loc", None),
                )
            )
            had_error = True

    program = ProgramOp(region=modules + devices, entry=entry_id)
    if had_error:
        return None, diagnostics
    return program, diagnostics


def _convert_module(
    name: str,
    module: ModuleDecl,
    *,
    module_id: str,
    file_id: str,
    symbol_table: Dict[str, List[_ResolvedSymbol]],
    id_allocator: _GraphIdAllocator,
) -> Tuple[ModuleOp, List[Diagnostic], bool]:
    """Convert a module declaration into GraphIR.

    Args:
        name: Module name.
        module: Module declaration.
        module_id: Stable module identifier.
        file_id: Source file identifier.
        symbol_table: Mapping from symbol names to resolved IDs.
        id_allocator: Shared ID allocator.

    Returns:
        The module op, diagnostics, and error flag.
    """
    diagnostics: List[Diagnostic] = []
    had_error = False

    inst_ops: List[InstanceOp] = []
    inst_name_to_id: Dict[str, str] = {}
    if module.instances:
        for inst_name, expr in module.instances.items():
            inst_loc = module._instances_loc.get(inst_name)
            ref, params, parse_error = _parse_instance_expr(expr)
            if parse_error is not None:
                diagnostics.append(
                    _diagnostic(
                        INVALID_INSTANCE_EXPR,
                        f"{parse_error} in module '{name}'",
                        inst_loc or module._loc,
                    )
                )
                had_error = True
                continue
            if ref is None:
                diagnostics.append(
                    _diagnostic(
                        INVALID_INSTANCE_EXPR,
                        f"Instance expression missing reference in module '{name}'",
                        inst_loc or module._loc,
                    )
                )
                had_error = True
                continue
            resolved = _resolve_symbol_reference(
                ref,
                symbol_table,
                diagnostics,
                inst_loc or module._loc,
            )
            if resolved is None:
                had_error = True
                continue
            inst_id = id_allocator.next("i")
            inst_name_to_id[inst_name] = inst_id
            inst_ops.append(
                InstanceOp(
                    inst_id=inst_id,
                    name=inst_name,
                    module_ref=(resolved.kind, resolved.sym_id),
                    module_ref_raw=ref,
                    props=_to_string_dict_attr(params),
                )
            )

    net_ops: List[NetOp] = []
    port_order: List[str] = []
    if module.nets:
        for net_name, endpoint_expr in module.nets.items():
            net_loc = module._nets_loc.get(net_name)
            net_name, is_port = _split_net_token(net_name)
            if is_port and net_name not in port_order:
                port_order.append(net_name)

            endpoints, _suppressed, endpoint_error = _parse_endpoints(endpoint_expr)
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

            endpoint_ops: List[EndpointOp] = []
            for inst_name, port_path in endpoints:
                inst_id = inst_name_to_id.get(inst_name)
                if inst_id is None:
                    diagnostics.append(
                        _diagnostic(
                            INVALID_ENDPOINT_EXPR,
                            (
                                f"Unknown instance '{inst_name}' referenced by endpoint "
                                f"'{inst_name}.{port_path}' in module '{name}'"
                            ),
                            net_loc or module._loc,
                        )
                    )
                    had_error = True
                    continue
                endpoint_ops.append(
                    EndpointOp(
                        endpoint_id=id_allocator.next("e"),
                        inst_id=inst_id,
                        port_path=port_path,
                    )
                )

            net_ops.append(
                NetOp(
                    net_id=id_allocator.next("n"),
                    name=net_name,
                    region=endpoint_ops,
                )
            )

    ops: List[object] = []
    ops.extend(net_ops)
    ops.extend(inst_ops)
    return (
        ModuleOp(
            module_id=module_id,
            name=name,
            file_id=file_id,
            region=ops,
            port_order=port_order or None,
        ),
        diagnostics,
        had_error,
    )


def _convert_device(
    name: str,
    device: DeviceDecl,
    *,
    device_id: str,
    file_id: str,
) -> DeviceOp:
    """Convert a device declaration into GraphIR.

    Args:
        name: Device name.
        device: Device declaration.
        device_id: Stable device identifier.
        file_id: Source file identifier.

    Returns:
        The device op.
    """
    ports = device.ports or []
    return DeviceOp(
        device_id=device_id,
        name=name,
        file_id=file_id,
        ports=ports,
        params=_to_string_dict_attr(device.params),
        region=[],
    )


def _resolve_file_id(document: AsdlDocument, name_env: Optional[NameEnv]) -> str:
    """Resolve a file identifier for GraphIR metadata.

    Args:
        document: AST document to inspect for location metadata.
        name_env: Optional name environment for file identity.

    Returns:
        A file identifier string.
    """
    if name_env is not None:
        return str(name_env.file_id)
    loc = getattr(document, "_loc", None)
    if loc is not None and loc.file:
        return loc.file
    return "<string>"


def _build_symbol_table(
    module_ids: Dict[str, str],
    device_ids: Dict[str, str],
) -> Dict[str, List[_ResolvedSymbol]]:
    """Build a symbol table for local module/device names.

    Args:
        module_ids: Mapping from module names to IDs.
        device_ids: Mapping from device names to IDs.

    Returns:
        Mapping from symbol name to resolved symbol metadata.
    """
    table: Dict[str, List[_ResolvedSymbol]] = {}
    for name, module_id in module_ids.items():
        table.setdefault(name, []).append(_ResolvedSymbol("module", module_id))
    for name, device_id in device_ids.items():
        table.setdefault(name, []).append(_ResolvedSymbol("device", device_id))
    return table


def _resolve_symbol_reference(
    ref: str,
    symbol_table: Dict[str, List[_ResolvedSymbol]],
    diagnostics: List[Diagnostic],
    loc: Optional[Locatable],
) -> Optional[_ResolvedSymbol]:
    """Resolve an instance reference to a local symbol.

    Args:
        ref: Instance reference token.
        symbol_table: Mapping of local symbols.
        diagnostics: Diagnostic collection to append errors to.
        loc: Optional source location.

    Returns:
        Resolved symbol metadata or None if unresolved.
    """
    if "." in ref:
        diagnostics.append(
            _diagnostic(
                UNRESOLVED_QUALIFIED,
                f"Unresolved symbol '{ref}'.",
                loc,
            )
        )
        return None
    candidates = symbol_table.get(ref)
    if not candidates:
        diagnostics.append(
            _diagnostic(
                UNRESOLVED_UNQUALIFIED,
                f"Unresolved symbol '{ref}'.",
                loc,
            )
        )
        return None
    if len(candidates) > 1:
        diagnostics.append(
            _diagnostic(
                UNRESOLVED_UNQUALIFIED,
                f"Ambiguous symbol '{ref}' refers to multiple definitions.",
                loc,
            )
        )
        return None
    return candidates[0]


def _parse_instance_expr(expr: str) -> Tuple[Optional[str], Dict[str, str], Optional[str]]:
    """Parse an instance expression into a reference and params.

    Args:
        expr: Instance expression string.

    Returns:
        Tuple of (reference, params, error message).
    """
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
    expr: Sequence[str],
) -> Tuple[List[Tuple[str, str]], Set[Tuple[str, str]], Optional[str]]:
    """Parse endpoint expressions into (instance, port) pairs.

    Args:
        expr: Sequence of endpoint tokens.

    Returns:
        Tuple of endpoints, suppressed endpoint keys, and error message.
    """
    endpoints: List[Tuple[str, str]] = []
    suppressed: Set[Tuple[str, str]] = set()
    if isinstance(expr, str):
        return (
            [],
            suppressed,
            "Endpoint lists must be YAML lists of '<instance>.<pin>' strings",
        )
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
        endpoints.append((inst, pin))
        if suppress_override:
            suppressed.add((inst, pin))
    return endpoints, suppressed, None


def _split_net_token(net_token: str) -> Tuple[str, bool]:
    """Split a net token into name and port flag.

    Args:
        net_token: Net token, optionally prefixed with '$'.

    Returns:
        Tuple of (net name, is port).
    """
    if net_token.startswith("$"):
        return net_token[1:], True
    return net_token, False


def _to_string_dict_attr(
    values: Optional[Dict[str, object]],
) -> Optional[DictionaryAttr]:
    """Convert a dictionary to a DictionaryAttr of string values.

    Args:
        values: Optional parameter mapping.

    Returns:
        DictionaryAttr of StringAttr values or None.
    """
    if not values:
        return None
    items = {key: StringAttr(_format_param_value(value)) for key, value in values.items()}
    return DictionaryAttr(items)


def _format_param_value(value: object) -> str:
    """Format parameter values as strings.

    Args:
        value: Parameter value.

    Returns:
        Serialized string representation.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _diagnostic(
    code: str,
    message: str,
    loc: Optional[Locatable],
    severity: Severity = Severity.ERROR,
) -> Diagnostic:
    """Create a diagnostic from a source location.

    Args:
        code: Diagnostic code.
        message: Diagnostic message.
        loc: Optional source location.
        severity: Diagnostic severity.

    Returns:
        Diagnostic instance.
    """
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


__all__ = ["convert_document"]
