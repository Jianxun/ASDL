from __future__ import annotations

from collections.abc import Iterable, Sequence

from xdsl.dialects.builtin import (
    ArrayAttr,
    DictionaryAttr,
    FileLineColLoc,
    FlatSymbolRefAttrConstr,
    StringAttr,
    SymbolNameConstraint,
    SymbolRefAttr,
    UnknownLoc,
    BoolAttr,
    IntegerAttr,
)
from xdsl.ir import Block, Dialect, Operation, ParametrizedAttribute, Region
from xdsl.irdl import (
    AnyOf,
    BaseAttr,
    IRDLOperation,
    irdl_attr_definition,
    irdl_op_definition,
    opt_prop_def,
    prop_def,
    region_def,
    traits_def,
)
from xdsl.traits import IsolatedFromAbove, NoTerminator, SymbolOpInterface, SymbolTable
from xdsl.utils.exceptions import VerifyException

_ALLOWED_VIEW_KINDS = {"subckt", "subckt_ref", "primitive", "dummy", "behav"}
_ALLOWED_PORT_DIRS = {"in", "out", "in_out"}
_ALLOWED_TOP_MODES = {"subckt", "flat"}

LocAttrConstraint = AnyOf([BaseAttr(UnknownLoc), BaseAttr(FileLineColLoc)])


@irdl_attr_definition
class ExprAttr(ParametrizedAttribute):
    name = "asdl.expr"

    text: StringAttr

    def __init__(self, text: str | StringAttr) -> None:
        if isinstance(text, str):
            text = StringAttr(text)
        super().__init__(text)


@irdl_attr_definition
class ConnAttr(ParametrizedAttribute):
    name = "asdl.conn"

    port: StringAttr
    net: StringAttr

    def __init__(self, port: str | StringAttr, net: str | StringAttr) -> None:
        if isinstance(port, str):
            port = StringAttr(port)
        if isinstance(net, str):
            net = StringAttr(net)
        super().__init__(port, net)


@irdl_op_definition
class DesignOp(IRDLOperation):
    name = "asdl.design"

    doc = opt_prop_def(StringAttr)
    top = opt_prop_def(StringAttr)
    top_mode = opt_prop_def(StringAttr)
    unit_name = opt_prop_def(StringAttr)
    src = opt_prop_def(LocAttrConstraint)

    body = region_def("single_block")

    traits = traits_def(IsolatedFromAbove(), NoTerminator(), SymbolTable())

    def __init__(
        self,
        *,
        region: Region | type[Region.DEFAULT] = Region.DEFAULT,
        doc: str | StringAttr | None = None,
        top: str | StringAttr | None = None,
        top_mode: str | StringAttr | None = None,
        unit_name: str | StringAttr | None = None,
        src: UnknownLoc | FileLineColLoc | None = None,
    ) -> None:
        if not isinstance(region, Region):
            region = Region(Block())
        properties: dict[str, object | None] = {
            "doc": _maybe_string_attr(doc),
            "top": _maybe_string_attr(top),
            "top_mode": _maybe_string_attr(top_mode),
            "unit_name": _maybe_string_attr(unit_name),
            "src": src,
        }
        super().__init__(properties=properties, regions=[region])

    def verify_(self) -> None:
        if self.top_mode is not None and self.top_mode.data not in _ALLOWED_TOP_MODES:
            raise VerifyException(
                f"top_mode must be one of {_ALLOWED_TOP_MODES}, got '{self.top_mode.data}'"
            )

        import_names: set[str] = set()
        for op in self.body.block.ops:
            if isinstance(op, ImportOp):
                name = op.as_name.data
                if name in import_names:
                    raise VerifyException(f"duplicate import alias '{name}' in design")
                import_names.add(name)
                continue
            if isinstance(op, ModuleOp):
                continue
            raise VerifyException(
                f"unexpected op '{op.name}' in asdl.design; expected import or module"
            )


