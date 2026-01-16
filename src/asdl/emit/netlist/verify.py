from __future__ import annotations

from dataclasses import dataclass
from typing import List

from xdsl.context import Context
from xdsl.dialects import builtin
from xdsl.passes import ModulePass, PassPipeline

from asdl.diagnostics import Diagnostic, Severity
from asdl.diagnostics.collector import DiagnosticCollector
from asdl.emit.backend_config import BackendConfig, validate_system_devices
from asdl.ir.ifir import ASDL_IFIR, DesignOp, InstanceOp

from .diagnostics import (
    MISSING_BACKEND,
    NETLIST_DESIGN_MISSING,
    NETLIST_VERIFY_CRASH,
    UNKNOWN_REFERENCE,
    _diagnostic,
)
from .ir_utils import (
    _collect_design_ops,
    _find_single_design,
    _resolve_top_name,
    _select_backend,
    _select_symbol,
)
from .render import _ordered_conns
from .params import _dict_attr_to_strings, _merge_variables
from .templates import (
    _allowed_backend_placeholders,
    _validate_system_device_templates,
    _validate_template,
)


@dataclass
class NetlistVerificationState:
    diagnostics: DiagnosticCollector
    backend_name: str
    backend_config: BackendConfig


@dataclass(frozen=True)
class VerifyNetlistPass(ModulePass):
    name = "verify-netlist"

    state: NetlistVerificationState

    def apply(self, ctx: Context, op: builtin.ModuleOp) -> None:
        design = _find_single_design(
            op,
            DesignOp,
            NETLIST_DESIGN_MISSING,
            diagnostics=self.state.diagnostics,
        )
        if design is None:
            return

        modules_by_name, devices_by_name, module_ops = _collect_design_ops(design)
        module_index = {
            (
                op.sym_name.data,
                op.file_id.data if op.file_id is not None else None,
            ): op
            for modules in modules_by_name.values()
            for op in modules
        }
        device_index = {
            (
                op.sym_name.data,
                op.file_id.data if op.file_id is not None else None,
            ): op
            for devices in devices_by_name.values()
            for op in devices
        }
        top_name = _resolve_top_name(design, module_ops, self.state.diagnostics)
        if top_name is None:
            return

        self.state.diagnostics.extend(
            validate_system_devices(self.state.backend_config)
        )
        _validate_system_device_templates(self.state.backend_config, self.state.diagnostics)

        for module in module_ops:
            for op in module.body.block.ops:
                if not isinstance(op, InstanceOp):
                    continue
                ref_name = op.ref.root_reference.data
                ref_file_id = (
                    op.ref_file_id.data if op.ref_file_id is not None else None
                )
                module = _select_symbol(
                    modules_by_name, module_index, ref_name, ref_file_id
                )
                if module is not None:
                    port_order = [attr.data for attr in module.port_order.data]
                    _ordered_conns(op, port_order, self.state.diagnostics)
                    continue
                device = _select_symbol(
                    devices_by_name, device_index, ref_name, ref_file_id
                )
                if device is None:
                    self.state.diagnostics.emit(
                        _diagnostic(
                            UNKNOWN_REFERENCE,
                            (
                                f"Instance '{op.name_attr.data}' references unknown "
                                f"symbol '{ref_name}'"
                            ),
                            Severity.ERROR,
                            op.src,
                        )
                    )
                    continue

                backend = _select_backend(device, self.state.backend_name)
                if backend is None:
                    self.state.diagnostics.emit(
                        _diagnostic(
                            MISSING_BACKEND,
                            f"Device '{ref_name}' has no backend '{self.state.backend_name}'",
                            Severity.ERROR,
                            device.src,
                        )
                    )
                    continue

                port_order = [attr.data for attr in device.ports.data]
                _ordered_conns(op, port_order, self.state.diagnostics)

                device_params = _dict_attr_to_strings(device.params)
                backend_params = _dict_attr_to_strings(backend.params)
                instance_params = _dict_attr_to_strings(op.params)
                device_vars = _dict_attr_to_strings(device.variables)
                backend_vars = _dict_attr_to_strings(backend.variables)
                props = _dict_attr_to_strings(backend.props)
                _, variable_diags = _merge_variables(
                    device_vars,
                    backend_vars,
                    device_param_keys=device_params.keys(),
                    backend_param_keys=backend_params.keys(),
                    backend_prop_keys=props.keys(),
                    instance_params=instance_params,
                    instance_name=op.name_attr.data,
                    device_name=ref_name,
                    device_loc=device.src,
                    backend_loc=backend.src,
                    instance_loc=op.src,
                )
                self.state.diagnostics.extend(variable_diags)

                placeholders = _validate_template(
                    backend.template.data,
                    ref_name,
                    self.state.diagnostics,
                    loc=backend.src,
                )
                if placeholders is None:
                    continue

                unknown = placeholders - _allowed_backend_placeholders(device, backend)
                if unknown:
                    unknown_name = sorted(unknown)[0]
                    self.state.diagnostics.emit(
                        _diagnostic(
                            UNKNOWN_REFERENCE,
                            (
                                f"Backend template for '{ref_name}' references "
                                f"unknown placeholder '{unknown_name}'"
                            ),
                            Severity.ERROR,
                            backend.src,
                        )
                    )


def _run_netlist_verification(
    design: DesignOp,
    *,
    backend_name: str,
    backend_config: BackendConfig,
) -> List[Diagnostic]:
    diagnostics = DiagnosticCollector()
    state = NetlistVerificationState(
        diagnostics=diagnostics,
        backend_name=backend_name,
        backend_config=backend_config,
    )

    # Clone when already attached to avoid reparenting into a new module.
    design_op = design.clone() if design.parent is not None else design
    module = builtin.ModuleOp([design_op])
    pipeline = PassPipeline((VerifyNetlistPass(state=state),))
    ctx = _build_context()
    try:
        pipeline.apply(ctx, module)
    except Exception as exc:  # pragma: no cover - defensive
        diagnostics.emit(
            _diagnostic(
                NETLIST_VERIFY_CRASH,
                f"Netlist verification failed: {exc}",
                Severity.ERROR,
            )
        )

    return diagnostics.to_list()


def _build_context() -> Context:
    ctx = Context()
    ctx.load_dialect(builtin.Builtin)
    ctx.load_dialect(ASDL_IFIR)
    return ctx
