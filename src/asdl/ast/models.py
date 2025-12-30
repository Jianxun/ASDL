from __future__ import annotations

from typing import Annotated, Any, Dict, List, Optional, Union, Literal

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator, model_validator

ParamValue = Union[int, float, bool, str]


class AstBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    _loc: Optional[Any] = PrivateAttr(default=None)

    def set_loc(self, loc: Any) -> "AstBaseModel":
        self._loc = loc
        return self


class ImportDecl(AstBaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    from_: str = Field(alias="from")
    items: Optional[List[str]] = None


class PortDecl(AstBaseModel):
    dir: Literal["in", "out", "in_out"]
    type: Optional[str] = "signal"
    metadata: Optional[Dict[str, Any]] = None


class NetDecl(AstBaseModel):
    type: Optional[str] = None
    doc: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class InstanceDecl(AstBaseModel):
    model: str
    view: Optional[str] = None
    conns: Dict[str, str]
    params: Optional[Dict[str, ParamValue]] = None
    doc: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SubcktRefDecl(AstBaseModel):
    cell: str
    include: Optional[str] = None
    section: Optional[str] = None
    backend: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BehavModelDecl(AstBaseModel):
    model_kind: str
    ref: str
    backend: Optional[str] = None
    params: Optional[Dict[str, ParamValue]] = None
    metadata: Optional[Dict[str, Any]] = None


class ViewDeclBase(AstBaseModel):
    doc: Optional[str] = None
    variables: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None


class SubcktViewDecl(ViewDeclBase):
    kind: Literal["subckt"]
    instances: Optional[Dict[str, InstanceDecl]] = None
    nets: Optional[Dict[str, NetDecl]] = None


class SubcktRefViewDecl(ViewDeclBase):
    kind: Literal["subckt_ref"]
    ref: SubcktRefDecl
    pin_map: Optional[Dict[str, str]] = None


class PrimitiveViewDecl(ViewDeclBase):
    kind: Literal["primitive"]
    templates: Dict[str, str]

    @field_validator("templates")
    @classmethod
    def templates_must_be_non_empty(cls, value: Dict[str, str]) -> Dict[str, str]:
        if not value:
            raise ValueError("templates must be a non-empty map")
        return value


class DummyViewDecl(ViewDeclBase):
    kind: Literal["dummy"]
    mode: Optional[Literal["weak_gnd"]] = None
    params: Optional[Dict[str, ParamValue]] = None


class BehavViewDecl(ViewDeclBase):
    kind: Literal["behav"]
    model: BehavModelDecl


ViewDecl = Annotated[
    Union[SubcktViewDecl, SubcktRefViewDecl, PrimitiveViewDecl, DummyViewDecl, BehavViewDecl],
    Field(discriminator="kind"),
]


class ModuleDecl(AstBaseModel):
    doc: Optional[str] = None
    ports: Dict[str, PortDecl]
    port_order: List[str]
    views: Dict[str, ViewDecl]
    metadata: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def validate_dummy_coupling(self) -> "ModuleDecl":
        for name, view in self.views.items():
            if view.kind == "dummy" and name != "dummy":
                raise ValueError("dummy view kind requires view name 'dummy'")
            if name == "dummy" and view.kind != "dummy":
                raise ValueError("view name 'dummy' is reserved for kind 'dummy'")
        return self


class AsdlDocument(AstBaseModel):
    doc: Optional[str] = None
    top: Optional[str] = None
    top_mode: Optional[Literal["subckt", "flat"]] = None
    imports: Optional[Dict[str, ImportDecl]] = None
    aliases: Optional[Dict[str, str]] = None
    modules: Dict[str, ModuleDecl]


__all__ = [
    "ParamValue",
    "AsdlDocument",
    "ImportDecl",
    "ModuleDecl",
    "PortDecl",
    "ViewDecl",
    "SubcktViewDecl",
    "SubcktRefViewDecl",
    "PrimitiveViewDecl",
    "DummyViewDecl",
    "BehavViewDecl",
    "InstanceDecl",
    "NetDecl",
    "SubcktRefDecl",
    "BehavModelDecl",
]
