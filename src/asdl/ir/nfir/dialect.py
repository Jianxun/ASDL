from __future__ import annotations

from typing import Dict, Iterable, List, Sequence, Tuple

from xdsl.dialects.builtin import ArrayAttr, DictionaryAttr, LocationAttr, StringAttr
from xdsl.ir import Block, Dialect, Operation, ParametrizedAttribute, Region
from xdsl.irdl import (
    IRDLOperation,
    attr_def,
    irdl_attr_definition,
    irdl_op_definition,
    opt_attr_def,
    param_def,
    region_def,
    traits_def,
)
from xdsl.traits import IsolatedFromAbove, NoTerminator
from xdsl.utils.exceptions import VerifyException

from asdl.ir.patterns import (
    AtomizedEndpoint,
    AtomizedPattern,
    atomize_endpoint,
    atomize_pattern,
)

@irdl_attr_definition
class EndpointAttr(ParametrizedAttribute):
    name = "asdl_nfir.endpoint"

    inst: StringAttr = param_def()
    pin: StringAttr = param_def()


@irdl_op_definition
class DesignOp(IRDLOperation):
    name = "asdl_nfir.design"

    top = opt_attr_def(StringAttr)
    entry_file_id = opt_attr_def(StringAttr)
    body = region_def("single_block")

    traits = traits_def(IsolatedFromAbove(), NoTerminator())
    assembly_format = "$body attr-dict"

    def __init__(
        self,
        *,
        region: Region | Sequence[Operation],
        top: StringAttr | str | None = None,
        entry_file_id: StringAttr | str | None = None,
    ):
        if isinstance(top, str):
            top = StringAttr(top)
        if isinstance(entry_file_id, str):
            entry_file_id = StringAttr(entry_file_id)
        attributes = {}
        if top is not None:
            attributes["top"] = top
        if entry_file_id is not None:
            attributes["entry_file_id"] = entry_file_id
        if isinstance(region, Region):
            body = region
        else:
            body = Region(Block(region))
        super().__init__(attributes=attributes, regions=[body])

    def verify_(self) -> None:
        module_names: dict[str | None, set[str]] = {}
        device_names: dict[str | None, set[str]] = {}
        all_module_names: set[str] = set()
        entry_module_names: set[str] = set()
        entry_file_id = (
            self.entry_file_id.data if self.entry_file_id is not None else None
        )
        for op in self.body.block.ops:
            if isinstance(op, ModuleOp):
                name = op.sym_name.data
                file_id = op.file_id.data if op.file_id is not None else None
                names = module_names.setdefault(file_id, set())
                if name in names:
                    raise VerifyException(f"Duplicate module name '{name}'")
                names.add(name)
                all_module_names.add(name)
                if entry_file_id is not None and file_id == entry_file_id:
                    entry_module_names.add(name)
                continue
            if isinstance(op, DeviceOp):
                name = op.sym_name.data
                file_id = op.file_id.data if op.file_id is not None else None
                names = device_names.setdefault(file_id, set())
                if name in names:
                    raise VerifyException(f"Duplicate device name '{name}'")
                names.add(name)
                continue
            raise VerifyException("asdl_nfir.design region must contain only module/device ops")
        if self.top is None:
            return
        if entry_file_id is None:
            if self.top.data not in all_module_names:
                raise VerifyException(f"Top module '{self.top.data}' is not defined")
            return
        if self.top.data not in entry_module_names:
            raise VerifyException(
                f"Top module '{self.top.data}' is not defined in entry file"
            )


