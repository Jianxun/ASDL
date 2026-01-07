from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from xdsl.context import Context
from xdsl.dialects import builtin
from xdsl.dialects.builtin import ArrayAttr, LocationAttr, StringAttr
from xdsl.ir import Operation
from xdsl.passes import ModulePass, PassPipeline
from xdsl.utils.exceptions import VerifyException

from asdl.diagnostics import Diagnostic, Severity, format_code
from asdl.diagnostics.collector import DiagnosticCollector
from asdl.ir.ifir import ASDL_IFIR, ConnAttr, DesignOp, DeviceOp, InstanceOp, ModuleOp, NetOp
from asdl.ir.location import location_attr_to_span
from asdl.patterns import expand_endpoint, expand_pattern

NO_SPAN_NOTE = "No source span available."

ELABORATION_DESIGN_MISSING = format_code("PASS", 5)
ELABORATION_INVALID_OP = format_code("PASS", 6)
ELABORATION_VERIFY_FAILED = format_code("PASS", 7)
ELABORATION_CRASH = format_code("PASS", 998)


@dataclass
class PatternElaborationState:
    diagnostics: DiagnosticCollector
    failed: bool = False
    design: Optional[DesignOp] = None


@dataclass(frozen=True)
class ElaboratePatternsPass(ModulePass):
    name = "elaborate-patterns"

    state: PatternElaborationState

    def apply(self, ctx: Context, op: builtin.ModuleOp) -> None:
        design = _find_single_design(
            op,
            DesignOp,
            ELABORATION_DESIGN_MISSING,
            diagnostics=self.state.diagnostics,
        )
        if design is None:
            self.state.failed = True
            return

        elaborated = _elaborate_design(design, self.state.diagnostics)
        if elaborated is None:
            self.state.failed = True
            return

        block = op.body.block
        block.insert_op_before(elaborated, design)
        block.erase_op(design)
        self.state.design = elaborated


def run_pattern_elaboration(
    design: DesignOp,
) -> Tuple[Optional[DesignOp], List[Diagnostic]]:
    diagnostics = DiagnosticCollector()
    state = PatternElaborationState(diagnostics=diagnostics)

    design_op = design.clone() if design.parent is not None else design
    module = builtin.ModuleOp([design_op])
    pipeline = PassPipeline((ElaboratePatternsPass(state=state),))
    ctx = _build_context()
    try:
        pipeline.apply(ctx, module)
    except Exception as exc:  # pragma: no cover - defensive
        diagnostics.emit(
            _diagnostic(
                ELABORATION_CRASH,
                f"Pattern elaboration failed: {exc}",
            )
        )
        return None, diagnostics.to_list()

    if state.failed:
        return None, diagnostics.to_list()

    if state.design is None:
        state.design = _find_single_design(
            module,
            DesignOp,
            ELABORATION_DESIGN_MISSING,
            diagnostics=diagnostics,
        )
        if state.design is None:
            return None, diagnostics.to_list()

    return state.design, diagnostics.to_list()


def _elaborate_design(
    design: DesignOp,
    diagnostics: DiagnosticCollector,
) -> Optional[DesignOp]:
    modules: List[ModuleOp] = []
    devices: List[DeviceOp] = []
    had_error = False

    for op in design.body.block.ops:
        if isinstance(op, ModuleOp):
            module, module_error = _elaborate_module(op, diagnostics)
            modules.append(module)
            had_error = had_error or module_error
            continue
        if isinstance(op, DeviceOp):
            devices.append(op.clone())
            continue
        diagnostics.emit(
            _diagnostic(
                ELABORATION_INVALID_OP,
                "asdl_ifir.design contains non-module/device ops",
                getattr(op, "src", None),
            )
        )
        had_error = True

    elaborated = DesignOp(
        region=[*modules, *devices],
        top=design.top,
        entry_file_id=design.entry_file_id,
        doc=design.doc,
        src=design.src,
    )
    if had_error:
        return None

    try:
        elaborated.verify()
    except VerifyException as exc:
        diagnostics.emit(
            _diagnostic(
                ELABORATION_VERIFY_FAILED,
                f"IFIR verification failed after elaboration: {exc}",
                design.src,
            )
        )
        return None

    return elaborated


