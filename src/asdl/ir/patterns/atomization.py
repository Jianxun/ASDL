from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Tuple

from xdsl.context import Context
from xdsl.dialects import builtin
from xdsl.dialects.builtin import ArrayAttr, DictionaryAttr, LocationAttr, StringAttr
from xdsl.ir import Operation
from xdsl.passes import ModulePass, PassPipeline
from xdsl.utils.exceptions import VerifyException

from asdl.diagnostics import Diagnostic, Severity, format_code
from asdl.diagnostics.collector import DiagnosticCollector
from asdl.ir.graphir import BundleOp, PatternExprOp
from asdl.ir.graphir.patterns import (
    rebundle_bundle as _rebundle_bundle,
    rebundle_pattern_expr as _rebundle_pattern_expr,
)
from asdl.ir.ifir import ASDL_IFIR, ConnAttr, DesignOp, DeviceOp, InstanceOp, ModuleOp, NetOp
from asdl.ir.location import location_attr_to_span
from asdl.patterns import (
    AtomizedEndpoint,
    AtomizedPattern,
    atomize_endpoint,
    atomize_pattern,
    collect_literal_collisions,
    format_endpoint_length_mismatch,
    format_literal_collision_message,
    format_param_length_mismatch,
)

NO_SPAN_NOTE = "No source span available."

ATOMIZE_DESIGN_MISSING = format_code("PASS", 8)
ATOMIZE_INVALID_OP = format_code("PASS", 9)
ATOMIZE_VERIFY_FAILED = format_code("PASS", 10)
ATOMIZE_LITERAL_COLLISION = format_code("PASS", 11)
ATOMIZE_UNKNOWN_ENDPOINT_INSTANCE = format_code("PASS", 12)
ATOMIZE_CRASH = format_code("PASS", 997)


@dataclass
class PatternAtomizeState:
    diagnostics: DiagnosticCollector
    failed: bool = False
    design: Optional[DesignOp] = None


@dataclass(frozen=True)
class PatternAtomizePass(ModulePass):
    name = "atomize-patterns"

    state: PatternAtomizeState

    def apply(self, ctx: Context, op: builtin.ModuleOp) -> None:
        design = _find_single_design(
            op,
            DesignOp,
            ATOMIZE_DESIGN_MISSING,
            diagnostics=self.state.diagnostics,
        )
        if design is None:
            self.state.failed = True
            return

        atomized = _atomize_design(design, self.state.diagnostics)
        if atomized is None:
            self.state.failed = True
            return

        block = op.body.block
        block.insert_op_before(atomized, design)
        block.erase_op(design)
        self.state.design = atomized


def run_pattern_atomization(
    design: DesignOp,
) -> Tuple[Optional[DesignOp], List[Diagnostic]]:
    diagnostics = DiagnosticCollector()
    state = PatternAtomizeState(diagnostics=diagnostics)

    design_op = design.clone() if design.parent is not None else design
    module = builtin.ModuleOp([design_op])
    pipeline = PassPipeline((PatternAtomizePass(state=state),))
    ctx = _build_context()
    try:
        pipeline.apply(ctx, module)
    except Exception as exc:  # pragma: no cover - defensive
        diagnostics.emit(
            _diagnostic(
                ATOMIZE_CRASH,
                f"Pattern atomization failed: {exc}",
            )
        )
        return None, diagnostics.to_list()

    if state.failed:
        return None, diagnostics.to_list()

    if state.design is None:
        state.design = _find_single_design(
            module,
            DesignOp,
            ATOMIZE_DESIGN_MISSING,
            diagnostics=diagnostics,
        )
        if state.design is None:
            return None, diagnostics.to_list()

    return state.design, diagnostics.to_list()


def _atomize_design(
    design: DesignOp,
    diagnostics: DiagnosticCollector,
) -> Optional[DesignOp]:
    modules: List[ModuleOp] = []
    devices: List[DeviceOp] = []
    had_error = False

    for op in design.body.block.ops:
        if isinstance(op, ModuleOp):
            module, module_error = _atomize_module(op, diagnostics)
            modules.append(module)
            had_error = had_error or module_error
            continue
        if isinstance(op, DeviceOp):
            devices.append(op.clone())
            continue
        diagnostics.emit(
            _diagnostic(
                ATOMIZE_INVALID_OP,
                "asdl_ifir.design contains non-module/device ops",
                getattr(op, "src", None),
            )
        )
        had_error = True

    atomized = DesignOp(
        region=[*modules, *devices],
        top=design.top,
        entry_file_id=design.entry_file_id,
        doc=design.doc,
        src=design.src,
    )
    if had_error:
        return None

    try:
        atomized.verify()
    except VerifyException as exc:
        diagnostics.emit(
            _diagnostic(
                ATOMIZE_VERIFY_FAILED,
                f"IFIR verification failed after atomization: {exc}",
                design.src,
            )
        )
        return None

    return atomized


