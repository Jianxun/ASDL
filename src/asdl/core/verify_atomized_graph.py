"""Stateless verification helpers for AtomizedGraph programs."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Optional

from asdl.core.atomized_graph import (
    AtomizedInstance,
    AtomizedModuleGraph,
    AtomizedProgramGraph,
)
from asdl.diagnostics import Diagnostic, DiagnosticCollector, Severity, format_code

NO_SPAN_NOTE = "No source span available."

DUPLICATE_NET_NAME = format_code("IR", 30)
DUPLICATE_INSTANCE_NAME = format_code("IR", 31)
UNKNOWN_ENDPOINT_REF = format_code("IR", 32)
UNKNOWN_ENDPOINT_PORT = format_code("IR", 33)


def verify_atomized_graph(program: AtomizedProgramGraph) -> list[Diagnostic]:
    """Verify AtomizedGraph invariants and return diagnostics.

    Args:
        program: Atomized program graph to verify.

    Returns:
        Diagnostics emitted during verification.
    """
    diagnostics = DiagnosticCollector()
    for module in program.modules.values():
        _verify_unique_net_names(module, diagnostics)
        _verify_unique_instance_names(module, diagnostics)
        _verify_endpoints(module, program, diagnostics)
    return diagnostics.to_list()


def verify_atomized_graph_if_clean(
    program: AtomizedProgramGraph,
    diagnostics: Iterable[Diagnostic],
) -> list[Diagnostic]:
    """Verify AtomizedGraph only when no error diagnostics are present.

    Args:
        program: Atomized program graph to verify.
        diagnostics: Existing diagnostics to respect for gating.

    Returns:
        Original diagnostics plus verification diagnostics when no errors exist.
    """
    existing = list(diagnostics)
    if _has_error_diagnostics(existing):
        return existing
    return [*existing, *verify_atomized_graph(program)]


def _verify_unique_net_names(
    module: AtomizedModuleGraph,
    diagnostics: DiagnosticCollector,
) -> None:
    """Emit diagnostics for duplicate net names within a module.

    Args:
        module: Module graph to inspect.
        diagnostics: Diagnostic collector to append to.
    """
    names: dict[str, list[str]] = defaultdict(list)
    for net_id, net in module.nets.items():
        names[net.name].append(net_id)
    for name, net_ids in names.items():
        if len(net_ids) > 1:
            diagnostics.emit(
                _diagnostic(
                    DUPLICATE_NET_NAME,
                    (
                        f"Net name '{name}' appears {len(net_ids)} times in "
                        f"module '{module.name}'."
                    ),
                )
            )


def _verify_unique_instance_names(
    module: AtomizedModuleGraph,
    diagnostics: DiagnosticCollector,
) -> None:
    """Emit diagnostics for duplicate instance names within a module.

    Args:
        module: Module graph to inspect.
        diagnostics: Diagnostic collector to append to.
    """
    names: dict[str, list[str]] = defaultdict(list)
    for inst_id, inst in module.instances.items():
        names[inst.name].append(inst_id)
    for name, inst_ids in names.items():
        if len(inst_ids) > 1:
            diagnostics.emit(
                _diagnostic(
                    DUPLICATE_INSTANCE_NAME,
                    (
                        f"Instance name '{name}' appears {len(inst_ids)} times "
                        f"in module '{module.name}'."
                    ),
                )
            )


def _verify_endpoints(
    module: AtomizedModuleGraph,
    program: AtomizedProgramGraph,
    diagnostics: DiagnosticCollector,
) -> None:
    """Emit diagnostics for invalid endpoint references and ports.

    Args:
        module: Module graph to inspect.
        program: Program graph containing module and device definitions.
        diagnostics: Diagnostic collector to append to.
    """
    for endpoint_id, endpoint in module.endpoints.items():
        if endpoint.net_id not in module.nets:
            diagnostics.emit(
                _diagnostic(
                    UNKNOWN_ENDPOINT_REF,
                    (
                        f"Endpoint '{endpoint_id}' in module '{module.name}' "
                        f"references unknown net id '{endpoint.net_id}'."
                    ),
                )
            )
        instance = module.instances.get(endpoint.inst_id)
        if instance is None:
            diagnostics.emit(
                _diagnostic(
                    UNKNOWN_ENDPOINT_REF,
                    (
                        f"Endpoint '{endpoint_id}' in module '{module.name}' "
                        f"references unknown instance id '{endpoint.inst_id}'."
                    ),
                )
            )
            continue
        ports = _resolve_instance_ports(program, instance)
        if ports is None:
            diagnostics.emit(
                _diagnostic(
                    UNKNOWN_ENDPOINT_PORT,
                    (
                        f"Endpoint '{endpoint_id}' in module '{module.name}' "
                        f"references missing {instance.ref_kind} id "
                        f"'{instance.ref_id}'."
                    ),
                )
            )
            continue
        if endpoint.port not in ports:
            diagnostics.emit(
                _diagnostic(
                    UNKNOWN_ENDPOINT_PORT,
                    (
                        f"Endpoint '{endpoint_id}' in module '{module.name}' "
                        f"uses unknown port '{endpoint.port}' for instance "
                        f"'{instance.name}'."
                    ),
                )
            )


def _resolve_instance_ports(
    program: AtomizedProgramGraph,
    instance: AtomizedInstance,
) -> Optional[list[str]]:
    """Resolve the port list for an instance reference.

    Args:
        program: Atomized program graph containing definitions.
        instance: Atomized instance to resolve.

    Returns:
        List of ports for the referenced module/device, or None if missing.
    """
    if instance.ref_kind == "module":
        module = program.modules.get(instance.ref_id)
        if module is None:
            return None
        return list(module.ports or [])
    device = program.devices.get(instance.ref_id)
    if device is None:
        return None
    return list(device.ports or [])


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
        source="core",
    )


def _has_error_diagnostics(diagnostics: Iterable[Diagnostic]) -> bool:
    """Return True when any diagnostics are errors or fatals.

    Args:
        diagnostics: Diagnostics to scan.

    Returns:
        True when an error or fatal diagnostic is present.
    """
    return any(
        diagnostic.severity in (Severity.ERROR, Severity.FATAL)
        for diagnostic in diagnostics
    )


__all__ = [
    "DUPLICATE_INSTANCE_NAME",
    "DUPLICATE_NET_NAME",
    "UNKNOWN_ENDPOINT_PORT",
    "UNKNOWN_ENDPOINT_REF",
    "verify_atomized_graph",
    "verify_atomized_graph_if_clean",
]