@irdl_op_definition
class ImportOp(IRDLOperation):
    name = "asdl.import"

    as_name = prop_def(StringAttr)
    from_ = prop_def(StringAttr, prop_name="from")
    items = opt_prop_def(ArrayAttr[StringAttr])
    src = opt_prop_def(LocAttrConstraint)

    def __init__(
        self,
        *,
        as_name: str | StringAttr,
        from_: str | StringAttr,
        items: Iterable[str | StringAttr] | ArrayAttr[StringAttr] | None = None,
        src: UnknownLoc | FileLineColLoc | None = None,
    ) -> None:
        if isinstance(as_name, str):
            as_name = StringAttr(as_name)
        if isinstance(from_, str):
            from_ = StringAttr(from_)
        if items is not None and not isinstance(items, ArrayAttr):
            items = ArrayAttr([StringAttr(item) if isinstance(item, str) else item for item in items])
        properties: dict[str, object | None] = {
            "as_name": as_name,
            "from": from_,
            "items": items,
            "src": src,
        }
        super().__init__(properties=properties)


@irdl_op_definition
class ModuleOp(IRDLOperation):
    name = "asdl.module"

    sym_name = prop_def(SymbolNameConstraint())
    doc = opt_prop_def(StringAttr)
    port_order = prop_def(ArrayAttr[StringAttr])
    src = opt_prop_def(LocAttrConstraint)

    body = region_def("single_block")

    traits = traits_def(IsolatedFromAbove(), NoTerminator(), SymbolTable(), SymbolOpInterface())

    def __init__(
        self,
        name: str | StringAttr,
        port_order: Iterable[str | StringAttr] | ArrayAttr[StringAttr],
        *,
        region: Region | type[Region.DEFAULT] = Region.DEFAULT,
        doc: str | StringAttr | None = None,
        src: UnknownLoc | FileLineColLoc | None = None,
    ) -> None:
        if isinstance(name, str):
            name = StringAttr(name)
        if not isinstance(port_order, ArrayAttr):
            port_order = ArrayAttr(
                [StringAttr(item) if isinstance(item, str) else item for item in port_order]
            )
        if not isinstance(region, Region):
            region = Region(Block())
        properties: dict[str, object | None] = {
            "sym_name": name,
            "doc": _maybe_string_attr(doc),
            "port_order": port_order,
            "src": src,
        }
        super().__init__(properties=properties, regions=[region])

    def verify_(self) -> None:
        port_names: list[str] = []
        for op in self.body.block.ops:
            if isinstance(op, PortOp):
                port_names.append(op.name_.data)
                continue
            if isinstance(op, ViewOp):
                continue
            raise VerifyException(
                f"unexpected op '{op.name}' in asdl.module; expected port or view"
            )

        if len(port_names) != len(set(port_names)):
            raise VerifyException("duplicate port name in module")

        order = [item.data for item in self.port_order.data]
        if len(order) != len(port_names) or set(order) != set(port_names):
            raise VerifyException("port_order must be a permutation of declared ports")


@irdl_op_definition
class PortOp(IRDLOperation):
    name = "asdl.port"

    name_ = prop_def(StringAttr, prop_name="name")
    dir = prop_def(StringAttr)
    type_ = prop_def(StringAttr, prop_name="type")
    src = opt_prop_def(LocAttrConstraint)

    def __init__(
        self,
        *,
        name: str | StringAttr,
        dir: str | StringAttr,
        type_: str | StringAttr,
        src: UnknownLoc | FileLineColLoc | None = None,
    ) -> None:
        if isinstance(name, str):
            name = StringAttr(name)
        if isinstance(dir, str):
            dir = StringAttr(dir)
        if isinstance(type_, str):
            type_ = StringAttr(type_)
        properties: dict[str, object | None] = {
            "name": name,
            "dir": dir,
            "type": type_,
            "src": src,
        }
        super().__init__(properties=properties)

    def verify_(self) -> None:
        if self.dir.data not in _ALLOWED_PORT_DIRS:
            raise VerifyException(
                f"port dir must be one of {_ALLOWED_PORT_DIRS}, got '{self.dir.data}'"
            )