def _atomize_module(
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
                ATOMIZE_INVALID_OP,
                "asdl_ifir.module contains non-net/instance ops",
                getattr(op, "src", None) or module.src,
            )
        )
        had_error = True

    net_cache: Dict[str, Optional[List[AtomizedPattern]]] = {}
    inst_cache: Dict[str, Optional[List[AtomizedPattern]]] = {}
    endpoint_cache: Dict[Tuple[str, str], Optional[List[AtomizedEndpoint]]] = {}

    port_order: List[str] = []
    for port_attr in module.port_order.data:
        token = port_attr.data
        atoms = _atomize_cached(token, net_cache, diagnostics)
        if atoms is None:
            had_error = True
            continue
        port_order.extend(atom.literal for atom in atoms)

    net_ops: List[NetOp] = []
    net_literals: List[Tuple[str, str, LocationAttr | None]] = []
    for net in nets:
        token = net.name_attr.data
        atoms = _atomize_cached(token, net_cache, diagnostics)
        if atoms is None:
            had_error = True
            continue
        for atom in atoms:
            pattern_origin = net.pattern_origin if net.pattern_origin is not None else atom.origin
            net_ops.append(
                NetOp(
                    name=atom.literal,
                    net_type=net.net_type,
                    pattern_origin=pattern_origin,
                    src=net.src,
                )
            )
            net_literals.append((atom.literal, atom.token, net.src or module.src))

    instance_order: List[Tuple[InstanceOp, List[AtomizedPattern]]] = []
    instance_atoms: List[str] = []
    instance_literals: List[Tuple[str, str, LocationAttr | None]] = []

    for inst in instances:
        token = inst.name_attr.data
        atoms = _atomize_cached(token, inst_cache, diagnostics)
        if atoms is None:
            had_error = True
            atoms = []
        instance_order.append((inst, atoms))
        for atom in atoms:
            instance_atoms.append(atom.literal)
            instance_literals.append((atom.literal, atom.token, inst.src or module.src))

    had_error = _emit_literal_collisions(
        net_literals,
        diagnostics,
        kind="Net",
        had_error=had_error,
    )
    had_error = _emit_literal_collisions(
        instance_literals,
        diagnostics,
        kind="Instance",
        had_error=had_error,
    )

    conn_map: Dict[str, List[ConnAttr]] = {atom: [] for atom in instance_atoms}
    param_map: Dict[str, Optional[DictionaryAttr]] = {}

    for inst, atoms in instance_order:
        params_per_atom, params_error = _atomize_instance_params(
            inst, atoms, diagnostics, inst.src or module.src
        )
        had_error = had_error or params_error
        for atom, params in zip(atoms, params_per_atom):
            param_map[atom.literal] = params

    for inst in instances:
        inst_token = inst.name_attr.data
        for conn in inst.conns.data:
            net_token = conn.net.data
            net_atoms = _atomize_cached(net_token, net_cache, diagnostics)
            if net_atoms is None:
                had_error = True
                continue

            endpoint_key = (inst_token, conn.port.data)
            if endpoint_key not in endpoint_cache:
                expanded, diags = atomize_endpoint(inst_token, conn.port.data)
                diagnostics.extend(diags)
                endpoint_cache[endpoint_key] = expanded
            endpoint_atoms = endpoint_cache[endpoint_key]
            if endpoint_atoms is None:
                had_error = True
                continue

            if len(net_atoms) > 1 and len(endpoint_atoms) != len(net_atoms):
                diagnostics.emit(
                    _diagnostic(
                        ATOMIZE_VERIFY_FAILED,
                        format_endpoint_length_mismatch(
                            net_token,
                            len(net_atoms),
                            f"{inst_token}.{conn.port.data}",
                            len(endpoint_atoms),
                            verb="atomizes",
                        ),
                        inst.src or module.src,
                    )
                )
                had_error = True
                continue

            if len(net_atoms) == 1:
                net_name = net_atoms[0].literal
                for endpoint in endpoint_atoms:
                    inst_atom = endpoint.inst.literal
                    if inst_atom not in conn_map:
                        diagnostics.emit(
                            _diagnostic(
                                ATOMIZE_UNKNOWN_ENDPOINT_INSTANCE,
                                (
                                    f"Endpoint '{inst_token}.{conn.port.data}' resolves "
                                    f"to undeclared instance atom '{inst_atom}'"
                                ),
                                inst.src or module.src,
                            )
                        )
                        had_error = True
                        continue
                    conn_map[inst_atom].append(
                        ConnAttr(StringAttr(endpoint.pin.literal), StringAttr(net_name))
                    )
                continue

            for net_atom, endpoint in zip(net_atoms, endpoint_atoms):
                inst_atom = endpoint.inst.literal
                if inst_atom not in conn_map:
                    diagnostics.emit(
                        _diagnostic(
                            ATOMIZE_UNKNOWN_ENDPOINT_INSTANCE,
                            (
                                f"Endpoint '{inst_token}.{conn.port.data}' resolves "
                                f"to undeclared instance atom '{inst_atom}'"
                            ),
                            inst.src or module.src,
                        )
                    )
                    had_error = True
                    continue
                conn_map[inst_atom].append(
                    ConnAttr(StringAttr(endpoint.pin.literal), StringAttr(net_atom.literal))
                )

    inst_ops: List[InstanceOp] = []
    for inst, atoms in instance_order:
        for atom in atoms:
            pattern_origin = (
                inst.pattern_origin if inst.pattern_origin is not None else atom.origin
            )
            conns = conn_map.get(atom.literal, [])
            inst_ops.append(
                InstanceOp(
                    name=atom.literal,
                    ref=inst.ref,
                    conns=ArrayAttr(conns),
                    ref_file_id=inst.ref_file_id,
                    params=param_map.get(atom.literal),
                    pattern_origin=pattern_origin,
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


def _atomize_cached(
    token: str,
    cache: Dict[str, Optional[List[AtomizedPattern]]],
    diagnostics: DiagnosticCollector,
) -> Optional[List[AtomizedPattern]]:
    if token not in cache:
        atoms, diags = atomize_pattern(token)
        diagnostics.extend(diags)
        cache[token] = atoms
    return cache[token]


def _atomize_instance_params(
    inst: InstanceOp,
    atoms: List[AtomizedPattern],
    diagnostics: DiagnosticCollector,
    loc: LocationAttr | None,
) -> Tuple[List[Optional[DictionaryAttr]], bool]:
    if not atoms:
        return [], False
    params = inst.params
    if params is None or not params.data:
        return [None for _ in atoms], False

    expanded_params: Dict[str, List[str]] = {}
    had_error = False
    instance_len = len(atoms)

    for key, value in params.data.items():
        value_str = _stringify_attr(value)
        atomized, diags = atomize_pattern(value_str)
        diagnostics.extend(diags)
        if atomized is None:
            had_error = True
            continue
        expanded = [atom.token for atom in atomized]
        if len(expanded) not in (1, instance_len):
            diagnostics.emit(
                _diagnostic(
                    ATOMIZE_VERIFY_FAILED,
                    format_param_length_mismatch(
                        inst.name_attr.data,
                        key,
                        len(expanded),
                        instance_len,
                        verb="atomizes",
                    ),
                    loc,
                )
            )
            had_error = True
            continue
        expanded_params[key] = expanded

    params_per_atom: List[Optional[DictionaryAttr]] = []
    for idx in range(instance_len):
        items: Dict[str, StringAttr] = {}
        for key, expanded in expanded_params.items():
            value = expanded[0] if len(expanded) == 1 else expanded[idx]
            items[key] = StringAttr(value)
        params_per_atom.append(DictionaryAttr(items) if items else None)

    return params_per_atom, had_error


def _stringify_attr(value: object) -> str:
    if isinstance(value, StringAttr):
        return value.data
    if hasattr(value, "data"):
        return str(value.data)
    return str(value)


def _emit_literal_collisions(
    entries: List[Tuple[str, str, LocationAttr | None]],
    diagnostics: DiagnosticCollector,
    *,
    kind: str,
    had_error: bool,
) -> bool:
    collisions = collect_literal_collisions(
        [(literal, token) for literal, token, _ in entries]
    )
    if not collisions:
        return had_error

    first_locations: Dict[str, LocationAttr | None] = {}
    for literal, _, loc in entries:
        if literal not in first_locations:
            first_locations[literal] = loc

    for literal, tokens in collisions.items():
        diagnostics.emit(
            _diagnostic(
                ATOMIZE_LITERAL_COLLISION,
                format_literal_collision_message(
                    kind,
                    literal,
                    tokens,
                    phase="atomization",
                ),
                first_locations.get(literal),
            )
        )
        had_error = True
    return had_error


def rebundle_bundle(bundle: BundleOp) -> str:
    """Rebundle a GraphIR bundle into a pattern token string.

    Args:
        bundle: Bundle op containing pattern metadata.

    Returns:
        Rebundled pattern token string.
    """
    return _rebundle_bundle(bundle)


def rebundle_pattern_expr(
    pattern_expr: PatternExprOp, bundles: Mapping[str, BundleOp]
) -> str:
    """Rebundle a GraphIR pattern expression using bundle order.

    Args:
        pattern_expr: Pattern expression op to rebundle.
        bundles: Mapping from bundle_id to BundleOp.

    Returns:
        Rebundled pattern token string with `;` boundaries preserved.
    """
    return _rebundle_pattern_expr(pattern_expr, bundles)


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


__all__ = [
    "PatternAtomizePass",
    "rebundle_bundle",
    "rebundle_pattern_expr",
    "run_pattern_atomization",
]
