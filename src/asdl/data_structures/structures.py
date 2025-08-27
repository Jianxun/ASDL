"""
Core data structures for ASDL representation.

These classes represent the ASDL schema elements and maintain the original
format including patterns and parameter expressions. Pattern expansion and
parameter resolution are handled as separate explicit steps.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# Universal metadata type alias
Metadata = Dict[str, Any]


# ─────────────────────────────────────────
# Top-Level Container
# ─────────────────────────────────────────

@dataclass
class ASDLFile:
    """
    Represents a single ASDL file with its unified modules and optional imports.
    
    Each ASDL file is like a library that can be included/imported by other files.
    The unified modules field contains both primitive and hierarchical modules.
    The imports field enables dependency resolution across multiple files.
    The model_alias field provides local shorthand for imported module references.
    """
    file_info: 'FileInfo' = field(
        metadata={"schema": {"description": "Document metadata; does not affect netlisting"}}
    )
    modules: Dict[str, 'Module'] = field(
        metadata={"schema": {"description": "Map of unified module definitions (both primitive and hierarchical)"}}
    )
    imports: Optional[Dict[str, str]] = field(
        default=None,
        metadata={"schema": {"description": "Map of file aliases to .asdl file paths for dependency resolution"}},
    )
    model_alias: Optional[Dict[str, str]] = field(
        default=None,
        metadata={"schema": {"description": "Local module aliases mapping to imported module references (alias.module_name format)"}},
    )
    metadata: Optional[Metadata] = field(
        default=None,
        metadata={"schema": {"description": "Open extension bag; agents should preserve unknown keys"}},
    )


# ─────────────────────────────────────────
# Design Metadata
# ─────────────────────────────────────────

@dataclass
class Locatable:
    """
    Represents a full span in a source file, including start and end
    positions and the file it belongs to.
    """
    # Fields excluded from author-facing schema generation
    __schema_exclude_fields__ = {"file_path", "start_line", "start_col", "end_line", "end_col"}

    file_path: Optional[Path] = None
    start_line: Optional[int] = None
    start_col: Optional[int] = None
    end_line: Optional[int] = None
    end_col: Optional[int] = None

    def __str__(self) -> str:
        """Format location information for display in error messages."""
        parts = []
        
        if self.file_path:
            parts.append(str(self.file_path))
        
        if self.start_line is not None:
            if self.start_col is not None:
                parts.append(f"{self.start_line}:{self.start_col}")
            else:
                parts.append(f"{self.start_line}")
        
        return ":".join(parts) if parts else "unknown location"


@dataclass
class FileInfo(Locatable):
    """Represents the file_info section of an ASDL file."""
    top_module: Optional[str] = field(
        default=None,
        metadata={"schema": {"description": "Default top module name in this ASDL file"}},
    )
    doc: Optional[str] = field(
        default=None,
        metadata={"schema": {"description": "Human-readable description of the design/library"}},
    )
    revision: Optional[str] = field(
        default=None,
        metadata={"schema": {"description": "Revision identifier for this document"}},
    )
    author: Optional[str] = field(
        default=None,
        metadata={"schema": {"description": "Author name or contact"}},
    )
    date: Optional[str] = field(
        default=None,
        metadata={"schema": {"description": "Date string (free-form or ISO 8601)"}},
    )
    metadata: Optional[Dict[str, Any]] = field(
        default=None,
        metadata={"schema": {"description": "Additional metadata for tools and annotations"}},
    )





# ─────────────────────────────────────────
# Module Structure  
# ─────────────────────────────────────────

class PortDirection(Enum):
    """Port direction specification."""
    IN = "in"
    OUT = "out"
    IN_OUT = "in_out"


class PortType(Enum):
    """Port type classification."""
    SIGNAL = "signal"
    POWER = "power"
    GROUND = "ground"
    BIAS = "bias"
    CONTROL = "control"


@dataclass(kw_only=True)
class Port(Locatable):
    """
    Port definition with direction and optional type classification.
    
    Port names may contain patterns (e.g., "in_<p,n>") that will be expanded
    during the pattern expansion phase.
    """
    dir: PortDirection = field(
        metadata={"schema": {"description": "Port direction classification"}}
    )
    type: PortType = field(
        default=PortType.SIGNAL,
        metadata={"schema": {"description": "Optional port type classification; defaults to 'signal'"}},
    )
    metadata: Optional[Metadata] = field(
        default=None, metadata={"schema": {"description": "Arbitrary metadata for tools and annotations"}}
    )


@dataclass(kw_only=True)
class Instance(Locatable):
    """
    Instance of a unified Module.
    
    An Instance represents the usage/instantiation of a Module, which can be either:
    - Primitive Module (has spice_template) -> generates inline SPICE device
    - Hierarchical Module (has instances) -> generates subcircuit call in SPICE
    
    Mappings and parameters may contain patterns and expressions that will
    be resolved during the expansion and resolution phases.
    
    The metadata field provides extensible metadata storage for:
    - Design intent annotations: {"purpose": "current mirror", "matching": "critical"}
    - Layout hints: {"placement": "symmetric", "routing": "minimize_parasitic"}
    - Optimization directives: {"optimize": ["power", "area"], "constraint": "speed"}
    - Tool-specific metadata: {"simulator": "spectre", "model_opts": {...}}
    - Future extensions: Any additional fields can be preserved here
    """
    model: str = field(metadata={"schema": {"description": "Reference to a Module by key/name"}})
    mappings: Dict[str, str] = field(
        metadata={
            "schema": {
                "description": "Map from target module's port names to net names. Keys must match the declared port names of the referenced module."
            }
        }
    )
    doc: Optional[str] = field(
        default=None, metadata={"schema": {"description": "Instance-level documentation"}}
    )
    parameters: Optional[Dict[str, Any]] = field(
        default=None, metadata={"schema": {"description": "Parameter overrides for this instance"}}
    )
    metadata: Optional[Metadata] = field(
        default=None, metadata={"schema": {"description": "Arbitrary metadata for tools and annotations"}}
    )
    
    def is_primitive_instance(self, asdl_file: 'ASDLFile') -> bool:
        """Check if this instance references a primitive Module."""
        return (self.model in asdl_file.modules and 
                asdl_file.modules[self.model].is_primitive())
    
    def is_hierarchical_instance(self, asdl_file: 'ASDLFile') -> bool:
        """Check if this instance references a hierarchical Module."""
        return (self.model in asdl_file.modules and 
                asdl_file.modules[self.model].is_hierarchical())


@dataclass
class Module(Locatable):
    """
    Unified module definition for both primitive and hierarchical circuits.
    
    A Module can be either:
    - Primitive: Has spice_template, renders as inline SPICE device
    - Hierarchical: Has instances, renders as .subckt definition
    
    These are mutually exclusive - a module cannot have both spice_template and instances.
    """
    doc: Optional[str] = field(
        default=None, metadata={"schema": {"description": "Module-level documentation"}}
    )
    ports: Optional[Dict[str, Port]] = field(
        default=None,
        metadata={
            "schema": {
                "description": "Port declarations keyed by port name. Each declared port implicitly defines a net with the same name in the module's interface. Use 'internal_nets' to declare additional local nets."
            }
        },
    )
    internal_nets: Optional[List[str]] = field(
        default=None,
        metadata={
            "schema": {
                "description": "Additional local nets inside the module body. Ports already imply interface nets; use this list for extra internal nodes."
            }
        },
    )
    parameters: Optional[Dict[str, Any]] = field(
        default=None,
        metadata={
            "schema": {
                "description": "Module parameters and default values. Parameters may be overridden per-instance via 'Instance.parameters'."
            }
        },
    )
    variables: Optional[Dict[str, Any]] = field(
        default=None,
        metadata={
            "schema": {
                "description": "Module variables for computed or derived values; variables are not overridable by instances."
            }
        },
    )
    
    # MUTUALLY EXCLUSIVE: Either primitive OR hierarchical
    spice_template: Optional[str] = field(
        default=None,
        metadata={
            "schema": {
                "description": "SPICE device template for primitive modules; implicit placeholder '{name}' resolves to the instance id"
            }
        },
    )
    instances: Optional[Dict[str, Instance]] = field(
        default=None, metadata={"schema": {"description": "Map of instance id to Instance for hierarchical modules"}}
    )
    
    # Additional fields
    pdk: Optional[str] = field(
        default=None,
        metadata={
            "schema": {
                "description": "PDK identifier associated with this module (informational). Note: automatic .include generation is deprecated and handled outside the generator."
            }
        },
    )
    metadata: Optional[Metadata] = field(
        default=None, metadata={"schema": {"description": "Arbitrary metadata for tools and annotations"}}
    )
    
    def __post_init__(self):
        """Validate mutual exclusion constraint and ensure module has implementation."""
        if self.spice_template is not None and self.instances is not None:
            raise ValueError("Module cannot have both spice_template and instances")
        
        if self.spice_template is None and self.instances is None:
            raise ValueError("Module must have either spice_template or instances")
    
    def is_primitive(self) -> bool:
        """Check if this is a primitive module (has spice_template)."""
        return self.spice_template is not None
    
    def is_hierarchical(self) -> bool:
        """Check if this is a hierarchical module (has instances)."""
        return self.instances is not None