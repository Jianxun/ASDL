"""
Deprecated: Pydantic-based schema models

This module will be removed once the dataclass-introspection-based schema
generator is in place. Do not extend this file; use data_structures.py as the
single source of truth for schema generation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

try:  # Pydantic v2 preferred
    from pydantic import BaseModel, Field
except Exception:  # pragma: no cover - fallback for older environments
    from pydantic import BaseModel  # type: ignore
    Field = lambda default=None, **kwargs: default  # type: ignore

from .data_structures import PrimitiveType, PortDirection, SignalType


class FileInfoModel(BaseModel):
    """Top-level file metadata block."""

    top_module: Optional[str] = Field(
        default=None, description="Name of the top module in this ASDL file"
    )
    doc: Optional[str] = Field(default=None, description="Human-readable description")
    revision: Optional[str] = Field(default=None, description="Revision identifier")
    author: Optional[str] = Field(default=None, description="Author name or email")
    date: Optional[str] = Field(default=None, description="Document or design date")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Arbitrary metadata for tools and annotations"
    )


class DeviceModelModel(BaseModel):
    """PDK or SPICE primitive template."""

    type: PrimitiveType = Field(description="Origin of the primitive model")
    ports: List[str] = Field(description="Ordered list of port names for this device")
    device_line: str = Field(
        description="SPICE device line template or model identifier"
    )
    doc: Optional[str] = Field(default=None, description="Documentation for the model")
    parameters: Optional[Dict[str, str]] = Field(
        default=None, description="Default parameter values or expressions"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Arbitrary metadata for tools and annotations"
    )


class PortConstraintsModel(BaseModel):
    """Placeholder structure for future formal constraints.

    For now, preserve raw content to avoid limiting schema evolution.
    """

    constraints: Any


class PortModel(BaseModel):
    """Port definition with direction and type."""

    dir: PortDirection
    type: SignalType
    constraints: Optional[PortConstraintsModel] = None
    metadata: Optional[Dict[str, Any]] = None


class InstanceModel(BaseModel):
    """Instance of a device model or a module."""

    model: str = Field(description="Target device model or module name")
    mappings: Dict[str, str] = Field(
        description="Port-to-net mapping for this instance"
    )
    doc: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class ModuleModel(BaseModel):
    """Hierarchical module definition."""

    doc: Optional[str] = None
    ports: Optional[Dict[str, PortModel]] = None
    internal_nets: Optional[List[str]] = None
    parameters: Optional[Dict[str, Any]] = None
    instances: Optional[Dict[str, InstanceModel]] = None
    metadata: Optional[Dict[str, Any]] = None


class ASDLFileModel(BaseModel):
    """Root ASDL YAML document structure."""

    file_info: FileInfoModel
    models: Dict[str, DeviceModelModel]
    modules: Dict[str, ModuleModel]


def build_json_schema() -> Dict[str, Any]:
    """Return the JSON Schema for the ASDL YAML document.

    Supports Pydantic v1 and v2 via a best-effort compatibility shim.
    """

    # Pydantic v2
    if hasattr(ASDLFileModel, "model_json_schema"):
        return ASDLFileModel.model_json_schema()  # type: ignore[attr-defined]

    # Pydantic v1 fallback
    return ASDLFileModel.schema()  # type: ignore[attr-defined]


def render_text_schema() -> str:
    """Render a human-readable schema overview similar to ams-compose schema.txt."""

    lines: List[str] = []
    lines.append("=" * 40)
    lines.append("ASDL YAML Configuration Schema")
    lines.append("=" * 40)
    lines.append("")

    lines.append("STRUCTURE:")
    lines.append("")
    lines.append("file_info:                           # Required: file metadata")
    lines.append("models:                               # Required: device model templates")
    lines.append("  <model_alias>:                      # Key is a unique alias")
    lines.append("    type: pdk_device|spice_device     # Required")
    lines.append("    ports: [names]                     # Required: ordered port names")
    lines.append("    device_line: <string>             # Required: SPICE device template or id")
    lines.append("    doc: <string>                     # Optional")
    lines.append("    parameters: {k: v}                # Optional")
    lines.append("    metadata: {..}                    # Optional")
    lines.append("modules:                              # Required: hierarchical modules")
    lines.append("  <module_name>:")
    lines.append("    doc: <string>                     # Optional")
    lines.append("    ports:                            # Optional: named port objects")
    lines.append("      <port_name>:")
    lines.append("        dir: in|out|in_out            # Required")
    lines.append("        type: voltage|current|digital # Required")
    lines.append("        constraints: {..}             # Optional")
    lines.append("        metadata: {..}                # Optional")
    lines.append("    internal_nets: [names]            # Optional")
    lines.append("    parameters: {k: v}                # Optional")
    lines.append("    instances:                        # Optional: instance map")
    lines.append("      <instance_id>:")
    lines.append("        model: <name>                 # Required: device model or module")
    lines.append("        mappings: {port: net}         # Required")
    lines.append("        doc: <string>                 # Optional")
    lines.append("        parameters: {..}              # Optional")
    lines.append("        metadata: {..}                # Optional")
    lines.append("")

    lines.append("FIELD DETAILS:")
    lines.append("")
    lines.append("Root Fields:")
    lines.append("  file_info        Required: file metadata block")
    lines.append("  models           Required: map of device model templates")
    lines.append("  modules          Required: map of module definitions")
    lines.append("")

    lines.append("file_info Fields:")
    lines.append("  top_module       Optional: default top module name")
    lines.append("  doc              Optional: document description")
    lines.append("  revision         Optional: revision identifier")
    lines.append("  author           Optional: author information")
    lines.append("  date             Optional: date string")
    lines.append("  metadata         Optional: arbitrary metadata")
    lines.append("")

    lines.append("Device Model Fields:")
    lines.append("  type             Required: pdk_device | spice_device")
    lines.append("  ports            Required: ordered port names")
    lines.append("  device_line      Required: SPICE device template or id")
    lines.append("  doc              Optional")
    lines.append("  parameters       Optional: default parameter map")
    lines.append("  metadata         Optional")
    lines.append("")

    lines.append("Module Fields:")
    lines.append("  doc              Optional")
    lines.append("  ports            Optional: map of port objects")
    lines.append("  internal_nets    Optional: list of net names")
    lines.append("  parameters       Optional: parameter map")
    lines.append("  instances        Optional: map of instances")
    lines.append("  metadata         Optional")
    lines.append("")

    lines.append("Port Fields:")
    lines.append("  dir              Required: in | out | in_out")
    lines.append("  type             Required: voltage | current | digital")
    lines.append("  constraints      Optional: placeholder object for future constraints")
    lines.append("  metadata         Optional")
    lines.append("")

    lines.append("Instance Fields:")
    lines.append("  model            Required: device model or module name")
    lines.append("  mappings         Required: {port: net}")
    lines.append("  doc              Optional")
    lines.append("  parameters       Optional")
    lines.append("  metadata         Optional")
    lines.append("")

    lines.append("EXAMPLE (minimal):")
    lines.append("")
    lines.append("file_info:")
    lines.append("  top_module: inverter")
    lines.append("models:")
    lines.append("  nmos:")
    lines.append("    type: pdk_device")
    lines.append("    ports: [d, g, s, b]")
    lines.append("    device_line: XNMOS %d %g %s %b nmos_model")
    lines.append("modules:")
    lines.append("  inverter:")
    lines.append("    ports:")
    lines.append("      in:")
    lines.append("        dir: in")
    lines.append("        type: voltage")
    lines.append("      out:")
    lines.append("        dir: out")
    lines.append("        type: voltage")
    lines.append("    internal_nets: [vdd, vss]")
    lines.append("    instances:")
    lines.append("      mn1:")
    lines.append("        model: nmos")
    lines.append("        mappings: {d: out, g: in, s: vss, b: vss}")

    return "\n".join(lines) + "\n"