@irdl_op_definition
class ViewOp(IRDLOperation):
    name = "asdl.view"

    sym_name = prop_def(SymbolNameConstraint())
    kind = prop_def(StringAttr)
    doc = opt_prop_def(StringAttr)
    src = opt_prop_def(LocAttrConstraint)

    body = region_def("single_block")

    traits = traits_def(NoTerminator(), SymbolOpInterface())

    def __init__(
        self,
        name: str | StringAttr,
        kind: str | StringAttr,
        *,
        region: Region | type[Region.DEFAULT] = Region.DEFAULT,
        doc: str | StringAttr | None = None,
        src: UnknownLoc | FileLineColLoc | None = None,
    ) -> None:
        if isinstance(name, str):
            name = StringAttr(name)
        if isinstance(kind, str):
            kind = StringAttr(kind)
        if not isinstance(region, Region):
            region = Region(Block())
        properties: dict[str, object | None] = {
            "sym_name": name,
            "kind": kind,
            "doc": _maybe_string_attr(doc),
            "src": src,
        }
        super().__init__(properties=properties, regions=[region])

    def verify_(self) -> None:
        if self.kind.data not in _ALLOWED_VIEW_KINDS:
            raise VerifyException(
                f"view kind must be one of {_ALLOWED_VIEW_KINDS}, got '{self.kind.data}'"
            )

        name = self.sym_name.data
        if self.kind.data == "dummy" and name != "dummy":
            raise VerifyException("dummy view kind requires name 'dummy'")
        if name == "dummy" and self.kind.data != "dummy":
            raise VerifyException("view name 'dummy' is reserved for kind 'dummy'")

        nets: list[NetOp] = []
        instances: list[InstanceOp] = []
        templates: list[TemplateOp] = []
        subckt_refs: list[SubcktRefOp] = []
        behav_models: list[BehavModelOp] = []
        dummy_modes: list[DummyModeOp] = []

        for op in self.body.block.ops:
            if isinstance(op, VarOp):
                continue
            elif isinstance(op, NetOp):
                nets.append(op)
            elif isinstance(op, InstanceOp):
                instances.append(op)
            elif isinstance(op, TemplateOp):
                templates.append(op)
            elif isinstance(op, SubcktRefOp):
                subckt_refs.append(op)
            elif isinstance(op, BehavModelOp):
                behav_models.append(op)
            elif isinstance(op, DummyModeOp):
                dummy_modes.append(op)
            else:
                raise VerifyException(
                    f"unexpected op '{op.name}' in asdl.view body"
                )

        if len({net.name_.data for net in nets}) != len(nets):
            raise VerifyException("duplicate net name in view")

        if len({inst.name_.data for inst in instances}) != len(instances):
            raise VerifyException("duplicate instance name in view")

        kind = self.kind.data
        if kind == "subckt":
            if templates or subckt_refs or behav_models or dummy_modes:
                raise VerifyException("subckt view cannot contain templates or subckt_ref")
        elif kind == "primitive":
            if not templates:
                raise VerifyException("primitive view must contain at least one template")
            if instances or nets or subckt_refs or behav_models or dummy_modes:
                raise VerifyException("primitive view cannot contain instances or nets")
        elif kind == "subckt_ref":
            if len(subckt_refs) != 1:
                raise VerifyException("subckt_ref view must contain exactly one subckt_ref")
            if instances or nets or templates or behav_models or dummy_modes:
                raise VerifyException("subckt_ref view cannot contain instances or templates")
        elif kind == "behav":
            if len(behav_models) != 1:
                raise VerifyException("behav view must contain exactly one behav_model")
            if instances or nets or templates or subckt_refs or dummy_modes:
                raise VerifyException("behav view cannot contain instances or templates")
        elif kind == "dummy":
            if len(dummy_modes) > 1:
                raise VerifyException("dummy view can contain at most one dummy_mode")
            if instances or nets or templates or subckt_refs or behav_models:
                raise VerifyException("dummy view cannot contain instances or templates")


@irdl_op_definition
class NetOp(IRDLOperation):
    name = "asdl.net"

    name_ = prop_def(StringAttr, prop_name="name")
    net_type = opt_prop_def(StringAttr)
    implicit = opt_prop_def(BoolAttr)
    src = opt_prop_def(LocAttrConstraint)

    def __init__(
        self,
        *,
        name: str | StringAttr,
        net_type: str | StringAttr | None = None,
        implicit: BoolAttr | IntegerAttr | None = None,
        src: UnknownLoc | FileLineColLoc | None = None,
    ) -> None:
        if isinstance(name, str):
            name = StringAttr(name)
        if isinstance(net_type, str):
            net_type = StringAttr(net_type)
        properties: dict[str, object | None] = {
            "name": name,
            "net_type": net_type,
            "implicit": implicit,
            "src": src,
        }
        super().__init__(properties=properties)


