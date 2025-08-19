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
    """
    file_info: 'FileInfo'  # schema: description="Document metadata; does not affect netlisting"
    modules: Dict[str, 'Module']  # schema: description="Map of unified module definitions (both primitive and hierarchical)"
    imports: Optional[Dict[str, 'ImportDeclaration']] = None  # schema: description="Map of import aliases to import declarations"
    metadata: Optional[Metadata] = None  # schema: description="Open extension bag; agents should preserve unknown keys"


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
    top_module: Optional[str] = None  # schema: description="Default top module name in this ASDL file"
    doc: Optional[str] = None  # schema: description="Human-readable description of the design/library"
    revision: Optional[str] = None  # schema: description="Revision identifier for this document"
    author: Optional[str] = None  # schema: description="Author name or contact"
    date: Optional[str] = None  # schema: description="Date string"
    metadata: Optional[Dict[str, Any]] = None  # schema: description="Additional metadata for tools and annotations"


@dataclass(kw_only=True)
class ImportDeclaration(Locatable):
    """
    Represents a single import declaration: alias: library.filename[@version]
    
    This enables the import system's qualified name resolution where
    library.filename maps to a file path, and alias.module_name references
    modules within that imported file.
    """
    alias: str  # schema: description="Local alias for the imported file"
    qualified_source: str  # schema: description="library.filename format for source resolution"
    version: Optional[str] = None  # schema: description="Optional @version tag for version-specific imports"


# ─────────────────────────────────────────
# Device Models (PDK Primitives)
# ─────────────────────────────────────────

class PrimitiveType(Enum):
    """
    Classifies the origin of the primitive model.
    
    This enum provides a simple, unambiguous classification:
    - PDK_DEVICE: Physical device model from external PDK library
    - SPICE_DEVICE: Primitive natively understood by SPICE simulator
    """
    PDK_DEVICE = "pdk_device"
    SPICE_DEVICE = "spice_device"


@dataclass(kw_only=True)
class DeviceModel(Locatable):
    """
    Template for a primitive component, which can be a physical PDK device
    or a built-in SPICE primitive.
    """
    type: PrimitiveType  # schema: description="Origin of primitive; determines SPICE interpretation"
    ports: List[str]  # schema: description="Ordered list of port names; order must match device_line"
    device_line: str  # schema: description="SPICE device template or model identifier"
    doc: Optional[str] = None  # schema: description="Documentation for this model"
    parameters: Optional[Dict[str, str]] = None  # schema: description="Default parameter values or expressions"
    metadata: Optional[Metadata] = None  # schema: description="Arbitrary metadata for tools and annotations"


# ─────────────────────────────────────────
# Module Structure  
# ─────────────────────────────────────────

class PortDirection(Enum):
    """Port direction specification."""
    IN = "in"
    OUT = "out"
    IN_OUT = "in_out"


class SignalType(Enum):
    """Signal type classification."""
    VOLTAGE = "voltage"
    CURRENT = "current"
    DIGITAL = "digital"


@dataclass
class PortConstraints:
    """
    Port constraint specification (placeholder implementation).
    
    Constraints are stored as raw data for future implementation.
    This allows us to defer constraint handling while preserving the data.
    """
    constraints: Any  # schema: description="Placeholder for future formal constraints; preserved as-is"


@dataclass(kw_only=True)
class Port(Locatable):
    """
    Port definition with direction, type, and optional constraints.
    
    Port names may contain patterns (e.g., "in_<p,n>") that will be expanded
    during the pattern expansion phase.
    """
    dir: PortDirection  # schema: description="Port direction classification"
    type: SignalType  # schema: description="Port signal type classification"
    constraints: Optional[PortConstraints] = None  # schema: description="Optional constraint object"
    metadata: Optional[Metadata] = None  # schema: description="Arbitrary metadata for tools and annotations"


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
    model: str  # schema: description="Reference to a Module by key/name"
    mappings: Dict[str, str]  # schema: description="Map from target's port names to net names"
    doc: Optional[str] = None  # schema: description="Instance-level documentation"
    parameters: Optional[Dict[str, Any]] = None  # schema: description="Parameter overrides for this instance"
    metadata: Optional[Metadata] = None  # schema: description="Arbitrary metadata for tools and annotations"
    
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
    doc: Optional[str] = None  # schema: description="Module-level documentation"
    ports: Optional[Dict[str, Port]] = None  # schema: description="Port declarations keyed by port name"
    internal_nets: Optional[List[str]] = None  # schema: description="Internal nets local to this module"
    parameters: Optional[Dict[str, Any]] = None  # schema: description="Module parameters and default values"
    
    # MUTUALLY EXCLUSIVE: Either primitive OR hierarchical
    spice_template: Optional[str] = None  # schema: description="SPICE device template for primitive modules"
    instances: Optional[Dict[str, Instance]] = None  # schema: description="Map of instance id to Instance for hierarchical modules"
    
    # Additional fields
    pdk: Optional[str] = None  # schema: description="PDK name for primitive modules (drives .include generation)"
    metadata: Optional[Metadata] = None  # schema: description="Arbitrary metadata for tools and annotations"
    
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