"""Pydantic AST models and validators for ASDL documents."""

from __future__ import annotations

from typing import Annotated, Any, Dict, List, Optional, TYPE_CHECKING, Union

import re

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

_TAG_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_pattern_group(value: object) -> object:
    if not isinstance(value, str):
        raise ValueError("Pattern values must be strings.")
    if value.startswith("<@") and value.endswith(">"):
        raise ValueError("Pattern values must not reference other named patterns.")
    if not _is_group_token(value):
        raise ValueError("Pattern values must be a single group token like <...>.")
    return value


def _is_group_token(value: str) -> bool:
    if value.startswith("<") and value.endswith(">"):
        return _is_valid_group_content(value[1:-1])
    return False


def _is_valid_group_content(content: str) -> bool:
    if not content:
        return False
    if any(char.isspace() for char in content):
        return False
    return not any(char in "<>[];" for char in content)


def _validate_pattern_tag(value: object) -> object:
    """Validate literal tag names for named pattern axes.

    Args:
        value: Raw tag value.

    Returns:
        The validated tag value.

    Raises:
        ValueError: If the tag is not a literal identifier string.
    """
    if not isinstance(value, str):
        raise ValueError("Pattern tags must be strings.")
    if not _TAG_NAME_RE.fullmatch(value):
        raise ValueError("Pattern tags must be literal identifiers.")
    return value


def _reject_string_endpoint_list(value: object) -> object:
    if isinstance(value, str):
        raise ValueError("Endpoint lists must be YAML lists of '<instance>.<pin>' strings")
    return value


def _validate_module_symbol(value: object) -> object:
    """Validate `cell` / `cell@view` symbol grammar."""
    if not isinstance(value, str):
        raise ValueError("Module symbols must be strings.")
    if not value:
        raise ValueError("Invalid module symbol: cell token is required.")

    at_count = value.count("@")
    if at_count > 1:
        raise ValueError(
            "Invalid module symbol: '@' separator may appear at most once in 'cell@view'."
        )

    if at_count == 0:
        if not _TAG_NAME_RE.fullmatch(value):
            raise ValueError("Invalid module symbol: cell token must be a valid identifier.")
        return value

    cell, view = value.split("@", 1)
    if not cell:
        raise ValueError("Invalid module symbol: cell token before '@' is required.")
    if not _TAG_NAME_RE.fullmatch(cell):
        raise ValueError("Invalid module symbol: cell token must be a valid identifier.")
    if not view:
        raise ValueError("Invalid module symbol: view token after '@' is required.")
    if not _TAG_NAME_RE.fullmatch(view):
        raise ValueError("Invalid module symbol: view token must be a valid identifier.")
    return value


EndpointListExpr = Annotated[List[StrictStr], BeforeValidator(_reject_string_endpoint_list)]
ImportsBlock = Dict[StrictStr, StrictStr]
NetsBlock = Dict[str, EndpointListExpr]
PatternGroup = Annotated[StrictStr, BeforeValidator(_validate_pattern_group)]
PatternTag = Annotated[StrictStr, BeforeValidator(_validate_pattern_tag)]
ModuleSymbol = Annotated[StrictStr, BeforeValidator(_validate_module_symbol)]


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


class PatternDecl(AstBaseModel):
    """Named pattern declaration with optional axis tag."""

    expr: PatternGroup
    tag: Optional[PatternTag] = None


PatternsBlock = Dict[str, Union[PatternGroup, PatternDecl]]


class DeviceBackendDecl(AstBaseModel):
    """Backend-specific device template, parameters, and variables."""

    model_config = ConfigDict(extra="allow")

    template: StrictStr
    parameters: Optional[Dict[str, ParamValue]] = None
    variables: Optional[Dict[str, ParamValue]] = None

    @model_validator(mode="before")
    @classmethod
    def reject_params_alias(cls, data: object) -> object:
        """Reject legacy params field for backend declarations."""
        if isinstance(data, dict) and "params" in data:
            raise ValueError("Use 'parameters' instead of 'params' for backends.")
        return data


class DeviceDecl(AstBaseModel):
    """Device declaration with ports, parameters, variables, and backends."""

    ports: Optional[List[StrictStr]] = None
    parameters: Optional[Dict[str, ParamValue]] = None
    variables: Optional[Dict[str, ParamValue]] = None
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


