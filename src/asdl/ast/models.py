"""Pydantic AST models and validators for ASDL documents."""

from __future__ import annotations

from typing import Annotated, Any, Dict, List, Optional, TYPE_CHECKING, Union

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    PrivateAttr,
    StrictStr,
    field_validator,
    model_validator,
)

ParamValue = Union[int, float, bool, str]
InstanceExpr = StrictStr

def _validate_pattern_group(value: object) -> object:
    if not isinstance(value, str):
        raise ValueError("Pattern values must be strings.")
    if value.startswith("<@") and value.endswith(">"):
        raise ValueError("Pattern values must not reference other named patterns.")
    if not _is_group_token(value):
        raise ValueError("Pattern values must be a single group token like <...> or [...].")
    return value


def _is_group_token(value: str) -> bool:
    if value.startswith("<") and value.endswith(">"):
        return _is_valid_group_content(value[1:-1])
    if value.startswith("[") and value.endswith("]"):
        return _is_valid_group_content(value[1:-1])
    return False


def _is_valid_group_content(content: str) -> bool:
    if not content:
        return False
    if any(char.isspace() for char in content):
        return False
    return not any(char in "<>[];" for char in content)


def _reject_string_endpoint_list(value: object) -> object:
    if isinstance(value, str):
        raise ValueError("Endpoint lists must be YAML lists of '<instance>.<pin>' strings")
    return value


EndpointListExpr = Annotated[List[StrictStr], BeforeValidator(_reject_string_endpoint_list)]
ImportsBlock = Dict[StrictStr, StrictStr]
InstancesBlock = Dict[str, InstanceExpr]
NetsBlock = Dict[str, EndpointListExpr]
PatternGroup = Annotated[StrictStr, BeforeValidator(_validate_pattern_group)]
PatternsBlock = Dict[str, PatternGroup]


class AstBaseModel(BaseModel):
    """Base AST model with optional source location metadata."""

    model_config = ConfigDict(extra="forbid")
    _loc: Optional[Any] = PrivateAttr(default=None)

    def set_loc(self, loc: Any) -> "AstBaseModel":
        """Attach a source location to this node.

        Args:
            loc: Location payload (usually a Locatable) from the YAML index.

        Returns:
            This model instance for chaining.
        """
        self._loc = loc
        return self


class DeviceBackendDecl(AstBaseModel):
    """Backend-specific device template and parameters."""

    model_config = ConfigDict(extra="allow")

    template: StrictStr
    params: Optional[Dict[str, ParamValue]] = None


class DeviceDecl(AstBaseModel):
    """Device declaration with ports, params, and backend templates."""

    ports: Optional[List[StrictStr]] = None
    params: Optional[Dict[str, ParamValue]] = None
    backends: Dict[str, DeviceBackendDecl]

    @field_validator("backends")
    @classmethod
    def backends_must_be_non_empty(
        cls, value: Dict[str, DeviceBackendDecl]
    ) -> Dict[str, DeviceBackendDecl]:
        """Reject empty backend maps for device declarations.

        Args:
            value: Mapping of backend names to backend declarations.

        Returns:
            The validated backend mapping.

        Raises:
            ValueError: If the mapping is empty.
        """
        if not value:
            raise ValueError("backends must be a non-empty map")
        return value


class InstanceDefaultsDecl(AstBaseModel):
    """Default instance bindings keyed by instance reference."""

    bindings: Dict[str, StrictStr]
    _bindings_loc: Dict[str, "Locatable"] = PrivateAttr(default_factory=dict)


InstanceDefaultsBlock = Dict[str, InstanceDefaultsDecl]


class ModuleDecl(AstBaseModel):
    """Module declaration with nets, instances, and defaults."""

    instances: Optional[InstancesBlock] = None
    nets: Optional[NetsBlock] = None
    patterns: Optional[PatternsBlock] = None
    instance_defaults: Optional[InstanceDefaultsBlock] = None
    _instances_loc: Dict[str, "Locatable"] = PrivateAttr(default_factory=dict)
    _instance_expr_loc: Dict[str, "Locatable"] = PrivateAttr(default_factory=dict)
    _nets_loc: Dict[str, "Locatable"] = PrivateAttr(default_factory=dict)
    _net_endpoint_locs: Dict[str, List[Optional["Locatable"]]] = PrivateAttr(
        default_factory=dict
    )
    _patterns_loc: Dict[str, "Locatable"] = PrivateAttr(default_factory=dict)
    _pattern_value_loc: Dict[str, "Locatable"] = PrivateAttr(default_factory=dict)


if TYPE_CHECKING:
    from .location import Locatable


class AsdlDocument(AstBaseModel):
    """Top-level ASDL document containing modules and devices."""

    imports: Optional[ImportsBlock] = None
    top: Optional[StrictStr] = None
    modules: Optional[Dict[str, ModuleDecl]] = None
    devices: Optional[Dict[str, DeviceDecl]] = None

    @model_validator(mode="after")
    def validate_document(self) -> "AsdlDocument":
        """Enforce document-level invariants.

        Returns:
            This document if validation succeeds.

        Raises:
            ValueError: If the document has no modules/devices or lacks a top.
        """
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
    "ImportsBlock",
    "InstancesBlock",
    "NetsBlock",
    "PatternsBlock",
    "InstanceDefaultsBlock",
    "InstanceDefaultsDecl",
    "AsdlDocument",
    "ModuleDecl",
    "DeviceDecl",
    "DeviceBackendDecl",
]
