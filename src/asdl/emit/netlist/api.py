from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import yaml

from asdl.diagnostics import Diagnostic, Severity
from asdl.emit.backend_config import BackendConfig, load_backend_config
from asdl.ir import convert_graphir_to_ifir
from asdl.ir.graphir import ProgramOp as GraphProgramOp
from asdl.ir.ifir import DesignOp

from .diagnostics import MISSING_BACKEND, _diagnostic, _has_error_diagnostics
from .render import _emit_design
from .verify import _run_netlist_verification


@dataclass(frozen=True)
class EmitOptions:
    top_as_subckt: bool = False
    backend_name: str = "sim.ngspice"
    backend_config: Optional[BackendConfig] = None
    emit_timestamp: datetime = field(default_factory=datetime.now)


def load_backend(
    backend_name: str, backend_config_path: Optional[Path] = None
) -> Tuple[Optional[BackendConfig], List[Diagnostic]]:
    diagnostics: List[Diagnostic] = []
    try:
        config = load_backend_config(backend_name, backend_config_path)
    except (FileNotFoundError, KeyError, TypeError, yaml.YAMLError) as exc:
        diagnostics.append(
            _diagnostic(
                MISSING_BACKEND,
                f"Failed to load backend config: {exc}",
                Severity.ERROR,
            )
        )
        return None, diagnostics
    return config, diagnostics


def emit_netlist(
    design: DesignOp | GraphProgramOp,
    *,
    backend_name: str = "sim.ngspice",
    top_as_subckt: bool = False,
    backend_config_path: Optional[Path] = None,
    backend_config: Optional[BackendConfig] = None,
    emit_timestamp: Optional[datetime] = None,
) -> Tuple[Optional[str], List[Diagnostic]]:
    diagnostics: List[Diagnostic] = []

    if backend_config is None:
        backend_config, backend_diags = load_backend(
            backend_name, backend_config_path
        )
        diagnostics.extend(backend_diags)
        if backend_config is None:
            return None, diagnostics

    if isinstance(design, GraphProgramOp):
        design, graphir_diags = convert_graphir_to_ifir(design)
        diagnostics.extend(graphir_diags)
        if design is None:
            return None, diagnostics

    verify_diags = _run_netlist_verification(
        design, backend_name=backend_name, backend_config=backend_config
    )
    diagnostics.extend(verify_diags)
    if _has_error_diagnostics(diagnostics):
        return None, diagnostics

    options = EmitOptions(
        top_as_subckt=top_as_subckt,
        backend_name=backend_name,
        backend_config=backend_config,
        emit_timestamp=emit_timestamp or datetime.now(),
    )
    netlist, emit_diags = _emit_design(design, options)
    diagnostics.extend(emit_diags)
    if netlist is None or _has_error_diagnostics(diagnostics):
        return None, diagnostics

    return netlist, diagnostics
