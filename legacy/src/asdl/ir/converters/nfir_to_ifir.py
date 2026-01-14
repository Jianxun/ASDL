from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from xdsl.dialects.builtin import (
    ArrayAttr,
    DictionaryAttr,
    LocationAttr,
    StringAttr,
    SymbolRefAttr,
)

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
from asdl.ir.nfir import (
    BackendOp as NfirBackendOp,
    DesignOp as NfirDesignOp,
    DeviceOp as NfirDeviceOp,
    InstanceOp as NfirInstanceOp,
    ModuleOp as NfirModuleOp,
    NetOp as NfirNetOp,
)
from asdl.ir.location import location_attr_to_span
from asdl.patterns import (
    AtomizedEndpoint,
    AtomizedPattern,
    atomize_endpoint,
    atomize_pattern,
)

INVALID_NFIR_DESIGN = format_code("IR", 3)
INVALID_NFIR_DEVICE = format_code("IR", 4)
UNKNOWN_ENDPOINT_INSTANCE = format_code("IR", 5)
PATTERN_BINDING_MISMATCH = format_code("IR", 6)
NO_SPAN_NOTE = "No source span available."


def convert_design(
    design: NfirDesignOp,
) -> Tuple[Optional[DesignOp], List[Diagnostic]]:
    diagnostics: List[Diagnostic] = []
    had_error = False
    modules: List[ModuleOp] = []
    devices: List[DeviceOp] = []

    for op in design.body.block.ops:
        if isinstance(op, NfirModuleOp):
            module, module_diags, module_error = _convert_module(op)
            diagnostics.extend(module_diags)
            had_error = had_error or module_error
            modules.append(module)
            continue
        if isinstance(op, NfirDeviceOp):
            device, device_diags, device_error = _convert_device(op)
            diagnostics.extend(device_diags)
            had_error = had_error or device_error
            devices.append(device)
            continue
        diagnostics.append(
            _diagnostic(
                INVALID_NFIR_DESIGN,
                "asdl_nfir.design contains non-module/device ops",
                getattr(op, "src", None),
            )
        )
        had_error = True

    design_op = DesignOp(
        region=[*modules, *devices],
        top=design.top,
        entry_file_id=design.entry_file_id,
    )
    if had_error:
        return None, diagnostics
    return design_op, diagnostics


