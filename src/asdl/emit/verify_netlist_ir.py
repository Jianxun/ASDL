"""Stateless verification helpers for NetlistIR designs."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from asdl.diagnostics import Diagnostic, DiagnosticCollector, Severity, format_code
from asdl.emit.netlist_ir import (
    NetlistDesign,
    NetlistDevice,
    NetlistInstance,
    NetlistModule,
    PatternExpressionEntry,
    PatternOrigin,
)
from asdl.ir.patterns.tokenize import _has_pattern_delimiters

NO_SPAN_NOTE = "No source span available."

INVALID_LITERAL_NAME = format_code("IR", 50)
DUPLICATE_NET_NAME = format_code("IR", 51)
DUPLICATE_INSTANCE_NAME = format_code("IR", 52)
UNKNOWN_CONN_TARGET = format_code("IR", 53)
INVALID_PORT_LIST = format_code("IR", 54)
INVALID_PATTERN_ORIGIN = format_code("IR", 55)
DUPLICATE_BACKEND_NAME = format_code("IR", 56)


def verify_netlist_ir(design: NetlistDesign) -> list[Diagnostic]:
    """Verify NetlistIR invariants and return diagnostics.

    Args:
        design: NetlistIR design to verify.

    Returns:
        Diagnostics emitted during verification.
    """
    diagnostics = DiagnosticCollector()
    for device in design.devices:
        _verify_unique_backend_names(device, diagnostics)
    for module in design.modules:
        net_names = _collect_names(net.name for net in module.nets)
        _verify_literal_names(module, diagnostics)
        _verify_unique_net_names(module, diagnostics)
        _verify_unique_instance_names(module, diagnostics)
        _verify_ports_list(module, net_names, diagnostics)
        _verify_connections(module, net_names, diagnostics)
        _verify_pattern_origins(module, diagnostics)
    return diagnostics.to_list()


def _verify_literal_names(
    module: NetlistModule,
    diagnostics: DiagnosticCollector,
) -> None:
    """Emit diagnostics for non-literal NetlistIR names.

    Args:
        module: Module to inspect.
        diagnostics: Diagnostic collector to append to.
    """
    for net in module.nets:
        if not _is_literal_name(net.name, allow_leading_dollar=False):
            diagnostics.emit(
                _diagnostic(
                    INVALID_LITERAL_NAME,
                    (
                        f"Net name '{net.name}' in module '{module.name}' must be "
                        "a literal name"
                    ),
                )
            )
    for port in module.ports:
        if not _is_literal_name(port, allow_leading_dollar=False):
            diagnostics.emit(
                _diagnostic(
                    INVALID_LITERAL_NAME,
                    (
                        f"Port name '{port}' in module '{module.name}' must be "
                        "a literal name"
                    ),
                )
            )
    for instance in module.instances:
        if not _is_literal_name(instance.name, allow_leading_dollar=False):
            diagnostics.emit(
                _diagnostic(
                    INVALID_LITERAL_NAME,
                    (
                        f"Instance name '{instance.name}' in module "
                        f"'{module.name}' must be a literal name"
                    ),
                )
            )
        if not _is_literal_name(instance.ref, allow_leading_dollar=False):
            diagnostics.emit(
                _diagnostic(
                    INVALID_LITERAL_NAME,
                    (
                        f"Instance '{instance.name}' in module '{module.name}' "
                        f"references non-literal symbol '{instance.ref}'"
                    ),
                )
            )
        for conn in instance.conns:
            if not _is_literal_name(conn.port, allow_leading_dollar=False):
                diagnostics.emit(
                    _diagnostic(
                        INVALID_LITERAL_NAME,
                        (
                            f"Instance '{instance.name}' in module '{module.name}' "
                            f"uses non-literal port name '{conn.port}'"
                        ),
                    )
                )


def _verify_unique_net_names(
    module: NetlistModule,
    diagnostics: DiagnosticCollector,
) -> None:
    """Emit diagnostics for duplicate net names within a module.

    Args:
        module: Module to inspect.
        diagnostics: Diagnostic collector to append to.
    """
    duplicates = _find_duplicates(net.name for net in module.nets)
    for name, count in duplicates.items():
        diagnostics.emit(
            _diagnostic(
                DUPLICATE_NET_NAME,
                (
                    f"Net name '{name}' appears {count} times in module "
                    f"'{module.name}'."
                ),
            )
        )


def _verify_unique_instance_names(
    module: NetlistModule,
    diagnostics: DiagnosticCollector,
) -> None:
    """Emit diagnostics for duplicate instance names within a module.

    Args:
        module: Module to inspect.
        diagnostics: Diagnostic collector to append to.
    """
    duplicates = _find_duplicates(inst.name for inst in module.instances)
    for name, count in duplicates.items():
        diagnostics.emit(
            _diagnostic(
                DUPLICATE_INSTANCE_NAME,
                (
                    f"Instance name '{name}' appears {count} times in module "
                    f"'{module.name}'."
                ),
            )
        )


def _verify_unique_backend_names(
    device: NetlistDevice,
    diagnostics: DiagnosticCollector,
) -> None:
    """Emit diagnostics for duplicate backend names within a device.

    Args:
        device: Device to inspect.
        diagnostics: Diagnostic collector to append to.
    """
    duplicates = _find_duplicates(backend.name for backend in device.backends)
    for name, count in duplicates.items():
        diagnostics.emit(
            _diagnostic(
                DUPLICATE_BACKEND_NAME,
                (
                    f"Backend name '{name}' appears {count} times in device "
                    f"'{device.name}'."
                ),
            )
        )


def _verify_connections(
    module: NetlistModule,
    net_names: set[str],
    diagnostics: DiagnosticCollector,
) -> None:
    """Emit diagnostics for invalid connection targets.

    Args:
        module: Module to inspect.
        net_names: Known net names in the module.
        diagnostics: Diagnostic collector to append to.
    """
    for instance in module.instances:
        seen_ports: set[str] = set()
        for conn in instance.conns:
            if conn.port in seen_ports:
                diagnostics.emit(
                    _diagnostic(
                        UNKNOWN_CONN_TARGET,
                        (
                            f"Instance '{instance.name}' in module '{module.name}' "
                            f"has duplicate port '{conn.port}'"
                        ),
                    )
                )
                continue
            seen_ports.add(conn.port)
            if conn.net not in net_names:
                diagnostics.emit(
                    _diagnostic(
                        UNKNOWN_CONN_TARGET,
                        (
                            f"Instance '{instance.name}' in module '{module.name}' "
                            f"references unknown net '{conn.net}'"
                        ),
                    )
                )


def _verify_ports_list(
    module: NetlistModule,
    net_names: set[str],
    diagnostics: DiagnosticCollector,
) -> None:
    """Emit diagnostics for invalid module port lists.

    Args:
        module: Module to inspect.
        net_names: Known net names in the module.
        diagnostics: Diagnostic collector to append to.
    """
    if not module.ports:
        return
    if len(module.ports) != len(set(module.ports)):
        diagnostics.emit(
            _diagnostic(
                INVALID_PORT_LIST,
                f"Module '{module.name}' port list contains duplicate names.",
            )
        )
    missing = [name for name in module.ports if name not in net_names]
    if missing:
        missing_names = ", ".join(missing)
        diagnostics.emit(
            _diagnostic(
                INVALID_PORT_LIST,
                (
                    f"Module '{module.name}' port list references missing nets: "
                    f"{missing_names}."
                ),
            )
        )


def _verify_pattern_origins(
    module: NetlistModule,
    diagnostics: DiagnosticCollector,
) -> None:
    """Emit diagnostics for invalid pattern origin metadata.

    Args:
        module: Module to inspect.
        diagnostics: Diagnostic collector to append to.
    """
    pattern_table = module.pattern_expression_table
    if not _module_has_pattern_origins(module):
        return
    if pattern_table is None:
        diagnostics.emit(
            _diagnostic(
                INVALID_PATTERN_ORIGIN,
                (
                    f"Module '{module.name}' is missing pattern_expression_table "
                    "for pattern-origin metadata."
                ),
            )
        )
        return
    for net in module.nets:
        _verify_pattern_origin_entry(
            module,
            net.pattern_origin,
            pattern_table,
            expected_kind="net",
            label=f"net '{net.name}'",
            diagnostics=diagnostics,
        )
    for instance in module.instances:
        _verify_pattern_origin_entry(
            module,
            instance.pattern_origin,
            pattern_table,
            expected_kind="inst",
            label=f"instance '{instance.name}'",
            diagnostics=diagnostics,
        )


def _verify_pattern_origin_entry(
    module: NetlistModule,
    origin: PatternOrigin | None,
    pattern_table: dict[str, PatternExpressionEntry],
    expected_kind: str,
    label: str,
    diagnostics: DiagnosticCollector,
) -> None:
    if origin is None:
        return
    entry = pattern_table.get(origin.expression_id)
    if entry is None:
        diagnostics.emit(
            _diagnostic(
                INVALID_PATTERN_ORIGIN,
                (
                    f"Module '{module.name}' pattern_origin for {label} references "
                    f"missing expression id '{origin.expression_id}'."
                ),
            )
        )
        return
    if entry.kind != expected_kind:
        diagnostics.emit(
            _diagnostic(
                INVALID_PATTERN_ORIGIN,
                (
                    f"Module '{module.name}' pattern_origin kind mismatch for {label}: "
                    f"expected '{expected_kind}', got '{entry.kind}'."
                ),
            )
        )


def _module_has_pattern_origins(module: NetlistModule) -> bool:
    for net in module.nets:
        if net.pattern_origin is not None:
            return True
    for instance in module.instances:
        if instance.pattern_origin is not None:
            return True
    return False


def _collect_names(names: Iterable[str]) -> set[str]:
    return {name for name in names}


def _find_duplicates(names: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for name in names:
        counts[name] += 1
    return {name: count for name, count in counts.items() if count > 1}


def _is_literal_name(name: str, *, allow_leading_dollar: bool) -> bool:
    if not name:
        return False
    if _has_pattern_delimiters(name):
        return False
    if not allow_leading_dollar and name.startswith("$"):
        return False
    return True


def _diagnostic(code: str, message: str) -> Diagnostic:
    """Create an error diagnostic without a source span.

    Args:
        code: Diagnostic code.
        message: Diagnostic message.

    Returns:
        Diagnostic with error severity and fallback note.
    """
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        message=message,
        primary_span=None,
        notes=[NO_SPAN_NOTE],
        source="emit",
    )


__all__ = [
    "DUPLICATE_INSTANCE_NAME",
    "DUPLICATE_BACKEND_NAME",
    "DUPLICATE_NET_NAME",
    "INVALID_LITERAL_NAME",
    "INVALID_PATTERN_ORIGIN",
    "INVALID_PORT_LIST",
    "UNKNOWN_CONN_TARGET",
    "verify_netlist_ir",
]
