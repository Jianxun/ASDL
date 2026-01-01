from __future__ import annotations

from collections.abc import Mapping

from xdsl.dialects.builtin import (
    ArrayAttr,
    DictionaryAttr,
    FileLineColLoc,
    FloatAttr,
    IntAttr,
    IntegerAttr,
    StringAttr,
    SymbolRefAttr,
    f64,
    i64,
)
from xdsl.ir import Block, Region

from ..ast import (
    AsdlDocument,
    BehavModelDecl,
    BehavViewDecl,
    DummyViewDecl,
    ImportDecl,
    InstanceDecl,
    ModuleDecl,
    NetDecl,
    ParamValue,
    PortDecl,
    PrimitiveViewDecl,
    SubcktRefDecl,
    SubcktRefViewDecl,
    SubcktViewDecl,
    ViewDecl,
)
from ..ast.location import Locatable
from .xdsl_dialect import (
    BehavModelOp,
    ConnAttr,
    DesignOp,
    DummyModeOp,
    ExprAttr,
    ImportOp,
    InstanceOp,
    ModuleOp,
    NetOp,
    PortOp,
    SubcktRefOp,
    TemplateOp,
    VarOp,
    ViewOp,
)


def convert_document(document: AsdlDocument) -> DesignOp:
    region = Region(Block())
    design = DesignOp(
        region=region,
        doc=document.doc,
        top=document.top,
        top_mode=document.top_mode,
        src=_loc_attr(document._loc),
    )
    block = design.body.block

    for as_name, import_decl in (document.imports or {}).items():
        block.add_op(_convert_import(as_name, import_decl))

    for name, module_decl in document.modules.items():
        block.add_op(_convert_module(name, module_decl))

    return design


def _convert_import(as_name: str, decl: ImportDecl) -> ImportOp:
    items = decl.items
    items_attr = None
    if items is not None:
        items_attr = ArrayAttr(StringAttr(item) for item in items)
    return ImportOp(
        as_name=as_name,
        from_=decl.from_,
        items=items_attr,
        src=_loc_attr(decl._loc),
    )


def _convert_module(name: str, decl: ModuleDecl) -> ModuleOp:
    region = Region(Block())
    module_op = ModuleOp(
        name,
        decl.port_order,
        region=region,
        doc=decl.doc,
        src=_loc_attr(decl._loc),
    )
    block = module_op.body.block

    for port_name, port in decl.ports.items():
        block.add_op(_convert_port(port_name, port))

    seen_view_names: set[str] = set()
    for view_name, view_decl in decl.views.items():
        normalized = _normalize_view_name(view_name)
        if normalized in seen_view_names:
            raise ValueError(f"duplicate view name after normalization: '{normalized}'")
        seen_view_names.add(normalized)
        block.add_op(_convert_view(normalized, view_decl))

    return module_op


def _convert_port(name: str, decl: PortDecl) -> PortOp:
    return PortOp(
        name=name,
        dir=decl.dir,
        type_=decl.type or "signal",
        src=_loc_attr(decl._loc),
    )


def _convert_view(name: str, view: ViewDecl) -> ViewOp:
    region = Region(Block())
    view_op = ViewOp(
        name,
        view.kind,
        region=region,
        doc=view.doc,
        src=_loc_attr(view._loc),
    )
    block = view_op.body.block

    for var_name, expr in (view.variables or {}).items():
        block.add_op(
            VarOp(
                name=var_name,
                expr=ExprAttr(expr),
                src=_loc_attr(view._loc),
            )
        )

    if isinstance(view, SubcktViewDecl):
        for net_name, net in (view.nets or {}).items():
            block.add_op(_convert_net(net_name, net))
        for inst_name, inst in (view.instances or {}).items():
            block.add_op(_convert_instance(inst_name, inst))
    elif isinstance(view, PrimitiveViewDecl):
        for backend, text in view.templates.items():
            block.add_op(
                TemplateOp(
                    backend=backend,
                    text=text,
                    src=_loc_attr(view._loc),
                )
            )
    elif isinstance(view, SubcktRefViewDecl):
        block.add_op(_convert_subckt_ref(view.ref, view.pin_map))
    elif isinstance(view, DummyViewDecl):
        dummy_mode = view.mode
        params_attr = _convert_params(view.params)
        if dummy_mode is None and params_attr is not None:
            dummy_mode = "weak_gnd"
        if dummy_mode is not None:
            block.add_op(
                DummyModeOp(
                    mode=dummy_mode,
                    params=params_attr,
                    src=_loc_attr(view._loc),
                )
            )
    elif isinstance(view, BehavViewDecl):
        block.add_op(_convert_behav_model(view.model))

    return view_op


def _convert_net(name: str, decl: NetDecl) -> NetOp:
    return NetOp(
        name=name,
        net_type=decl.type,
        src=_loc_attr(decl._loc),
    )


def _convert_instance(name: str, decl: InstanceDecl) -> InstanceOp:
    conns = ArrayAttr(ConnAttr(port, net) for port, net in decl.conns.items())
    params_attr = _convert_params(decl.params)
    view_override = None
    if decl.view is not None:
        view_override = _normalize_view_name(decl.view)
    return InstanceOp(
        name=name,
        ref=SymbolRefAttr(decl.model),
        conns=conns,
        view=view_override,
        params=params_attr,
        doc=decl.doc,
        src=_loc_attr(decl._loc),
    )


def _convert_subckt_ref(
    decl: SubcktRefDecl, pin_map: Mapping[str, str] | None
) -> SubcktRefOp:
    pin_map_attr = None
    if pin_map is not None:
        pin_map_attr = DictionaryAttr(
            {key: StringAttr(value) for key, value in pin_map.items()}
        )
    return SubcktRefOp(
        cell=decl.cell,
        include=decl.include,
        section=decl.section,
        backend=decl.backend,
        pin_map=pin_map_attr,
        src=_loc_attr(decl._loc),
    )


def _convert_behav_model(decl: BehavModelDecl) -> BehavModelOp:
    return BehavModelOp(
        backend=decl.backend,
        model_kind=decl.model_kind,
        ref=decl.ref,
        params=_convert_params(decl.params),
        src=_loc_attr(decl._loc),
    )


def _convert_params(params: Mapping[str, ParamValue] | None) -> DictionaryAttr | None:
    if params is None:
        return None
    return DictionaryAttr({key: _param_value_attr(value) for key, value in params.items()})


def _param_value_attr(value: ParamValue):
    if isinstance(value, bool):
        return IntegerAttr.from_bool(value)
    if isinstance(value, int):
        return IntegerAttr(value, i64)
    if isinstance(value, float):
        return FloatAttr(value, f64)
    return ExprAttr(value)


def _normalize_view_name(name: str) -> str:
    return "nominal" if name == "nom" else name


def _loc_attr(loc: Locatable | None) -> FileLineColLoc | None:
    if loc is None or loc.start_line is None or loc.start_col is None:
        return None
    return FileLineColLoc(
        StringAttr(loc.file),
        IntAttr(loc.start_line),
        IntAttr(loc.start_col),
    )


__all__ = ["convert_document"]