def _convert_module(
    module: NfirModuleOp,
) -> Tuple[ModuleOp, List[Diagnostic], bool]:
    diagnostics: List[Diagnostic] = []
    had_error = False
    nfir_nets: List[NfirNetOp] = []
    nfir_instances: List[NfirInstanceOp] = []

    for op in module.body.block.ops:
        if isinstance(op, NfirNetOp):
            nfir_nets.append(op)
            continue
        if isinstance(op, NfirInstanceOp):
            nfir_instances.append(op)
            continue
        diagnostics.append(
            _diagnostic(
                INVALID_NFIR_DESIGN,
                "asdl_nfir.module contains non-net/instance ops",
                getattr(op, "src", None) or module.src,
            )
        )
        had_error = True

    net_ops: List[NetOp] = []
    port_order: List[str] = []
    net_cache: Dict[str, List[AtomizedPattern] | None] = {}
    endpoint_cache: Dict[Tuple[str, str], List[AtomizedEndpoint] | None] = {}
    inst_cache: Dict[str, List[AtomizedPattern] | None] = {}

    pattern_diags, pattern_error = _verify_pattern_bindings(
        module,
        nfir_nets,
        net_cache=net_cache,
        endpoint_cache=endpoint_cache,
    )
    diagnostics.extend(pattern_diags)
    had_error = had_error or pattern_error

    for port_attr in module.port_order.data:
        token = port_attr.data
        atoms = _atomize_pattern_cached(token, net_cache, diagnostics)
        if atoms is None:
            had_error = True
            continue
        port_order.extend(atom.literal for atom in atoms)

    inst_literal_map: Dict[str, str] = {}
    inst_atoms: List[str] = []
    inst_order: List[Tuple[NfirInstanceOp, List[AtomizedPattern]]] = []
    for inst in nfir_instances:
        token = inst.name_attr.data
        atoms = _atomize_pattern_cached(token, inst_cache, diagnostics)
        if atoms is None:
            had_error = True
            atoms = []
        inst_order.append((inst, atoms))
        for atom in atoms:
            inst_atoms.append(atom.literal)
            inst_literal_map.setdefault(atom.literal, atom.literal)

    for net in nfir_nets:
        net_name = net.name_attr.data
        atoms = _atomize_pattern_cached(net_name, net_cache, diagnostics)
        if atoms is None:
            had_error = True
            continue
        for atom in atoms:
            net_ops.append(
                NetOp(
                    name=atom.literal,
                    pattern_origin=atom.origin,
                    src=net.src,
                )
            )

    conn_map: Dict[str, List[ConnAttr]] = {atom: [] for atom in inst_atoms}
    param_map: Dict[str, Optional[DictionaryAttr]] = {}

    for inst, atoms in inst_order:
        params_per_atom, params_error = _atomize_instance_params(
            inst, atoms, diagnostics, inst.src or module.src
        )
        had_error = had_error or params_error
        for atom, params in zip(atoms, params_per_atom):
            param_map[atom.literal] = params

    for net in nfir_nets:
        net_token = net.name_attr.data
        net_atoms = _atomize_pattern_cached(net_token, net_cache, diagnostics)
        if net_atoms is None:
            had_error = True
            continue
        for endpoint in net.endpoints.data:
            endpoint_atoms = _atomize_endpoint_cached(
                (endpoint.inst.data, endpoint.pin.data),
                endpoint_cache,
                diagnostics,
            )
            if endpoint_atoms is None:
                had_error = True
                continue
            if len(net_atoms) > 1 and len(endpoint_atoms) != len(net_atoms):
                had_error = True
                continue
            if len(net_atoms) == 1:
                net_name = net_atoms[0].literal
                owners: List[str] = []
                for atom in endpoint_atoms:
                    owner = inst_literal_map.get(atom.inst.literal)
                    if owner is None:
                        diagnostics.append(
                            _diagnostic(
                                UNKNOWN_ENDPOINT_INSTANCE,
                                (
                                    "Endpoint references unknown instance "
                                    f"'{endpoint.inst.data}'"
                                ),
                                net.src or module.src,
                            )
                        )
                        had_error = True
                        owners = []
                        break
                    owners.append(owner)
                if not owners:
                    continue
                for owner, atom in zip(owners, endpoint_atoms):
                    conn_map[owner].append(
                        ConnAttr(StringAttr(atom.pin.literal), StringAttr(net_name))
                    )
                continue
            owners: List[str] = []
            for endpoint_atom in endpoint_atoms:
                owner = inst_literal_map.get(endpoint_atom.inst.literal)
                if owner is None:
                    diagnostics.append(
                        _diagnostic(
                            UNKNOWN_ENDPOINT_INSTANCE,
                            (
                                "Endpoint references unknown instance "
                                f"'{endpoint.inst.data}'"
                            ),
                            net.src or module.src,
                        )
                    )
                    had_error = True
                    owners = []
                    break
                owners.append(owner)
            if not owners:
                continue
            for net_atom, endpoint_atom, owner in zip(net_atoms, endpoint_atoms, owners):
                conn_map[owner].append(
                    ConnAttr(
                        StringAttr(endpoint_atom.pin.literal),
                        StringAttr(net_atom.literal),
                    )
                )

    inst_ops: List[InstanceOp] = []
    for inst, atoms in inst_order:
        for atom in atoms:
            conns = conn_map.get(atom.literal, [])
            inst_ops.append(
                InstanceOp(
                    name=atom.literal,
                    ref=SymbolRefAttr(inst.ref.data),
                    conns=ArrayAttr(conns),
                    ref_file_id=inst.ref_file_id,
                    params=param_map.get(atom.literal),
                    pattern_origin=atom.origin,
                    doc=inst.doc,
                    src=inst.src,
                )
            )

    return (
        ModuleOp(
            name=module.sym_name,
            port_order=port_order,
            region=[*net_ops, *inst_ops],
            file_id=module.file_id,
            doc=module.doc,
            src=module.src,
        ),
        diagnostics,
        had_error,
    )


