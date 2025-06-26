"""
Core data structures for ASDL representation.

These classes represent the ASDL schema elements and maintain the original
format including patterns and parameter expressions. Pattern expansion and
parameter resolution are handled as separate explicit steps.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum

# Universal metadata type alias
Metadata = Dict[str, Any]


# ─────────────────────────────────────────
# Top-Level Container
# ─────────────────────────────────────────

@dataclass
class ASDLFile:
    """
    Represents a single ASDL file with its modules and models.
    
    Each ASDL file is like a library that can be included/imported by other files.
    The full chip design will be composed of multiple ASDL files with dependencies.
    """
    file_info: 'FileInfo'
    models: Dict[str, 'DeviceModel']  # model_alias -> DeviceModel
    modules: Dict[str, 'Module']      # module_id -> Module
    metadata: Optional[Metadata] = None  # Universal metadata field


# ─────────────────────────────────────────
# Design Metadata
# ─────────────────────────────────────────

@dataclass
class FileInfo:
    """File metadata and information from file_info section."""
    top_module: str
    doc: str
    revision: str
    author: str
    date: str  # ISO 8601 format
    metadata: Optional[Metadata] = None  # Universal metadata field


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





@dataclass
class DeviceModel:
    """
    Template for a primitive component, which can be a physical PDK device
    or a built-in SPICE primitive.
    """
    type: PrimitiveType                      # Classifies the origin of the primitive model
    ports: List[str]                         # Defines terminal order, e.g., ['D', 'G', 'S', 'B']
    device_line: str                         # Raw SPICE line with {placeholders}, e.g., "MN {D} {G} {S} {B} nch W={W}"
    doc: Optional[str] = None                # Optional documentation
    parameters: Optional[Dict[str, str]] = None  # Default values for parameters used in device_line
    metadata: Optional[Metadata] = None      # Extensible metadata storage


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
    constraints: Any  # Store raw constraint data as-is


@dataclass
class Port:
    """
    Port definition with direction, type, and optional constraints.
    
    Port names may contain patterns (e.g., "in_<p,n>") that will be expanded
    during the pattern expansion phase.
    """
    dir: PortDirection
    type: SignalType
    constraints: Optional[PortConstraints] = None
    metadata: Optional[Metadata] = None  # Universal metadata field





@dataclass
class Instance:
    """
    Instance of a DeviceModel or Module.
    
    An Instance represents the usage/instantiation of either:
    - A DeviceModel (leaf device) -> generates device line in SPICE
    - A Module (hierarchical) -> generates subcircuit call in SPICE
    
    Mappings and parameters may contain patterns and expressions that will
    be resolved during the expansion and resolution phases.
    
    The metadata field provides extensible metadata storage for:
    - Design intent annotations: {"purpose": "current mirror", "matching": "critical"}
    - Layout hints: {"placement": "symmetric", "routing": "minimize_parasitic"}
    - Optimization directives: {"optimize": ["power", "area"], "constraint": "speed"}
    - Tool-specific metadata: {"simulator": "spectre", "model_opts": {...}}
    - Future extensions: Any additional fields can be preserved here
    """
    model: str                                # References DeviceModel alias or Module name
    mappings: Dict[str, str]                  # Port-to-net mapping (may contain patterns)
    doc: Optional[str] = None                 # Instance documentation (first-class citizen)
    parameters: Optional[Dict[str, Any]] = None  # Instance parameters (may contain expressions)
    metadata: Optional[Metadata] = None       # Universal metadata field
    
    def is_device_instance(self, asdl_file: 'ASDLFile') -> bool:
        """Check if this instance references a DeviceModel."""
        return self.model in asdl_file.models
    
    def is_module_instance(self, asdl_file: 'ASDLFile') -> bool:
        """Check if this instance references a Module."""
        return self.model in asdl_file.modules


@dataclass
class Module:
    """
    Circuit module definition.
    
    A Module is a template/definition that describes:
    - Interface (ports)
    - Internal structure (instances and connectivity)
    - Parameters for customization
    
    Each Module becomes a .subckt definition in SPICE.
    """
    doc: Optional[str] = None
    ports: Optional[Dict[str, Port]] = None               # port_name -> Port (may contain patterns)
    internal_nets: Optional[List[str]] = None             # Internal net declarations
    parameters: Optional[Dict[str, Any]] = None           # Module parameters  
    instances: Optional[Dict[str, Instance]] = None       # instance_id -> Instance
    metadata: Optional[Metadata] = None                   # Universal metadata field 