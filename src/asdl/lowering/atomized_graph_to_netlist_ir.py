"""Lower AtomizedGraph programs into NetlistIR designs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from asdl.core.atomized_graph import (
    AtomizedDeviceDef,
    AtomizedEndpoint,
    AtomizedInstance,
    AtomizedModuleGraph,
    AtomizedNet,
    AtomizedProgramGraph,
)
from asdl.core.registries import PatternExpr, PatternExprKind, RegistrySet
from asdl.emit.netlist_ir import (
    NetlistBackend,
    NetlistConn,
    NetlistDesign,
    NetlistDevice,
    NetlistInstance,
    NetlistModule,
    NetlistNet,
    PatternExpressionEntry,
    PatternExpressionTable,
    PatternOrigin,
)
from asdl.patterns_refactor.parser import PatternGroup, PatternLiteral


@dataclass(frozen=True)
class _PatternAtom:
    """Expanded atom metadata for pattern origin reconstruction."""

    literal: str
    segment_index: int
    atom_index: int
    base_name: str
    pattern_parts: list[str | int]


class _PatternOriginResolver:
    """Resolve pattern origin metadata from AtomizedGraph registries."""

    def __init__(self, registries: RegistrySet) -> None:
        self._expr_registry = registries.pattern_expressions
        self._expr_kinds = registries.pattern_expr_kinds
        self._pattern_origins = registries.pattern_origins
        self._atoms_cache: Dict[str, List[List[_PatternAtom]]] = {}

    def resolve(
        self,
        entity_id: Optional[str],
        literal: str,
        _expected_kind: PatternExprKind,
    ) -> Optional[PatternOrigin]:
        """Resolve a NetlistIR PatternOrigin for an atomized literal."""
        if entity_id is None:
            return None
        if self._pattern_origins is None or self._expr_registry is None:
            return None
        origin = self._pattern_origins.get(entity_id)
        if origin is None:
            return None
        expr_id, segment_index, atom_index = origin
        expr = self._expr_registry.get(expr_id)
        if expr is None:
            return None
        # Intentionally skip kind checks so the verifier can report mismatches.
        atoms_by_segment = self._atoms_cache.get(expr_id)
        if atoms_by_segment is None:
            atoms_by_segment = _index_pattern_atoms(expr)
            self._atoms_cache[expr_id] = atoms_by_segment
        if segment_index < 0 or segment_index >= len(atoms_by_segment):
            return None
        segment_atoms = atoms_by_segment[segment_index]
        if atom_index < 0 or atom_index >= len(segment_atoms):
            return None
        atom = segment_atoms[atom_index]
        if atom.literal != literal:
            return None
        return PatternOrigin(
            expression_id=expr_id,
            segment_index=segment_index,
            base_name=atom.base_name,
            pattern_parts=atom.pattern_parts,
        )

    def collect_expr_ids(self, entity_ids: Iterable[str]) -> list[str]:
        """Collect ordered expression ids referenced by entity ids."""
        if self._pattern_origins is None:
            return []
        expr_ids: list[str] = []
        seen: set[str] = set()
        for entity_id in entity_ids:
            origin = self._pattern_origins.get(entity_id)
            if origin is None:
                continue
            expr_id = origin[0]
            if expr_id in seen:
                continue
            seen.add(expr_id)
            expr_ids.append(expr_id)
        return expr_ids

    def build_pattern_expression_table(
        self, expr_ids: Iterable[str]
    ) -> Optional[PatternExpressionTable]:
        """Build a module-local pattern expression table when possible."""
        if self._expr_registry is None or self._expr_kinds is None:
            return None
        entries: Dict[str, PatternExpressionEntry] = {}
        for expr_id in expr_ids:
            expr = self._expr_registry.get(expr_id)
            kind = self._expr_kinds.get(expr_id)
            if expr is None or kind is None:
                continue
            entries[expr_id] = PatternExpressionEntry(
                expression=expr.raw,
                kind=kind,
                span=expr.span,
            )
        return entries or None


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
        current: List[Tuple[str, list[str | int]]] = [("", [])]
        for token in segment.tokens:
            if isinstance(token, PatternLiteral):
                current = [
                    (value + token.text, parts) for value, parts in current
                ]
                continue
            if isinstance(token, PatternGroup):
                expanded: List[Tuple[str, list[str | int]]] = []
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


def build_netlist_ir_design(
    program: AtomizedProgramGraph,
    *,
    top_module_id: Optional[str] = None,
) -> NetlistDesign:
    """Lower an AtomizedGraph program into a NetlistIR design.

    Args:
        program: Atomized program graph to lower.
        top_module_id: Optional module ID to use as the design top.

    Returns:
        NetlistIR design for the atomized program.
    """
    top_module = None
    if top_module_id is not None:
        top_module = program.modules.get(top_module_id)
    elif len(program.modules) == 1:
        top_module = next(iter(program.modules.values()))

    pattern_resolver = _PatternOriginResolver(program.registries)

    modules = [
        _convert_module(module, program, pattern_resolver)
        for module in program.modules.values()
    ]
    devices = [
        _convert_device(device, program.registries)
        for device in program.devices.values()
    ]

    return NetlistDesign(
        modules=modules,
        devices=devices,
        top=top_module.name if top_module is not None else None,
        entry_file_id=top_module.file_id if top_module is not None else None,
    )


def _convert_module(
    module: AtomizedModuleGraph,
    program: AtomizedProgramGraph,
    pattern_resolver: _PatternOriginResolver,
) -> NetlistModule:
    """Convert an atomized module into a NetlistIR module."""
    conn_map: Dict[str, List[NetlistConn]] = {
        inst_id: [] for inst_id in module.instances
    }
    netlist_nets: List[NetlistNet] = []

    for net in module.nets.values():
        netlist_nets.append(
            NetlistNet(
                name=net.name,
                pattern_origin=pattern_resolver.resolve(
                    net.patterned_net_id, net.name, "net"
                ),
            )
        )
        for endpoint in _collect_net_endpoints(module, net):
            conn_map[endpoint.inst_id].append(
                NetlistConn(port=endpoint.port, net=net.name)
            )

    netlist_instances: List[NetlistInstance] = []
    for inst_id, instance in module.instances.items():
        ref_name, ref_file_id = _resolve_ref(instance, program)
        netlist_instances.append(
            NetlistInstance(
                name=instance.name,
                ref=ref_name,
                ref_file_id=ref_file_id,
                params=_to_string_dict(instance.param_values),
                conns=conn_map.get(inst_id, []),
                pattern_origin=pattern_resolver.resolve(
                    instance.patterned_inst_id, instance.name, "inst"
                ),
            )
        )

    expr_ids = pattern_resolver.collect_expr_ids(
        [
            entity_id
            for entity_id in (
                [net.patterned_net_id for net in module.nets.values()]
                + [inst.patterned_inst_id for inst in module.instances.values()]
            )
            if entity_id is not None
        ]
    )
    pattern_expression_table = pattern_resolver.build_pattern_expression_table(
        expr_ids
    )

    return NetlistModule(
        name=module.name,
        file_id=module.file_id,
        ports=list(module.ports or []),
        nets=netlist_nets,
        instances=netlist_instances,
        pattern_expression_table=pattern_expression_table,
    )


def _collect_net_endpoints(
    module: AtomizedModuleGraph,
    net: AtomizedNet,
) -> List[AtomizedEndpoint]:
    """Collect endpoints for a net in their declared order."""
    endpoints: List[AtomizedEndpoint] = []
    for endpoint_id in net.endpoint_ids:
        endpoint = module.endpoints.get(endpoint_id)
        if endpoint is not None:
            endpoints.append(endpoint)
    return endpoints


def _convert_device(
    device: AtomizedDeviceDef,
    registries: RegistrySet,
) -> NetlistDevice:
    """Convert an atomized device definition into a NetlistIR device."""
    backends: List[NetlistBackend] = []
    templates = (
        registries.device_backend_templates.get(device.device_id)
        if registries.device_backend_templates
        else None
    )
    if templates:
        for backend_name, template in templates.items():
            backends.append(
                NetlistBackend(
                    name=backend_name,
                    template=template,
                )
            )
    return NetlistDevice(
        name=device.name,
        file_id=device.file_id,
        ports=list(device.ports or []),
        params=_to_string_dict(device.parameters),
        variables=_to_string_dict(device.variables),
        backends=backends,
    )


def _resolve_ref(
    instance: AtomizedInstance,
    program: AtomizedProgramGraph,
) -> Tuple[str, str]:
    """Resolve instance references into NetlistIR symbol data."""
    if instance.ref_kind == "module":
        module = program.modules[instance.ref_id]
        return module.name, module.file_id
    device = program.devices[instance.ref_id]
    return device.name, device.file_id


def _to_string_dict(values: Optional[Dict[str, object]]) -> Optional[Dict[str, str]]:
    """Convert a dictionary to string values for NetlistIR."""
    if not values:
        return None
    return {key: _format_param_value(value) for key, value in values.items()}


def _format_param_value(value: object) -> str:
    """Format parameter values as strings."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


__all__ = ["build_netlist_ir_design"]