@irdl_op_definition
class ModuleOp(IRDLOperation):
    name = "asdl_nfir.module"

    sym_name = attr_def(StringAttr)
    port_order = attr_def(ArrayAttr[StringAttr])
    file_id = opt_attr_def(StringAttr)
    doc = opt_attr_def(StringAttr)
    src = opt_attr_def(LocationAttr)
    body = region_def("single_block")

    traits = traits_def(IsolatedFromAbove(), NoTerminator())
    assembly_format = "$body attr-dict"

    def __init__(
        self,
        *,
        name: StringAttr | str,
        port_order: ArrayAttr[StringAttr] | Iterable[str],
        region: Region | Sequence[Operation],
        file_id: StringAttr | str | None = None,
        doc: StringAttr | str | None = None,
        src: LocationAttr | None = None,
    ):
        if isinstance(name, str):
            name = StringAttr(name)
        if isinstance(doc, str):
            doc = StringAttr(doc)
        if isinstance(file_id, str):
            file_id = StringAttr(file_id)
        if not isinstance(port_order, ArrayAttr):
            port_order = ArrayAttr([StringAttr(item) for item in port_order])
        attributes = {
            "sym_name": name,
            "port_order": port_order,
        }
        if file_id is not None:
            attributes["file_id"] = file_id
        if doc is not None:
            attributes["doc"] = doc
        if src is not None:
            attributes["src"] = src
        if isinstance(region, Region):
            body = region
        else:
            body = Region(Block(region))
        super().__init__(attributes=attributes, regions=[body])

    def verify_(self) -> None:
        net_names: set[str] = set()
        inst_names: set[str] = set()
        nets: List[NetOp] = []
        instances: List[InstanceOp] = []

        for op in self.body.block.ops:
            if isinstance(op, NetOp):
                name = op.name_attr.data
                if name in net_names:
                    raise VerifyException(f"Duplicate net name '{name}' in module")
                if name.startswith("$"):
                    raise VerifyException("NFIR net names must not start with '$'")
                net_names.add(name)
                nets.append(op)
                continue
            if isinstance(op, InstanceOp):
                name = op.name_attr.data
                if name in inst_names:
                    raise VerifyException(f"Duplicate instance name '{name}' in module")
                inst_names.add(name)
                instances.append(op)
                continue
            raise VerifyException("asdl_nfir.module region must contain only net/instance ops")

        port_list = [attr.data for attr in self.port_order.data]
        if len(port_list) != len(set(port_list)):
            raise VerifyException("port_order must contain unique names")
        missing_ports = [name for name in port_list if name not in net_names]
        if missing_ports:
            missing_str = ", ".join(missing_ports)
            raise VerifyException(f"port_order references missing nets: {missing_str}")

        instance_literals: set[str] = set()
        instance_cache: Dict[str, List[AtomizedPattern] | None] = {}
        for inst in instances:
            token = inst.name_attr.data
            if token not in instance_cache:
                atoms, diags = atomize_pattern(token)
                instance_cache[token] = atoms
                if atoms is None:
                    message = diags[0].message if diags else f"Invalid instance token '{token}'"
                    raise VerifyException(message)
            atoms = instance_cache[token]
            if atoms is None:
                continue
            for atom in atoms:
                instance_literals.add(atom.literal)

        endpoint_pairs: set[tuple[str, str]] = set()
        endpoint_cache: Dict[Tuple[str, str], List[AtomizedEndpoint] | None] = {}
        for net in nets:
            for endpoint in net.endpoints.data:
                inst = endpoint.inst.data
                pin = endpoint.pin.data
                key = (inst, pin)
                if key not in endpoint_cache:
                    atoms, diags = atomize_endpoint(inst, pin)
                    endpoint_cache[key] = atoms
                    if atoms is None:
                        message = diags[0].message if diags else f"Invalid endpoint '{inst}.{pin}'"
                        raise VerifyException(message)
                atoms = endpoint_cache[key]
                if atoms is None:
                    continue
                for atom in atoms:
                    inst_literal = atom.inst
                    port_literal = atom.port
                    pair = (inst_literal, port_literal)
                    if pair in endpoint_pairs:
                        raise VerifyException(
                            f"Endpoint {inst_literal}.{port_literal} appears on more than one net"
                        )
                    endpoint_pairs.add(pair)
                    if inst_literal not in instance_literals:
                        raise VerifyException(
                            f"Endpoint references unknown instance '{inst_literal}'"
                        )

        for instance in instances:
            if not instance.ref.data:
                raise VerifyException("Instance ref must be non-empty")


@irdl_op_definition
class NetOp(IRDLOperation):
    name = "asdl_nfir.net"

    name_attr = attr_def(StringAttr, attr_name="name")
    endpoints = attr_def(ArrayAttr[EndpointAttr])
    src = opt_attr_def(LocationAttr)

    assembly_format = "attr-dict"

    def __init__(
        self,
        *,
        name: StringAttr | str,
        endpoints: ArrayAttr[EndpointAttr] | Iterable[EndpointAttr],
        src: LocationAttr | None = None,
    ):
        if isinstance(name, str):
            name = StringAttr(name)
        if not isinstance(endpoints, ArrayAttr):
            endpoints = ArrayAttr(list(endpoints))
        attributes = {"name": name, "endpoints": endpoints}
        if src is not None:
            attributes["src"] = src
        super().__init__(attributes=attributes)