def _elaborate_module(
    module: ModuleOp,
    diagnostics: DiagnosticCollector,
) -> Tuple[ModuleOp, bool]:
    had_error = False
    nets: List[NetOp] = []
    instances: List[InstanceOp] = []
    for op in module.body.block.ops:
        if isinstance(op, NetOp):
            nets.append(op)
            continue
        if isinstance(op, InstanceOp):
            instances.append(op)
            continue
        diagnostics.emit(
            _diagnostic(
                ELABORATION_INVALID_OP,
                "asdl_ifir.module contains non-net/instance ops",
                getattr(op, "src", None) or module.src,
            )
        )
        had_error = True

    port_order: List[str] = []
    port_expansions: Dict[str, Optional[List[str]]] = {}
    for port_attr in module.port_order.data:
        token = port_attr.data
        atoms = _expand_cached(token, port_expansions, diagnostics)
        if atoms is None:
            had_error = True
            continue
        port_order.extend(atoms)

    net_expansions: Dict[str, Optional[List[str]]] = {}
    net_ops: List[NetOp] = []
    for net in nets:
        token = net.name_attr.data
        atoms = _expand_cached(token, net_expansions, diagnostics)
        if atoms is None:
            had_error = True
            continue
        for atom in atoms:
            net_ops.append(
                NetOp(
                    name=atom,
                    net_type=net.net_type,
                    src=net.src,
                )
            )

    instance_expansions: Dict[str, Optional[List[str]]] = {}
    instance_order: List[Tuple[InstanceOp, List[str]]] = []
    instance_atoms: List[str] = []
    seen_instances: set[str] = set()
    for inst in instances:
        token = inst.name_attr.data
        atoms = _expand_cached(token, instance_expansions, diagnostics)
        if atoms is None:
            had_error = True
            atoms = []
        instance_order.append((inst, atoms))
        for atom in atoms:
            if atom in seen_instances:
                diagnostics.emit(
                    _diagnostic(
                        ELABORATION_VERIFY_FAILED,
                        f"Duplicate instance name '{atom}' after pattern expansion",
                        inst.src or module.src,
                    )
                )
                had_error = True
                continue
            seen_instances.add(atom)
            instance_atoms.append(atom)

    conn_map: Dict[str, List[ConnAttr]] = {atom: [] for atom in instance_atoms}
    endpoint_cache: Dict[Tuple[str, str], Optional[List[Tuple[str, str]]]] = {}

    for inst in instances:
        inst_token = inst.name_attr.data
        for conn in inst.conns.data:
            net_token = conn.net.data
            net_atoms = _expand_cached(net_token, net_expansions, diagnostics)
            if net_atoms is None:
                had_error = True
                continue

            endpoint_key = (inst_token, conn.port.data)
            if endpoint_key not in endpoint_cache:
                expanded, diags = expand_endpoint(inst_token, conn.port.data)
                diagnostics.extend(diags)
                endpoint_cache[endpoint_key] = expanded
            endpoint_atoms = endpoint_cache[endpoint_key]
            if endpoint_atoms is None:
                had_error = True
                continue

            if len(net_atoms) > 1 and len(endpoint_atoms) != len(net_atoms):
                diagnostics.emit(
                    _diagnostic(
                        ELABORATION_VERIFY_FAILED,
                        (
                            f"Net '{net_token}' expands to {len(net_atoms)} atoms but "
                            f"endpoint '{inst_token}.{conn.port.data}' expands to "
                            f"{len(endpoint_atoms)}"
                        ),
                        inst.src or module.src,
                    )
                )
                had_error = True
                continue

            if len(net_atoms) == 1:
                net_name = net_atoms[0]
                for inst_atom, pin_atom in endpoint_atoms:
                    if inst_atom not in conn_map:
                        had_error = True
                        continue
                    conn_map[inst_atom].append(
                        ConnAttr(StringAttr(pin_atom), StringAttr(net_name))
                    )
                continue

            for net_name, (inst_atom, pin_atom) in zip(net_atoms, endpoint_atoms):
                if inst_atom not in conn_map:
                    had_error = True
                    continue
                conn_map[inst_atom].append(
                    ConnAttr(StringAttr(pin_atom), StringAttr(net_name))
                )

    inst_ops: List[InstanceOp] = []
    for inst, atoms in instance_order:
        for atom in atoms:
            conns = conn_map.get(atom, [])
            inst_ops.append(
                InstanceOp(
                    name=atom,
                    ref=inst.ref,
                    conns=ArrayAttr(conns),
                    ref_file_id=inst.ref_file_id,
                    params=inst.params,
                    doc=inst.doc,
                    src=inst.src,
                )
            )

    module_op = ModuleOp(
        name=module.sym_name,
        port_order=port_order,
        region=[*net_ops, *inst_ops],
        file_id=module.file_id,
        doc=module.doc,
        src=module.src,
    )
    return module_op, had_error


def _expand_cached(
    token: str,
    cache: Dict[str, Optional[List[str]]],
    diagnostics: DiagnosticCollector,
) -> Optional[List[str]]:
    if token not in cache:
        expanded, diags = expand_pattern(token)
        diagnostics.extend(diags)
        cache[token] = expanded
    return cache[token]


def _build_context() -> Context:
    ctx = Context()
    ctx.load_dialect(builtin.Builtin)
    ctx.load_dialect(ASDL_IFIR)
    return ctx


def _find_single_design(
    module: builtin.ModuleOp,
    design_type: type[DesignOp],
    code: str,
    *,
    diagnostics: Optional[DiagnosticCollector] = None,
) -> Optional[DesignOp]:
    found = [op for op in module.body.block.ops if isinstance(op, design_type)]
    if len(found) == 1:
        return found[0]
    if diagnostics is not None:
        diagnostics.emit(
            _diagnostic(
                code,
                f"Expected single {design_type.name} in module, found {len(found)}",
            )
        )
    return None


def _diagnostic(
    code: str,
    message: str,
    loc: LocationAttr | None = None,
) -> Diagnostic:
    span = location_attr_to_span(loc)
    notes = None if span is not None else [NO_SPAN_NOTE]
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        message=message,
        primary_span=span,
        notes=notes,
        source="pass",
    )


__all__ = ["ElaboratePatternsPass", "run_pattern_elaboration"]
