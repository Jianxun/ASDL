"""
Core data structures for ASDL representation.

These classes represent the ASDL schema elements and maintain the original
format including patterns and parameter expressions. Pattern expansion and
parameter resolution are handled as separate explicit steps.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import yaml
import json
from pathlib import Path


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
    
    def to_yaml(self) -> str:
        """
        Convert ASDLFile back to YAML string (round-trip).
        
        Note: Round-trip is only guaranteed for original ASDLFile instances
        (before pattern expansion and parameter resolution).
        
        Returns:
            YAML string representation of the ASDLFile
        """
        # Convert to dictionary, handling enum serialization
        data = self._to_serializable_dict()
        return yaml.dump(data, default_flow_style=False, sort_keys=False)
    
    def save_to_file(self, filepath: str) -> None:
        """
        Save ASDLFile to YAML file (round-trip).
        
        Args:
            filepath: Path to save the YAML file to
        """
        yaml_content = self.to_yaml()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
    
    def to_json(self) -> str:
        """
        Convert ASDLFile to JSON string for debugging.
        
        Returns:
            JSON string representation for debugging purposes
        """
        data = self._to_serializable_dict()
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def dump_json(self, filepath: str) -> None:
        """
        Save ASDLFile as JSON file for debugging.
        
        Args:
            filepath: Path to save the JSON file to
        """
        json_content = self.to_json()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(json_content)
    
    def _to_serializable_dict(self) -> Dict[str, Any]:
        """
        Convert ASDLFile to a dictionary with proper serialization of enums and objects.
        
        Returns:
            Dictionary representation suitable for YAML/JSON serialization
        """
        def convert_value(obj):
            """Recursively convert objects to serializable format."""
            if isinstance(obj, Enum):
                return obj.value
            elif hasattr(obj, '__dict__'):
                return {k: convert_value(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, dict):
                return {k: convert_value(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_value(item) for item in obj]
            else:
                return obj
        
        # Convert the dataclass to dict
        data_dict = asdict(self)
        
        # Apply custom serialization
        result = convert_value(data_dict)
        
        # Use 'file_info' key (v0.4 format) for consistency
        return {
            'file_info': result['file_info'],
            'models': result['models'],
            'modules': result['modules']
        }


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
    # Future device types for extensibility
    AMPLIFIER = "amplifier"
    INDUCTOR = "inductor"
    TRANSMISSION_LINE = "transmission_line"
    CURRENT_SOURCE = "current_source"
    VOLTAGE_SOURCE = "voltage_source"
    # Add more device types as needed
    
    @classmethod
    def _missing_(cls, value):
        """Handle unknown device types gracefully."""
        # Create a pseudo-enum member for unknown types
        # This allows parsing to continue while preserving the original value
        pseudo_member = object.__new__(cls)
        pseudo_member._name_ = f"UNKNOWN_{value.upper()}"
        pseudo_member._value_ = value
        return pseudo_member


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


@dataclass
class Nets:
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
    
    The intent field provides extensible metadata storage for:
    - Design intent annotations: {"purpose": "current mirror", "matching": "critical"}
    - Layout hints: {"placement": "symmetric", "routing": "minimize_parasitic"}
    - Optimization directives: {"optimize": ["power", "area"], "constraint": "speed"}
    - Tool-specific metadata: {"simulator": "spectre", "model_opts": {...}}
    - Future extensions: Any additional fields can be preserved here
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
    nets: Optional[Nets] = None                 # Net declarations
    parameters: Optional[Dict[str, Any]] = None           # Module parameters  
    instances: Optional[Dict[str, Instance]] = None       # instance_id -> Instance 