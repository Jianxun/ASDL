"""Lower AtomizedGraph programs into IFIR design ops."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from xdsl.dialects.builtin import DictionaryAttr, StringAttr

from asdl.core.atomized_graph import (
    AtomizedDeviceDef,
    AtomizedEndpoint,
    AtomizedInstance,
    AtomizedModuleGraph,
    AtomizedNet,
    AtomizedProgramGraph,
)
from asdl.core.registries import PatternExpr, PatternExprKind, RegistrySet
from asdl.diagnostics import Diagnostic, Severity, format_code
from asdl.ir.ifir import (
    BackendOp,
    ConnAttr,
    DesignOp,
    DeviceOp,
    InstanceOp,
    ModuleOp,
    NetOp,
)
from asdl.ir.patterns.expr_table import (
    PatternExpressionEntry,
    encode_pattern_expression_table,
)
from asdl.ir.patterns.origin import PatternOrigin, encode_pattern_origin
from asdl.ir.patterns.parts import PatternPart
from asdl.patterns_refactor.parser import PatternGroup, PatternLiteral

NO_SPAN_NOTE = "No source span available."

UNKNOWN_ATOMIZED_REFERENCE = format_code("IR", 40)
UNKNOWN_ATOMIZED_ENDPOINT = format_code("IR", 41)
MISSING_ATOMIZED_PATTERN = format_code("IR", 42)
MISSING_ATOMIZED_EXPR_KIND = format_code("IR", 43)
MISSING_ATOMIZED_BACKEND_TEMPLATE = format_code("IR", 44)


@dataclass(frozen=True)
class _PatternAtom:
    """Expanded atom metadata for pattern origin reconstruction."""

    literal: str
    segment_index: int
    atom_index: int
    base_name: str
    pattern_parts: list[PatternPart]


class _PatternOriginResolver:
    """Resolve pattern origin metadata from AtomizedGraph registries."""

    def __init__(self, registries: RegistrySet) -> None:
        self._expr_registry = registries.pattern_expressions
        self._expr_kinds = registries.pattern_expr_kinds
        self._pattern_origins = registries.pattern_origins
        self._atoms_cache: Dict[str, List[List[_PatternAtom]]] = {}
        self._missing_expr_ids: set[str] = set()
        self._missing_kind_ids: set[str] = set()
        self._missing_origin_ids: set[str] = set()
        self._missing_origin_registry_reported = False
        self._missing_expr_registry_reported = False
        self._missing_kind_registry_reported = False

    def _report_missing_expr(
        self, expr_id: str, diagnostics: List[Diagnostic], message: str
    ) -> bool:
        """Record a missing pattern expression once per expr id."""
        if expr_id in self._missing_expr_ids:
            return False
        self._missing_expr_ids.add(expr_id)
        diagnostics.append(_diagnostic(MISSING_ATOMIZED_PATTERN, message))
        return True

    def _report_missing_kind(
        self, expr_id: str, diagnostics: List[Diagnostic], message: str
    ) -> bool:
        """Record a missing pattern expression kind once per expr id."""
        if expr_id in self._missing_kind_ids:
            return False
        self._missing_kind_ids.add(expr_id)
        diagnostics.append(_diagnostic(MISSING_ATOMIZED_EXPR_KIND, message))
        return True

    def resolve(
        self,
        *,
        entity_id: Optional[str],
        literal: str,
        expected_kind: PatternExprKind,
        diagnostics: List[Diagnostic],
        label: str,
        module_name: str,
    ) -> Tuple[Optional[object], bool]:
        """Resolve a GraphPatternOriginAttr for an atomized literal.

        Args:
            entity_id: PatternedGraph entity identifier.
            literal: Atomized literal name.
            expected_kind: Expected pattern expression kind.
            diagnostics: Diagnostic output list to append to on failures.
            label: Entity label for diagnostics.
            module_name: Module name for diagnostics.

        Returns:
            Tuple of (encoded GraphPatternOriginAttr or None, error flag).
        """
        if entity_id is None:
            return None, False
        if self._pattern_origins is None:
            if not self._missing_origin_registry_reported:
                diagnostics.append(
                    _diagnostic(
                        MISSING_ATOMIZED_PATTERN,
                        (
                            "Missing pattern origin registry for "
                            f"{label} in module '{module_name}'."
                        ),
                    )
                )
                self._missing_origin_registry_reported = True
            return None, True
        origin = self._pattern_origins.get(entity_id)
        if origin is None:
            if entity_id not in self._missing_origin_ids:
                diagnostics.append(
                    _diagnostic(
                        MISSING_ATOMIZED_PATTERN,
                        (
                            "Missing pattern origin entry for "
                            f"{label} in module '{module_name}'."
                        ),
                    )
                )
                self._missing_origin_ids.add(entity_id)
            return None, True
        expr_id, segment_index, atom_index = origin
        if self._expr_registry is None:
            if not self._missing_expr_registry_reported:
                diagnostics.append(
                    _diagnostic(
                        MISSING_ATOMIZED_PATTERN,
                        (
                            "Missing pattern expression registry for "
                            f"{label} in module '{module_name}'."
                        ),
                    )
                )
                self._missing_expr_registry_reported = True
            return None, True
        expr = self._expr_registry.get(expr_id)
        if expr is None:
            self._report_missing_expr(
                expr_id,
                diagnostics,
                (
                    f"Missing pattern expression '{expr_id}' for "
                    f"{label} in module '{module_name}'."
                ),
            )
            return None, True
        if self._expr_kinds is None:
            if not self._missing_kind_registry_reported:
                diagnostics.append(
                    _diagnostic(
                        MISSING_ATOMIZED_EXPR_KIND,
                        (
                            "Missing pattern expression kind registry for "
                            f"{label} in module '{module_name}'."
                        ),
                    )
                )
                self._missing_kind_registry_reported = True
            return None, True
        expr_kind = self._expr_kinds.get(expr_id)
        if expr_kind is None:
            self._report_missing_kind(
                expr_id,
                diagnostics,
                (
                    f"Missing pattern expression kind for '{expr_id}' used by "
                    f"{label} in module '{module_name}'."
                ),
            )
            return None, True
        if expr_kind != expected_kind:
            diagnostics.append(
                _diagnostic(
                    MISSING_ATOMIZED_EXPR_KIND,
                    (
                        f"Pattern expression kind mismatch for {label} in module "
                        f"'{module_name}': expected '{expected_kind}', got "
                        f"'{expr_kind}'."
                    ),
                )
            )
            return None, True
        atoms_by_segment = self._atoms_cache.get(expr_id)
        if atoms_by_segment is None:
            atoms_by_segment = _index_pattern_atoms(expr)
            self._atoms_cache[expr_id] = atoms_by_segment
        if segment_index < 0 or segment_index >= len(atoms_by_segment):
            diagnostics.append(
                _diagnostic(
                    MISSING_ATOMIZED_PATTERN,
                    (
                        f"Invalid pattern origin segment index for {label} in "
                        f"module '{module_name}': {segment_index}."
                    ),
                )
            )
            return None, True
        segment_atoms = atoms_by_segment[segment_index]
        if atom_index < 0 or atom_index >= len(segment_atoms):
            diagnostics.append(
                _diagnostic(
                    MISSING_ATOMIZED_PATTERN,
                    (
                        f"Invalid pattern origin atom index for {label} in "
                        f"module '{module_name}': {atom_index}."
                    ),
                )
            )
            return None, True
        atom = segment_atoms[atom_index]
        if atom.literal != literal:
            diagnostics.append(
                _diagnostic(
                    MISSING_ATOMIZED_PATTERN,
                    (
                        f"Pattern origin literal mismatch for {label} in module "
                        f"'{module_name}': expected '{literal}', got "
                        f"'{atom.literal}'."
                    ),
                )
            )
            return None, True
        return (
            encode_pattern_origin(
                PatternOrigin(
                    expression_id=expr_id,
                    segment_index=segment_index,
                    base_name=atom.base_name,
                    pattern_parts=atom.pattern_parts,
                )
            ),
            False,
        )

    def collect_expr_ids(self, entity_ids: Iterable[str]) -> set[str]:
        """Collect expression ids referenced by entity ids."""
        if self._pattern_origins is None:
            return set()
        expr_ids: set[str] = set()
        for entity_id in entity_ids:
            origin = self._pattern_origins.get(entity_id)
            if origin is not None:
                expr_ids.add(origin[0])
        return expr_ids

    def build_pattern_expression_table(
        self,
        expr_ids: Iterable[str],
        diagnostics: List[Diagnostic],
        module_name: str,
    ) -> Tuple[Optional[DictionaryAttr], bool]:
        """Build a module-local pattern expression table when possible."""
        expr_id_list = list(expr_ids)
        if not expr_id_list:
            return None, False
        had_error = False
        if self._expr_registry is None:
            if not self._missing_expr_registry_reported:
                diagnostics.append(
                    _diagnostic(
                        MISSING_ATOMIZED_PATTERN,
                        (
                            "Missing pattern expression registry for "
                            f"module '{module_name}'."
                        ),
                    )
                )
                self._missing_expr_registry_reported = True
            return None, True
        if self._expr_kinds is None:
            if not self._missing_kind_registry_reported:
                diagnostics.append(
                    _diagnostic(
                        MISSING_ATOMIZED_EXPR_KIND,
                        (
                            "Missing pattern expression kind registry for "
                            f"module '{module_name}'."
                        ),
                    )
                )
                self._missing_kind_registry_reported = True
            return None, True
        entries: Dict[str, PatternExpressionEntry] = {}
        for expr_id in expr_id_list:
            expr = self._expr_registry.get(expr_id)
            if expr is None:
                if self._report_missing_expr(
                    expr_id,
                    diagnostics,
                    (
                        f"Missing pattern expression '{expr_id}' for module "
                        f"'{module_name}'."
                    ),
                ):
                    had_error = True
                continue
            kind = self._expr_kinds.get(expr_id)
            if kind is None:
                if self._report_missing_kind(
                    expr_id,
                    diagnostics,
                    (
                        f"Missing pattern expression kind for '{expr_id}' in "
                        f"module '{module_name}'."
                    ),
                ):
                    had_error = True
                continue
            entries[expr_id] = PatternExpressionEntry(
                expression=expr.raw,
                kind=kind,
                span=expr.span,
            )
        if not entries:
            return None, had_error
        return encode_pattern_expression_table(entries), had_error


def _index_pattern_atoms(expr: PatternExpr) -> List[List[_PatternAtom]]:
    """Index expanded atoms by segment and atom index."""
    atoms_by_segment: List[List[_PatternAtom]] = []
    for atom in _expand_pattern_atoms(expr):
        while atom.segment_index >= len(atoms_by_segment):
            atoms_by_segment.append([])
        atoms_by_segment[atom.segment_index].append(atom)
    return atoms_by_segment


def _expand_pattern_atoms(expr: PatternExpr) -> List[_PatternAtom]:
    """Expand a PatternExpr into atoms annotated with pattern parts."""
    atoms: List[_PatternAtom] = []
    for segment_index, segment in enumerate(expr.segments):
        base_name = "".join(
            token.text
            for token in segment.tokens
            if isinstance(token, PatternLiteral)
        )
        current: List[Tuple[str, list[PatternPart]]] = [("", [])]
        for token in segment.tokens:
            if isinstance(token, PatternLiteral):
                current = [
                    (value + token.text, parts) for value, parts in current
                ]
                continue
            if isinstance(token, PatternGroup):
                expanded: List[Tuple[str, list[PatternPart]]] = []
                for value, parts in current:
                    for label in token.labels:
                        expanded.append((value + str(label), [*parts, label]))
                current = expanded
                continue
        atoms.extend(
            _PatternAtom(
                literal=literal,
                segment_index=segment_index,
                atom_index=atom_index,
                base_name=base_name,
                pattern_parts=parts,
            )
            for atom_index, (literal, parts) in enumerate(current)
        )
    return atoms


def build_ifir_design(
    program: AtomizedProgramGraph,
    *,
    top_module_id: Optional[str] = None,
) -> Tuple[Optional[DesignOp], List[Diagnostic]]:
    """Lower an AtomizedGraph program into an IFIR design op.

    Args:
        program: Atomized program graph to lower.
        top_module_id: Optional module ID to use as the design top.

    Returns:
        Tuple of (IFIR design or None, diagnostics).
    """
    diagnostics: List[Diagnostic] = []
    had_error = False

    top_module = None
    if top_module_id is not None:
        top_module = program.modules.get(top_module_id)
        if top_module is None:
            diagnostics.append(
                _diagnostic(
                    UNKNOWN_ATOMIZED_REFERENCE,
                    f"Top module id '{top_module_id}' is not defined.",
                )
            )
            had_error = True
    elif len(program.modules) == 1:
        top_module = next(iter(program.modules.values()))

    pattern_resolver = _PatternOriginResolver(program.registries)

    module_ops: List[ModuleOp] = []
    for module in program.modules.values():
        module_op, module_error = _convert_module(
            module, program, diagnostics, pattern_resolver
        )
        module_ops.append(module_op)
        had_error = had_error or module_error

    backend_templates = program.registries.device_backend_templates
    device_ops: List[DeviceOp] = []
    for device in program.devices.values():
        device_op, device_error = _convert_device(
            device, backend_templates, diagnostics
        )
        device_ops.append(device_op)
        had_error = had_error or device_error

    top_name = top_module.name if top_module is not None else None
    entry_file_id = top_module.file_id if top_module is not None else None
    design = DesignOp(
        region=[*module_ops, *device_ops],
        top=top_name,
        entry_file_id=entry_file_id,
    )
    if had_error:
        return None, diagnostics
    return design, diagnostics


def _convert_module(
    module: AtomizedModuleGraph,
    program: AtomizedProgramGraph,
    diagnostics: List[Diagnostic],
    pattern_resolver: _PatternOriginResolver,
) -> Tuple[ModuleOp, bool]:
    """Convert an atomized module into an IFIR module op."""
    had_error = False
    conn_map: Dict[str, List[ConnAttr]] = {
        inst_id: [] for inst_id in module.instances
    }
    net_ops: List[NetOp] = []

    for net in module.nets.values():
        pattern_origin, origin_error = pattern_resolver.resolve(
            entity_id=net.patterned_net_id,
            literal=net.name,
            expected_kind="net",
            diagnostics=diagnostics,
            label=f"net '{net.name}'",
            module_name=module.name,
        )
        had_error = had_error or origin_error
        net_ops.append(NetOp(name=net.name, pattern_origin=pattern_origin))
        endpoints, endpoint_error = _collect_net_endpoints(
            module, net, diagnostics
        )
        had_error = had_error or endpoint_error
        for endpoint in endpoints:
            conns = conn_map.get(endpoint.inst_id)
            if conns is None:
                diagnostics.append(
                    _diagnostic(
                        UNKNOWN_ATOMIZED_ENDPOINT,
                        (
                            f"Endpoint '{endpoint.endpoint_id}' in module "
                            f"'{module.name}' references unknown instance "
                            f"'{endpoint.inst_id}'."
                        ),
                    )
                )
                had_error = True
                continue
            conns.append(
                ConnAttr(StringAttr(endpoint.port), StringAttr(net.name))
            )

    inst_ops: List[InstanceOp] = []
    for inst_id, instance in module.instances.items():
        ref_name, ref_file_id, ref_error = _resolve_ref(
            instance, program, diagnostics
        )
        had_error = had_error or ref_error
        if ref_name is None:
            continue
        pattern_origin, origin_error = pattern_resolver.resolve(
            entity_id=instance.patterned_inst_id,
            literal=instance.name,
            expected_kind="inst",
            diagnostics=diagnostics,
            label=f"instance '{instance.name}'",
            module_name=module.name,
        )
        had_error = had_error or origin_error
        inst_ops.append(
            InstanceOp(
                name=instance.name,
                ref=ref_name,
                ref_file_id=ref_file_id,
                params=_to_string_dict_attr(instance.param_values),
                conns=conn_map.get(inst_id, []),
                pattern_origin=pattern_origin,
            )
        )

    expr_ids = pattern_resolver.collect_expr_ids(
        [
            entity_id
            for entity_id in (
                [net.patterned_net_id for net in module.nets.values()]
                + [inst.patterned_inst_id for inst in module.instances.values()]
                + [endpoint.patterned_endpoint_id for endpoint in module.endpoints.values()]
            )
            if entity_id is not None
        ]
    )
    pattern_expression_table, table_error = pattern_resolver.build_pattern_expression_table(
        expr_ids,
        diagnostics,
        module.name,
    )
    had_error = had_error or table_error

    return (
        ModuleOp(
            name=module.name,
            port_order=module.ports or [],
            region=[*net_ops, *inst_ops],
            file_id=module.file_id,
            pattern_expression_table=pattern_expression_table,
        ),
        had_error,
    )


def _collect_net_endpoints(
    module: AtomizedModuleGraph,
    net: AtomizedNet,
    diagnostics: List[Diagnostic],
) -> Tuple[List[AtomizedEndpoint], bool]:
    """Collect endpoints for a net, emitting diagnostics for missing entries."""
    had_error = False
    endpoints: List[AtomizedEndpoint] = []
    for endpoint_id in net.endpoint_ids:
        endpoint = module.endpoints.get(endpoint_id)
        if endpoint is None:
            diagnostics.append(
                _diagnostic(
                    UNKNOWN_ATOMIZED_ENDPOINT,
                    (
                        f"Net '{net.name}' in module '{module.name}' references "
                        f"missing endpoint '{endpoint_id}'."
                    ),
                )
            )
            had_error = True
            continue
        endpoints.append(endpoint)
    return endpoints, had_error


def _convert_device(
    device: AtomizedDeviceDef,
    backend_templates: Optional[Dict[str, Dict[str, str]]],
    diagnostics: List[Diagnostic],
) -> Tuple[DeviceOp, bool]:
    """Convert an atomized device definition into an IFIR device op.

    Returns:
        Tuple of (device op, error flag).
    """
    had_error = False
    backends: List[BackendOp] = []
    templates = backend_templates.get(device.device_id) if backend_templates else None
    if templates:
        for backend_name, template in templates.items():
            backends.append(
                BackendOp(
                    name=backend_name,
                    template=template,
                )
            )
    else:
        diagnostics.append(
            _diagnostic(
                MISSING_ATOMIZED_BACKEND_TEMPLATE,
                (
                    f"Missing backend template for device '{device.name}' "
                    f"(id '{device.device_id}')."
                ),
            )
        )
        had_error = True
    return (
        DeviceOp(
            name=device.name,
            ports=device.ports or [],
            file_id=device.file_id,
            params=_to_string_dict_attr(device.parameters),
            variables=_to_string_dict_attr(device.variables),
            region=backends,
        ),
        had_error,
    )


def _resolve_ref(
    instance: AtomizedInstance,
    program: AtomizedProgramGraph,
    diagnostics: List[Diagnostic],
) -> Tuple[Optional[str], Optional[str], bool]:
    """Resolve instance references into IFIR symbol data."""
    if instance.ref_kind == "module":
        module = program.modules.get(instance.ref_id)
        if module is None:
            diagnostics.append(
                _diagnostic(
                    UNKNOWN_ATOMIZED_REFERENCE,
                    (
                        f"Instance '{instance.name}' references unknown module "
                        f"id '{instance.ref_id}'."
                    ),
                )
            )
            return None, None, True
        return module.name, module.file_id, False
    if instance.ref_kind == "device":
        device = program.devices.get(instance.ref_id)
        if device is None:
            diagnostics.append(
                _diagnostic(
                    UNKNOWN_ATOMIZED_REFERENCE,
                    (
                        f"Instance '{instance.name}' references unknown device "
                        f"id '{instance.ref_id}'."
                    ),
                )
            )
            return None, None, True
        return device.name, device.file_id, False

    diagnostics.append(
        _diagnostic(
            UNKNOWN_ATOMIZED_REFERENCE,
            (
                f"Instance '{instance.name}' has unsupported ref kind "
                f"'{instance.ref_kind}'."
            ),
        )
    )
    return None, None, True


def _to_string_dict_attr(
    values: Optional[Dict[str, object]],
) -> Optional[DictionaryAttr]:
    """Convert a dictionary to a DictionaryAttr of string values."""
    if not values:
        return None
    payload = {key: StringAttr(_format_param_value(value)) for key, value in values.items()}
    return DictionaryAttr(payload)


def _format_param_value(value: object) -> str:
    """Format parameter values as strings."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _diagnostic(code: str, message: str) -> Diagnostic:
    """Create an error diagnostic without a source span."""
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        message=message,
        primary_span=None,
        notes=[NO_SPAN_NOTE],
        source="ir",
    )


__all__ = ["build_ifir_design"]
