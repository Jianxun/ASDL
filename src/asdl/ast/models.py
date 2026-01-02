from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, PrivateAttr, StrictStr, field_validator, model_validator

ParamValue = Union[int, float, bool, str]
InstanceExpr = StrictStr
EndpointListExpr = StrictStr
InstancesBlock = Dict[str, InstanceExpr]
NetsBlock = Dict[str, EndpointListExpr]


class AstBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    _loc: Optional[Any] = PrivateAttr(default=None)

    def set_loc(self, loc: Any) -> "AstBaseModel":
        self._loc = loc
        return self


class DeviceBackendDecl(AstBaseModel):
    model_config = ConfigDict(extra="allow")

    template: StrictStr
    params: Optional[Dict[str, ParamValue]] = None


class DeviceDecl(AstBaseModel):
    ports: List[StrictStr]
    params: Optional[Dict[str, ParamValue]] = None
    backends: Dict[str, DeviceBackendDecl]

    @field_validator("backends")
    @classmethod
    def backends_must_be_non_empty(
        cls, value: Dict[str, DeviceBackendDecl]
    ) -> Dict[str, DeviceBackendDecl]:
        if not value:
            raise ValueError("backends must be a non-empty map")
        return value


class ModuleDecl(AstBaseModel):
    instances: Optional[InstancesBlock] = None
    nets: Optional[NetsBlock] = None


class AsdlDocument(AstBaseModel):
    top: Optional[StrictStr] = None
    modules: Optional[Dict[str, ModuleDecl]] = None
    devices: Optional[Dict[str, DeviceDecl]] = None

    @model_validator(mode="after")
    def validate_document(self) -> "AsdlDocument":
        has_modules = bool(self.modules)
        has_devices = bool(self.devices)
        if not has_modules and not has_devices:
            raise ValueError("At least one of modules or devices must be present")
        if self.modules is not None and len(self.modules) > 1 and not self.top:
            raise ValueError("top is required when more than one module is defined")
        return self


__all__ = [
    "ParamValue",
    "InstanceExpr",
    "EndpointListExpr",
    "InstancesBlock",
    "NetsBlock",
    "AsdlDocument",
    "ModuleDecl",
    "DeviceDecl",
    "DeviceBackendDecl",
]