@irdl_op_definition
class InstanceOp(IRDLOperation):
    name = "asdl.instance"

    name_ = prop_def(StringAttr, prop_name="name")
    ref = prop_def(FlatSymbolRefAttrConstr)
    view = opt_prop_def(StringAttr)
    params = opt_prop_def(DictionaryAttr)
    conns = prop_def(ArrayAttr[ConnAttr])
    doc = opt_prop_def(StringAttr)
    src = opt_prop_def(LocAttrConstraint)

    def __init__(
        self,
        *,
        name: str | StringAttr,
        ref: str | SymbolRefAttr,
        conns: Sequence[ConnAttr] | ArrayAttr[ConnAttr],
        view: str | StringAttr | None = None,
        params: DictionaryAttr | None = None,
        doc: str | StringAttr | None = None,
        src: UnknownLoc | FileLineColLoc | None = None,
    ) -> None:
        if isinstance(name, str):
            name = StringAttr(name)
        if isinstance(ref, str):
            ref = SymbolRefAttr(ref)
        if not isinstance(conns, ArrayAttr):
            conns = ArrayAttr(conns)
        if isinstance(view, str):
            view = StringAttr(view)
        properties: dict[str, object | None] = {
            "name": name,
            "ref": ref,
            "view": view,
            "params": params,
            "conns": conns,
            "doc": _maybe_string_attr(doc),
            "src": src,
        }
        super().__init__(properties=properties)

    def verify_(self) -> None:
        ports = [conn.port.data for conn in self.conns.data]
        if len(ports) != len(set(ports)):
            raise VerifyException("duplicate port in instance connections")


@irdl_op_definition
class TemplateOp(IRDLOperation):
    name = "asdl.template"

    backend = prop_def(StringAttr)
    text = prop_def(StringAttr)
    src = opt_prop_def(LocAttrConstraint)

    def __init__(
        self,
        *,
        backend: str | StringAttr,
        text: str | StringAttr,
        src: UnknownLoc | FileLineColLoc | None = None,
    ) -> None:
        if isinstance(backend, str):
            backend = StringAttr(backend)
        if isinstance(text, str):
            text = StringAttr(text)
        properties: dict[str, object | None] = {
            "backend": backend,
            "text": text,
            "src": src,
        }
        super().__init__(properties=properties)


@irdl_op_definition
class VarOp(IRDLOperation):
    name = "asdl.var"

    name_ = prop_def(StringAttr, prop_name="name")
    expr = prop_def(ExprAttr)
    src = opt_prop_def(LocAttrConstraint)

    def __init__(
        self,
        *,
        name: str | StringAttr,
        expr: str | StringAttr | ExprAttr,
        src: UnknownLoc | FileLineColLoc | None = None,
    ) -> None:
        if isinstance(name, str):
            name = StringAttr(name)
        if isinstance(expr, str):
            expr = ExprAttr(expr)
        if isinstance(expr, StringAttr):
            expr = ExprAttr(expr)
        properties: dict[str, object | None] = {
            "name": name,
            "expr": expr,
            "src": src,
        }
        super().__init__(properties=properties)


