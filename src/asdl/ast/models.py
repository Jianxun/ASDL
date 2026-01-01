from __future__ import annotations

from typing import Annotated, Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator, model_validator

ParamValue = Union[int, float, bool, str]

Name = Annotated[str, Field(pattern=r"^[^*<>\[\]]+$")]
NetName = Annotated[str, Field(pattern=r"^\$?[^*<>\[\]]+$")]
Ports = Annotated[List[Name], Field(min_length=1)]
Endpoints = Annotated[List["EndpointDecl"], Field(min_length=1)]


class AstBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    _loc: Optional[Any] = PrivateAttr(default=None)

    def set_loc(self, loc: Any) -> "AstBaseModel":
        self._loc = loc
        return self


class EndpointDecl(AstBaseModel):
    inst: Name
    pin: Name


class InstanceDecl(AstBaseModel):
    ref: Name
    params: Optional[Dict[str, ParamValue]] = None


class ModuleDecl(AstBaseModel):
    instances: Optional[Dict[Name, InstanceDecl]] = None
    nets: Optional[Dict[NetName, Endpoints]] = None


class DeviceBackendDecl(AstBaseModel):
    model_config = ConfigDict(extra="allow")

    template: str
    params: Optional[Dict[str, ParamValue]] = None


class DeviceDecl(AstBaseModel):
    ports: Ports
    params: Optional[Dict[str, ParamValue]] = None
    backends: Dict[Name, DeviceBackendDecl]

    @field_validator("backends")
    @classmethod
    def backends_must_be_non_empty(
        cls, value: Dict[str, DeviceBackendDecl]
    ) -> Dict[str, DeviceBackendDecl]:
        if not value:
            raise ValueError("backends must be a non-empty map")
        return value


class AsdlDocument(AstBaseModel):
    top: Optional[Name] = None
    modules: Optional[Dict[Name, ModuleDecl]] = None
    devices: Optional[Dict[Name, DeviceDecl]] = None

    @model_validator(mode="after")
    def validate_document(self) -> "AsdlDocument":
        if not self.modules and not self.devices:
            raise ValueError("ASDL document must define at least one module or device")
        if self.modules and len(self.modules) > 1 and not self.top:
            raise ValueError("top is required when multiple modules are defined")
        return self


__all__ = [
    "ParamValue",
    "AsdlDocument",
    "ModuleDecl",
    "DeviceDecl",
    "DeviceBackendDecl",
    "InstanceDecl",
    "EndpointDecl",
]
