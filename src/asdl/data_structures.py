"""
Core data structures for ASDL representation.

These classes represent the ASDL schema elements and maintain the original
format including patterns and parameter expressions. Pattern expansion and
parameter resolution are handled as separate explicit steps.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from enum import Enum


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


# ─────────────────────────────────────────
# Device Models (PDK Primitives)
# ─────────────────────────────────────────

class DeviceType(Enum):
    """Enumeration of supported device types."""
    NMOS = "nmos"
    PMOS = "pmos"
    RESISTOR = "resistor"
    CAPACITOR = "capacitor"
    DIODE = "diode"
    # Add more device types as needed


@dataclass
class DeviceModel:
    """
    Device template that maps to PDK primitives.
    
    The 'model' field contains the exact PDK model name to use in SPICE,
    and will be used as-is without any transformation.
    """
    model: str                        # PDK model name (used as-is in SPICE)
    type: DeviceType                  # Device type classification
    ports: List[str]                  # Terminal order [G, D, S, B]
    params: Dict[str, Any]            # Default parameters
    description: Optional[str] = None # Optional description


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
    
    Constraints are stored as a flexible dictionary for future implementation.
    This allows us to defer constraint handling while preserving the data.
    """
    constraints: Dict[str, Any]


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


@dataclass
class NetDeclaration:
    """
    Net declaration for module (optional).
    
    Each port implicitly declares a net of the same name. The internal list
    specifies additional nets that are not ports.
    """
    internal: Optional[List[str]] = None
    
    def get_all_nets(self, port_names: List[str]) -> List[str]:
        """
        Get all nets: ports (implicit) + internal (explicit).
        
        Args:
            port_names: List of port names from the module
            
        Returns:
            Combined list of all net names
        """
        nets = list(port_names)  # Ports implicitly declare nets
        if self.internal:
            nets.extend(self.internal)
        return nets


@dataclass
class Instance:
    """
    Instance of a DeviceModel or Module.
    
    An Instance represents the usage/instantiation of either:
    - A DeviceModel (leaf device) -> generates device line in SPICE
    - A Module (hierarchical) -> generates subcircuit call in SPICE
    
    Mappings and parameters may contain patterns and expressions that will
    be resolved during the expansion and resolution phases.
    """
    model: str                                # References DeviceModel alias or Module name
    mappings: Dict[str, str]                  # Port-to-net mapping (may contain patterns)
    parameters: Optional[Dict[str, Any]] = None  # Instance parameters (may contain expressions)
    intent: Optional[Dict[str, Any]] = None      # Free-form intent metadata
    
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
    nets: Optional[NetDeclaration] = None                 # Net declarations
    parameters: Optional[Dict[str, Any]] = None           # Module parameters  
    instances: Optional[Dict[str, Instance]] = None       # instance_id -> Instance 