def _convert_device(
    device: NfirDeviceOp,
) -> Tuple[DeviceOp, List[Diagnostic], bool]:
    diagnostics: List[Diagnostic] = []
    had_error = False
    backends: List[BackendOp] = []
    for backend in device.body.block.ops:
        if not isinstance(backend, NfirBackendOp):
            diagnostics.append(
                _diagnostic(
                    INVALID_NFIR_DEVICE,
                    "asdl_nfir.device contains non-backend ops",
                    getattr(backend, "src", None) or device.src,
                )
            )
            had_error = True
            continue
        backends.append(
            BackendOp(
                name=backend.name_attr,
                template=backend.template,
                params=backend.params,
                props=backend.props,
                src=backend.src,
            )
        )

    return (
        DeviceOp(
        name=device.sym_name,
        ports=device.ports,
        file_id=device.file_id,
        params=device.params,
        region=backends,
        doc=device.doc,
        src=device.src,
        ),
        diagnostics,
        had_error,
    )


def _diagnostic(
    code: str, message: str, loc: LocationAttr | None = None
) -> Diagnostic:
    span = location_attr_to_span(loc)
    notes = None if span is not None else [NO_SPAN_NOTE]
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        message=message,
        primary_span=span,
        notes=notes,
        source="ir",
    )


def _verify_pattern_bindings(
    module: NfirModuleOp,
    nets: List[NfirNetOp],
    *,
    net_cache: Dict[str, List[AtomizedPattern] | None],
    endpoint_cache: Dict[Tuple[str, str], List[AtomizedEndpoint] | None],
) -> Tuple[List[Diagnostic], bool]:
    diagnostics: List[Diagnostic] = []
    had_error = False

    for net in nets:
        net_token = net.name_attr.data
        net_atoms = _atomize_pattern_cached(net_token, net_cache, diagnostics)
        if net_atoms is None:
            had_error = True
            continue
        net_len = len(net_atoms)

        for endpoint in net.endpoints.data:
            endpoint_token = f"{endpoint.inst.data}.{endpoint.pin.data}"
            endpoint_atoms = _atomize_endpoint_cached(
                (endpoint.inst.data, endpoint.pin.data),
                endpoint_cache,
                diagnostics,
            )
            if endpoint_atoms is None:
                had_error = True
                continue
            endpoint_len = len(endpoint_atoms)
            if net_len > 1 and endpoint_len != net_len:
                diagnostics.append(
                    _diagnostic(
                        PATTERN_BINDING_MISMATCH,
                        (
                            f"Net '{net_token}' expands to {net_len} atoms but "
                            f"endpoint '{endpoint_token}' expands to {endpoint_len}"
                        ),
                        net.src or module.src,
                    )
                )
                had_error = True

    return diagnostics, had_error


def _atomize_pattern_cached(
    token: str,
    cache: Dict[str, List[AtomizedPattern] | None],
    diagnostics: List[Diagnostic],
) -> List[AtomizedPattern] | None:
    if token in cache:
        return cache[token]
    atoms, diags = atomize_pattern(token)
    diagnostics.extend(diags)
    cache[token] = atoms
    return atoms


def _atomize_endpoint_cached(
    key: Tuple[str, str],
    cache: Dict[Tuple[str, str], List[AtomizedEndpoint] | None],
    diagnostics: List[Diagnostic],
) -> List[AtomizedEndpoint] | None:
    if key in cache:
        return cache[key]
    atoms, diags = atomize_endpoint(*key)
    diagnostics.extend(diags)
    cache[key] = atoms
    return atoms


def _atomize_instance_params(
    inst: NfirInstanceOp,
    atoms: List[AtomizedPattern],
    diagnostics: List[Diagnostic],
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
            diagnostics.append(
                _diagnostic(
                    PATTERN_BINDING_MISMATCH,
                    (
                        f"Instance '{inst.name_attr.data}' parameter '{key}' atomizes to "
                        f"{len(expanded)} values but instance atomizes to {instance_len}"
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


__all__ = ["convert_design"]