@irdl_op_definition
class InstanceOp(IRDLOperation):
    name = "asdl_nfir.instance"

    name_attr = attr_def(StringAttr, attr_name="name")
    ref = attr_def(StringAttr)
    ref_file_id = opt_attr_def(StringAttr)
    params = opt_attr_def(DictionaryAttr)
    doc = opt_attr_def(StringAttr)
    src = opt_attr_def(LocationAttr)

    assembly_format = "attr-dict"

    def __init__(
        self,
        *,
        name: StringAttr | str,
        ref: StringAttr | str,
        ref_file_id: StringAttr | str | None = None,
        params: DictionaryAttr | None = None,
        doc: StringAttr | str | None = None,
        src: LocationAttr | None = None,
    ):
        if isinstance(name, str):
            name = StringAttr(name)
        if isinstance(ref, str):
            ref = StringAttr(ref)
        if isinstance(ref_file_id, str):
            ref_file_id = StringAttr(ref_file_id)
        if isinstance(doc, str):
            doc = StringAttr(doc)
        attributes = {
            "name": name,
            "ref": ref,
        }
        if ref_file_id is not None:
            attributes["ref_file_id"] = ref_file_id
        if params is not None:
            attributes["params"] = params
        if doc is not None:
            attributes["doc"] = doc
        if src is not None:
            attributes["src"] = src
        super().__init__(attributes=attributes)


@irdl_op_definition
class DeviceOp(IRDLOperation):
    name = "asdl_nfir.device"

    sym_name = attr_def(StringAttr)
    ports = attr_def(ArrayAttr[StringAttr])
    file_id = opt_attr_def(StringAttr)
    params = opt_attr_def(DictionaryAttr)
    doc = opt_attr_def(StringAttr)
    src = opt_attr_def(LocationAttr)
    body = region_def("single_block")

    traits = traits_def(IsolatedFromAbove(), NoTerminator())
    assembly_format = "$body attr-dict"

    def __init__(
        self,
        *,
        name: StringAttr | str,
        ports: ArrayAttr[StringAttr] | Iterable[str],
        region: Region | Sequence[Operation],
        file_id: StringAttr | str | None = None,
        params: DictionaryAttr | None = None,
        doc: StringAttr | str | None = None,
        src: LocationAttr | None = None,
    ):
        if isinstance(name, str):
            name = StringAttr(name)
        if isinstance(doc, str):
            doc = StringAttr(doc)
        if isinstance(file_id, str):
            file_id = StringAttr(file_id)
        if not isinstance(ports, ArrayAttr):
            ports = ArrayAttr([StringAttr(item) for item in ports])
        attributes = {"sym_name": name, "ports": ports}
        if file_id is not None:
            attributes["file_id"] = file_id
        if params is not None:
            attributes["params"] = params
        if doc is not None:
            attributes["doc"] = doc
        if src is not None:
            attributes["src"] = src
        if isinstance(region, Region):
            body = region
        else:
            body = Region(Block(region))
        super().__init__(attributes=attributes, regions=[body])

    def verify_(self) -> None:
        backend_names: set[str] = set()
        for op in self.body.block.ops:
            if not isinstance(op, BackendOp):
                raise VerifyException("asdl_nfir.device region must contain only backend ops")
            name = op.name_attr.data
            if name in backend_names:
                raise VerifyException(f"Duplicate backend name '{name}' in device")
            backend_names.add(name)


@irdl_op_definition
class BackendOp(IRDLOperation):
    name = "asdl_nfir.backend"

    name_attr = attr_def(StringAttr, attr_name="name")
    template = attr_def(StringAttr)
    params = opt_attr_def(DictionaryAttr)
    props = opt_attr_def(DictionaryAttr)
    src = opt_attr_def(LocationAttr)

    assembly_format = "attr-dict"

    def __init__(
        self,
        *,
        name: StringAttr | str,
        template: StringAttr | str,
        params: DictionaryAttr | None = None,
        props: DictionaryAttr | None = None,
        src: LocationAttr | None = None,
    ):
        if isinstance(name, str):
            name = StringAttr(name)
        if isinstance(template, str):
            template = StringAttr(template)
        attributes = {"name": name, "template": template}
        if params is not None:
            attributes["params"] = params
        if props is not None:
            attributes["props"] = props
        if src is not None:
            attributes["src"] = src
        super().__init__(attributes=attributes)


ASDL_NFIR = Dialect(
    "asdl_nfir",
    [
        DesignOp,
        ModuleOp,
        NetOp,
        InstanceOp,
        DeviceOp,
        BackendOp,
    ],
    [EndpointAttr],
)


__all__ = [
    "ASDL_NFIR",
    "BackendOp",
    "DesignOp",
    "DeviceOp",
    "EndpointAttr",
    "InstanceOp",
    "ModuleOp",
    "NetOp",
]
