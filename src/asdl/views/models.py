"""Validation models for profile-based ASDL view binding configuration."""

from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, RootModel, field_validator, model_validator

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_BIND_SYMBOL = re.compile(
    r"^(?P<cell>[A-Za-z_][A-Za-z0-9_]*)(?:@(?P<view>[A-Za-z_][A-Za-z0-9_]*))?$"
)


class ViewMatch(BaseModel):
    """Typed match predicates for selecting instance occurrences.

    Fields implement v0 semantics from `spec_asdl_view_config.md`.
    """

    model_config = ConfigDict(extra="forbid")

    path: Optional[str] = None
    instance: Optional[str] = None
    module: Optional[str] = None

    @field_validator("path")
    @classmethod
    def _validate_path(cls, value: Optional[str]) -> Optional[str]:
        """Validate hierarchical match path syntax.

        Args:
            value: Optional dotted hierarchy path.

        Returns:
            The validated path.

        Raises:
            ValueError: If the path is empty or contains empty segments.
        """
        if value is None:
            return None
        if value.strip() == "":
            raise ValueError("path must not be empty")
        segments = value.split(".")
        if any(segment == "" for segment in segments):
            raise ValueError("path must not contain empty hierarchy segments")
        return value

    @field_validator("instance")
    @classmethod
    def _validate_instance(cls, value: Optional[str]) -> Optional[str]:
        """Validate match instance leaf predicate.

        Args:
            value: Optional instance leaf name.

        Returns:
            The validated instance name.

        Raises:
            ValueError: If the instance is empty or includes path separators.
        """
        if value is None:
            return None
        if value.strip() == "":
            raise ValueError("instance must not be empty")
        if "." in value:
            raise ValueError("instance must be a leaf name and must not include '.'")
        return value

    @field_validator("module")
    @classmethod
    def _validate_module(cls, value: Optional[str]) -> Optional[str]:
        """Validate module predicate syntax.

        Args:
            value: Optional logical module symbol predicate.

        Returns:
            The validated module predicate.

        Raises:
            ValueError: If the module is decorated or malformed.
        """
        if value is None:
            return None
        if not _IDENTIFIER.fullmatch(value):
            raise ValueError(
                "module must be an undecorated logical cell name matching "
                "[A-Za-z_][A-Za-z0-9_]*"
            )
        return value

    @model_validator(mode="after")
    def _validate_match_fields(self) -> "ViewMatch":
        """Apply cross-field match constraints.

        Returns:
            The validated match object.

        Raises:
            ValueError: If required predicates are missing or mutually exclusive.
        """
        has_any_predicate = any(
            predicate is not None for predicate in (self.path, self.instance, self.module)
        )
        if not has_any_predicate:
            raise ValueError(
                "match must include at least one of 'path', 'instance', or 'module'"
            )
        if self.instance is not None and self.module is not None:
            raise ValueError("'instance' and 'module' are mutually exclusive")
        return self


class ViewRule(BaseModel):
    """Rule-level configuration for explicit view binding overrides."""

    model_config = ConfigDict(extra="forbid")

    id: Optional[str] = None
    match: ViewMatch
    bind: str

    @field_validator("id")
    @classmethod
    def _validate_id(cls, value: Optional[str]) -> Optional[str]:
        """Validate optional rule identifier.

        Args:
            value: Optional explicit rule identifier.

        Returns:
            The validated identifier.

        Raises:
            ValueError: If identifier is empty.
        """
        if value is None:
            return None
        if value.strip() == "":
            raise ValueError("id must not be empty")
        return value

    @field_validator("bind")
    @classmethod
    def _validate_bind(cls, value: str) -> str:
        """Validate rule bind symbol grammar.

        Args:
            value: Bound module symbol in `cell` or `cell@view` form.

        Returns:
            The validated bind symbol.

        Raises:
            ValueError: If bind does not match v0 symbol grammar.
        """
        if _BIND_SYMBOL.fullmatch(value) is None:
            raise ValueError(
                "bind must be a module symbol in 'cell' or 'cell@view' form"
            )
        return value


class ViewProfile(BaseModel):
    """A profile describing baseline view precedence and ordered override rules."""

    model_config = ConfigDict(extra="forbid")

    description: Optional[str] = None
    view_order: list[str]
    rules: list[ViewRule] = Field(default_factory=list)

    @field_validator("view_order")
    @classmethod
    def _validate_view_order(cls, value: list[str]) -> list[str]:
        """Validate baseline view precedence tokens.

        Args:
            value: Ordered precedence list containing `default` and/or view names.

        Returns:
            The validated precedence list.

        Raises:
            ValueError: If empty or containing malformed/decorated tokens.
        """
        if not value:
            raise ValueError("view_order must be a non-empty list")
        for token in value:
            if token == "default":
                continue
            if not _IDENTIFIER.fullmatch(token):
                raise ValueError(
                    "view_order tokens must be 'default' or identifiers matching "
                    "[A-Za-z_][A-Za-z0-9_]*"
                )
        return value

    @model_validator(mode="after")
    def _assign_default_rule_ids(self) -> "ViewProfile":
        """Assign deterministic default IDs to rules without explicit IDs.

        Returns:
            Profile with missing rule IDs normalized to `rule<k>`.
        """
        normalized_rules: list[ViewRule] = []
        for index, rule in enumerate(self.rules, start=1):
            if rule.id is None:
                normalized_rules.append(rule.model_copy(update={"id": f"rule{index}"}))
            else:
                normalized_rules.append(rule)
        self.rules = normalized_rules
        return self


class ViewConfig(RootModel[dict[str, ViewProfile]]):
    """Top-level mapping of profile names to profile definitions."""

    @field_validator("root")
    @classmethod
    def _validate_profiles(cls, value: dict[str, ViewProfile]) -> dict[str, ViewProfile]:
        """Validate top-level profile map.

        Args:
            value: Profile mapping keyed by profile name.

        Returns:
            The validated mapping.

        Raises:
            ValueError: If mapping is empty or has malformed profile names.
        """
        if not value:
            raise ValueError("view config must define at least one profile")
        for profile_name in value:
            if not isinstance(profile_name, str) or profile_name.strip() == "":
                raise ValueError("profile names must be non-empty strings")
        return value

    @property
    def profiles(self) -> dict[str, ViewProfile]:
        """Return the profile mapping.

        Returns:
            Mapping of profile name to validated profile model.
        """
        return self.root


__all__ = ["ViewConfig", "ViewMatch", "ViewProfile", "ViewRule"]
