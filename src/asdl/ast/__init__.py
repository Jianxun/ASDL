"""Public AST API and parser entry points."""

from .models import (
    AsdlDocument,
    DeviceBackendDecl,
    DeviceDecl,
    EndpointListExpr,
    ImportsBlock,
    InstanceDefaultsBlock,
    InstanceDefaultsDecl,
    InstanceExpr,
    InstancesBlock,
    ModuleDecl,
    NetsBlock,
    PatternsBlock,
    ParamValue,
)
from .location import Locatable, LocationIndex
from .parser import parse_file, parse_string


def model_json_schema() -> dict:
    """Return the JSON schema for the AST document model."""
    return AsdlDocument.model_json_schema()


__all__ = [
    "Locatable",
    "LocationIndex",
    "ParamValue",
    "InstanceExpr",
    "EndpointListExpr",
    "ImportsBlock",
    "InstanceDefaultsBlock",
    "InstanceDefaultsDecl",
    "InstancesBlock",
    "NetsBlock",
    "PatternsBlock",
    "AsdlDocument",
    "ModuleDecl",
    "DeviceDecl",
    "DeviceBackendDecl",
    "model_json_schema",
    "parse_file",
    "parse_string",
]
