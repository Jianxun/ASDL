from __future__ import annotations

from typing import Iterable, List, Sequence

from xdsl.dialects.builtin import (
    ArrayAttr,
    DictionaryAttr,
    FlatSymbolRefAttrConstr,
    LocationAttr,
    StringAttr,
    SymbolRefAttr,
)
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
class ConnAttr(ParametrizedAttribute):
    name = "asdl_ifir.conn"

    port: StringAttr = param_def()
    net: StringAttr = param_def()


@irdl_op_definition
class DesignOp(IRDLOperation):
    name = "asdl_ifir.design"

    top = opt_attr_def(StringAttr)
    doc = opt_attr_def(StringAttr)
    src = opt_attr_def(LocationAttr)
    body = region_def("single_block")

    traits = traits_def(IsolatedFromAbove(), NoTerminator())
    assembly_format = "$body attr-dict"

    def __init__(
        self,
        *,
        region: Region | Sequence[Operation],
        top: StringAttr | str | None = None,
        doc: StringAttr | str | None = None,
        src: LocationAttr | None = None,
    ):
        if isinstance(top, str):
            top = StringAttr(top)
        if isinstance(doc, str):
            doc = StringAttr(doc)
        attributes = {}
        if top is not None:
            attributes["top"] = top
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
            raise VerifyException("asdl_ifir.design region must contain only module/device ops")
        if self.top is not None and self.top.data not in module_names:
            raise VerifyException(f"Top module '{self.top.data}' is not defined")


@irdl_op_definition
class ModuleOp(IRDLOperation):
    name = "asdl_ifir.module"

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
                    raise VerifyException("IFIR net names must not start with '$'")
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
            raise VerifyException("asdl_ifir.module region must contain only net/instance ops")

        port_list = [attr.data for attr in self.port_order.data]
        if len(port_list) != len(set(port_list)):
            raise VerifyException("port_order must contain unique names")
        missing_ports = [name for name in port_list if name not in net_names]
        if missing_ports:
            missing_str = ", ".join(missing_ports)
            raise VerifyException(f"port_order references missing nets: {missing_str}")

        for instance in instances:
            if not instance.ref.root_reference.data:
                raise VerifyException("Instance ref must be non-empty")
            seen_ports: set[str] = set()
            for conn in instance.conns.data:
                port = conn.port.data
                if port in seen_ports:
                    raise VerifyException(
                        f"Instance '{instance.name_attr.data}' has duplicate port '{port}'"
                    )
                seen_ports.add(port)
                net_name = conn.net.data
                if net_name not in net_names:
                    raise VerifyException(
                        f"Instance '{instance.name_attr.data}' references unknown net '{net_name}'"
                    )


@irdl_op_definition
class NetOp(IRDLOperation):
    name = "asdl_ifir.net"

    name_attr = attr_def(StringAttr, attr_name="name")
    net_type = opt_attr_def(StringAttr)
    src = opt_attr_def(LocationAttr)

    assembly_format = "attr-dict"

    def __init__(
        self,
        *,
        name: StringAttr | str,
        net_type: StringAttr | str | None = None,
        src: LocationAttr | None = None,
    ):
        if isinstance(name, str):
            name = StringAttr(name)
        if isinstance(net_type, str):
            net_type = StringAttr(net_type)
        attributes = {"name": name}
        if net_type is not None:
            attributes["net_type"] = net_type
        if src is not None:
            attributes["src"] = src
        super().__init__(attributes=attributes)


@irdl_op_definition
class InstanceOp(IRDLOperation):
    name = "asdl_ifir.instance"

    name_attr = attr_def(StringAttr, attr_name="name")
    ref = attr_def(FlatSymbolRefAttrConstr)
    params = opt_attr_def(DictionaryAttr)
    conns = attr_def(ArrayAttr[ConnAttr])
    doc = opt_attr_def(StringAttr)
    src = opt_attr_def(LocationAttr)

    assembly_format = "attr-dict"

    def __init__(
        self,
        *,
        name: StringAttr | str,
        ref: SymbolRefAttr | str,
        conns: ArrayAttr[ConnAttr] | Iterable[ConnAttr],
        params: DictionaryAttr | None = None,
        doc: StringAttr | str | None = None,
        src: LocationAttr | None = None,
    ):
        if isinstance(name, str):
            name = StringAttr(name)
        if isinstance(ref, str):
            ref = SymbolRefAttr(ref)
        if isinstance(doc, str):
            doc = StringAttr(doc)
        if not isinstance(conns, ArrayAttr):
            conns = ArrayAttr(list(conns))
        attributes = {
            "name": name,
            "ref": ref,
            "conns": conns,
        }
        if params is not None:
            attributes["params"] = params
        if doc is not None:
            attributes["doc"] = doc
        if src is not None:
            attributes["src"] = src
        super().__init__(attributes=attributes)


@irdl_op_definition
class DeviceOp(IRDLOperation):
    name = "asdl_ifir.device"

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
                raise VerifyException("asdl_ifir.device region must contain only backend ops")
            name = op.name_attr.data
            if name in backend_names:
                raise VerifyException(f"Duplicate backend name '{name}' in device")
            backend_names.add(name)


@irdl_op_definition
class BackendOp(IRDLOperation):
    name = "asdl_ifir.backend"

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


ASDL_IFIR = Dialect(
    "asdl_ifir",
    [
        DesignOp,
        ModuleOp,
        NetOp,
        InstanceOp,
        DeviceOp,
        BackendOp,
    ],
    [ConnAttr],
)


__all__ = [
    "ASDL_IFIR",
    "BackendOp",
    "ConnAttr",
    "DesignOp",
    "DeviceOp",
    "InstanceOp",
    "ModuleOp",
    "NetOp",
]
