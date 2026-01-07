from __future__ import annotations

from typing import Iterable, List, Sequence

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


@irdl_attr_definition
class EndpointAttr(ParametrizedAttribute):
    name = "asdl_nfir.endpoint"

    inst: StringAttr = param_def()
    pin: StringAttr = param_def()


@irdl_op_definition
class DesignOp(IRDLOperation):
    name = "asdl_nfir.design"

    top = opt_attr_def(StringAttr)
    body = region_def("single_block")

    traits = traits_def(IsolatedFromAbove(), NoTerminator())
    assembly_format = "$body attr-dict"

    def __init__(
        self,
        *,
        region: Region | Sequence[Operation],
        top: StringAttr | str | None = None,
    ):
        if isinstance(top, str):
            top = StringAttr(top)
        attributes = {}
        if top is not None:
            attributes["top"] = top
        if isinstance(region, Region):
            body = region
        else:
            body = Region(Block(region))
        super().__init__(attributes=attributes, regions=[body])

    def verify_(self) -> None:
        module_names: set[str] = set()
        device_names: set[str] = set()
        for op in self.body.block.ops:
            if isinstance(op, ModuleOp):
                name = op.sym_name.data
                if name in module_names:
                    raise VerifyException(f"Duplicate module name '{name}'")
                module_names.add(name)
                continue
            if isinstance(op, DeviceOp):
                name = op.sym_name.data
                if name in device_names:
                    raise VerifyException(f"Duplicate device name '{name}'")
                device_names.add(name)
                continue
            raise VerifyException("asdl_nfir.design region must contain only module/device ops")
        if self.top is not None and self.top.data not in module_names:
            raise VerifyException(f"Top module '{self.top.data}' is not defined")


@irdl_op_definition
class ModuleOp(IRDLOperation):
    name = "asdl_nfir.module"

    sym_name = attr_def(StringAttr)
    port_order = attr_def(ArrayAttr[StringAttr])
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
        doc: StringAttr | str | None = None,
        src: LocationAttr | None = None,
    ):
        if isinstance(name, str):
            name = StringAttr(name)
        if isinstance(doc, str):
            doc = StringAttr(doc)
        if not isinstance(port_order, ArrayAttr):
            port_order = ArrayAttr([StringAttr(item) for item in port_order])
        attributes = {
            "sym_name": name,
            "port_order": port_order,
        }
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

        endpoint_pairs: set[tuple[str, str]] = set()
        for net in nets:
            for endpoint in net.endpoints.data:
                inst = endpoint.inst.data
                pin = endpoint.pin.data
                pair = (inst, pin)
                if pair in endpoint_pairs:
                    raise VerifyException(
                        f"Endpoint {inst}.{pin} appears on more than one net"
                    )
                endpoint_pairs.add(pair)
                if inst not in inst_names:
                    raise VerifyException(f"Endpoint references unknown instance '{inst}'")

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
        params: DictionaryAttr | None = None,
        doc: StringAttr | str | None = None,
        src: LocationAttr | None = None,
    ):
        if isinstance(name, str):
            name = StringAttr(name)
        if isinstance(doc, str):
            doc = StringAttr(doc)
        if not isinstance(ports, ArrayAttr):
            ports = ArrayAttr([StringAttr(item) for item in ports])
        attributes = {"sym_name": name, "ports": ports}
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