@irdl_op_definition
class SubcktRefOp(IRDLOperation):
    name = "asdl.subckt_ref"

    cell = prop_def(StringAttr)
    include = opt_prop_def(StringAttr)
    section = opt_prop_def(StringAttr)
    backend = opt_prop_def(StringAttr)
    pin_map = opt_prop_def(DictionaryAttr)
    src = opt_prop_def(LocAttrConstraint)

    def __init__(
        self,
        *,
        cell: str | StringAttr,
        include: str | StringAttr | None = None,
        section: str | StringAttr | None = None,
        backend: str | StringAttr | None = None,
        pin_map: DictionaryAttr | None = None,
        src: UnknownLoc | FileLineColLoc | None = None,
    ) -> None:
        if isinstance(cell, str):
            cell = StringAttr(cell)
        if isinstance(include, str):
            include = StringAttr(include)
        if isinstance(section, str):
            section = StringAttr(section)
        if isinstance(backend, str):
            backend = StringAttr(backend)
        properties: dict[str, object | None] = {
            "cell": cell,
            "include": include,
            "section": section,
            "backend": backend,
            "pin_map": pin_map,
            "src": src,
        }
        super().__init__(properties=properties)

    def verify_(self) -> None:
        if not self.cell.data:
            raise VerifyException("subckt_ref cell must be non-empty")
        if self.pin_map is None:
            return

        module = _enclosing_module(self)
        if module is None:
            raise VerifyException("subckt_ref must be nested within an asdl.module")

        port_names = {port.name_.data for port in _module_ports(module)}
        pin_keys = set(self.pin_map.data.keys())
        if pin_keys != port_names:
            raise VerifyException("pin_map keys must match module ports")


@irdl_op_definition
class BehavModelOp(IRDLOperation):
    name = "asdl.behav_model"

    backend = opt_prop_def(StringAttr)
    model_kind = prop_def(StringAttr)
    ref = prop_def(StringAttr)
    params = opt_prop_def(DictionaryAttr)
    src = opt_prop_def(LocAttrConstraint)

    def __init__(
        self,
        *,
        model_kind: str | StringAttr,
        ref: str | StringAttr,
        backend: str | StringAttr | None = None,
        params: DictionaryAttr | None = None,
        src: UnknownLoc | FileLineColLoc | None = None,
    ) -> None:
        if isinstance(model_kind, str):
            model_kind = StringAttr(model_kind)
        if isinstance(ref, str):
            ref = StringAttr(ref)
        if isinstance(backend, str):
            backend = StringAttr(backend)
        properties: dict[str, object | None] = {
            "backend": backend,
            "model_kind": model_kind,
            "ref": ref,
            "params": params,
            "src": src,
        }
        super().__init__(properties=properties)


@irdl_op_definition
class DummyModeOp(IRDLOperation):
    name = "asdl.dummy_mode"

    mode = prop_def(StringAttr)
    params = opt_prop_def(DictionaryAttr)
    src = opt_prop_def(LocAttrConstraint)

    def __init__(
        self,
        *,
        mode: str | StringAttr,
        params: DictionaryAttr | None = None,
        src: UnknownLoc | FileLineColLoc | None = None,
    ) -> None:
        if isinstance(mode, str):
            mode = StringAttr(mode)
        properties: dict[str, object | None] = {
            "mode": mode,
            "params": params,
            "src": src,
        }
        super().__init__(properties=properties)

    def verify_(self) -> None:
        if self.mode.data != "weak_gnd":
            raise VerifyException("dummy_mode only supports 'weak_gnd' in v0")


ASDL = Dialect(
    "asdl",
    [
        DesignOp,
        ImportOp,
        ModuleOp,
        PortOp,
        ViewOp,
        NetOp,
        InstanceOp,
        TemplateOp,
        VarOp,
        SubcktRefOp,
        BehavModelOp,
        DummyModeOp,
    ],
    [ExprAttr, ConnAttr],
)


def _maybe_string_attr(value: str | StringAttr | None) -> StringAttr | None:
    if value is None:
        return None
    if isinstance(value, StringAttr):
        return value
    return StringAttr(value)


def _enclosing_module(op: Operation) -> ModuleOp | None:
    parent = op.parent_op()
    while parent is not None and not isinstance(parent, ModuleOp):
        parent = parent.parent_op()
    return parent


def _module_ports(module: ModuleOp) -> list[PortOp]:
    return [op for op in module.body.block.ops if isinstance(op, PortOp)]


__all__ = [
    "ExprAttr",
    "ConnAttr",
    "DesignOp",
    "ImportOp",
    "ModuleOp",
    "PortOp",
    "ViewOp",
    "NetOp",
    "InstanceOp",
    "TemplateOp",
    "VarOp",
    "SubcktRefOp",
    "BehavModelOp",
    "DummyModeOp",
    "ASDL",
]