class InstanceDecl(AstBaseModel):
    """Structured instance declaration with canonical parameters map."""

    ref: ModuleSymbol
    parameters: Optional[Dict[str, ParamValue]] = None

    @model_validator(mode="before")
    @classmethod
    def reject_params_alias(cls, data: object) -> object:
        """Reject legacy params field for structured instance declarations."""
        if isinstance(data, dict) and "params" in data:
            raise ValueError("Use 'parameters' instead of 'params' for instances.")
        return data


InstanceExpr = StrictStr
InstanceValue = Union[InstanceDecl, InstanceExpr]
InstancesBlock = Dict[str, InstanceValue]


class ModuleDecl(AstBaseModel):
    """Module declaration with nets, instances, and defaults."""

    instances: Optional[InstancesBlock] = None
    nets: Optional[NetsBlock] = None
    patterns: Optional[PatternsBlock] = None
    variables: Optional[Dict[str, ParamValue]] = None
    instance_defaults: Optional[InstanceDefaultsBlock] = None
    _instances_loc: Dict[str, "Locatable"] = PrivateAttr(default_factory=dict)
    _instance_expr_loc: Dict[str, "Locatable"] = PrivateAttr(default_factory=dict)
    _instance_ref_loc: Dict[str, "Locatable"] = PrivateAttr(default_factory=dict)
    _instance_parameters_loc: Dict[str, "Locatable"] = PrivateAttr(default_factory=dict)
    _instance_parameter_value_locs: Dict[str, Dict[str, "Locatable"]] = PrivateAttr(
        default_factory=dict
    )
    _nets_loc: Dict[str, "Locatable"] = PrivateAttr(default_factory=dict)
    _net_endpoint_locs: Dict[str, List[Optional["Locatable"]]] = PrivateAttr(
        default_factory=dict
    )
    _patterns_loc: Dict[str, "Locatable"] = PrivateAttr(default_factory=dict)
    _pattern_value_loc: Dict[str, "Locatable"] = PrivateAttr(default_factory=dict)
    _pattern_tag_loc: Dict[str, "Locatable"] = PrivateAttr(default_factory=dict)

    @field_validator("instances")
    @classmethod
    def validate_inline_instance_refs(
        cls, value: Optional[InstancesBlock]
    ) -> Optional[InstancesBlock]:
        """Validate inline instance expression references against module symbol grammar."""
        if value is None:
            return value
        for instance in value.values():
            if isinstance(instance, str):
                ref = instance.split(maxsplit=1)[0]
                if not ref:
                    raise ValueError(
                        "Instance expressions must start with an instance reference token."
                    )
                _validate_module_symbol(ref)
        return value

    def pattern_axis_id(self, name: str) -> Optional[str]:
        """Resolve the axis identifier for a named pattern.

        Args:
            name: Named pattern identifier.

        Returns:
            The axis identifier (tag or pattern name), or None if unknown.
        """
        if not self.patterns:
            return None
        pattern = self.patterns.get(name)
        if pattern is None:
            return None
        if isinstance(pattern, PatternDecl) and pattern.tag:
            return pattern.tag
        return name

    def pattern_axis_id_loc(self, name: str) -> Optional["Locatable"]:
        """Return the location span for a named pattern axis identifier.

        Args:
            name: Named pattern identifier.

        Returns:
            The location for the axis tag if present, otherwise the pattern name location.
        """
        if not self.patterns or name not in self.patterns:
            return None
        pattern = self.patterns.get(name)
        if isinstance(pattern, PatternDecl) and pattern.tag:
            return self._pattern_tag_loc.get(name) or self._patterns_loc.get(name)
        return self._patterns_loc.get(name)

    def pattern_expr_loc(self, name: str) -> Optional["Locatable"]:
        """Return the location span for a named pattern expression.

        Args:
            name: Named pattern identifier.

        Returns:
            The expression location, if available.
        """
        if not self.patterns or name not in self.patterns:
            return None
        return self._pattern_value_loc.get(name)


if TYPE_CHECKING:
    from .location import Locatable


class AsdlDocument(AstBaseModel):
    """Top-level ASDL document containing modules and devices."""

    imports: Optional[ImportsBlock] = None
    top: Optional[StrictStr] = None
    modules: Optional[Dict[ModuleSymbol, ModuleDecl]] = None
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
    "ModuleSymbol",
    "InstanceExpr",
    "InstanceDecl",
    "InstanceValue",
    "EndpointListExpr",
    "ImportsBlock",
    "InstancesBlock",
    "NetsBlock",
    "PatternsBlock",
    "PatternDecl",
    "InstanceDefaultsBlock",
    "InstanceDefaultsDecl",
    "AsdlDocument",
    "ModuleDecl",
    "DeviceDecl",
    "DeviceBackendDecl",
]
