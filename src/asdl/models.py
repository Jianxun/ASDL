"""
ASDL Data Models

Simple dataclasses to represent the parsed ASDL structure.
Designed for prototype development - prioritize simplicity over optimization.
"""

import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from pathlib import Path


@dataclass
class Circuit:
    """Represents a device or submodule instance within a module's circuits list."""
    name: Optional[str] = None          # Instance name (may have patterns like MN_{P,N})
    model: Optional[str] = None         # Device type or submodule name
    nets: Dict[str, Any] = field(default_factory=dict)  # Pin -> net mappings
    parameters: Dict[str, Any] = field(default_factory=dict)  # Device parameters
    
    def __post_init__(self):
        """Handle various circuit representation formats from YAML."""
        # Handle cases where the circuit is defined as a dict with special keys
        if self.name is None and self.model is None:
            # This might be a circuit defined inline - extract from parameters
            if 'name' in self.parameters:
                self.name = self.parameters.pop('name')
            if 'model' in self.parameters:
                self.model = self.parameters.pop('model')


@dataclass
class ASDLModule:
    """Represents an ASDL module (reusable circuit block)."""
    name: str
    nets: Dict[str, str] = field(default_factory=dict)        # net_name -> role
    parameters: Dict[str, Any] = field(default_factory=dict)  # param hierarchies
    circuits: List[Circuit] = field(default_factory=list)     # devices + submodule instances
    notes: Dict[str, Any] = field(default_factory=dict)       # design intent


@dataclass
class ASDLFile:
    """Represents a complete ASDL file."""
    version: str = ""
    top_module: str = ""
    models: Dict[str, Any] = field(default_factory=dict)      # Physical device models
    modules: Dict[str, ASDLModule] = field(default_factory=dict)
    
    def get_top_module(self) -> Optional[ASDLModule]:
        """Get the top-level module specified by .top_module."""
        return self.modules.get(self.top_module)
    
    def get_module_dependencies(self, module_name: str) -> List[str]:
        """Get list of modules that this module depends on."""
        module = self.modules.get(module_name)
        if not module:
            return []
        
        dependencies = []
        for circuit in module.circuits:
            if circuit.model and circuit.model in self.modules:
                dependencies.append(circuit.model)
        
        return dependencies
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the ASDLFile to a dictionary for JSON serialization."""
        return asdict(self)
    
    def to_json(self, indent: int = 2, sort_keys: bool = True) -> str:
        """
        Convert the ASDLFile to a JSON string for inspection and debugging.
        
        Args:
            indent: Number of spaces for indentation (default: 2)
            sort_keys: Whether to sort dictionary keys (default: True)
            
        Returns:
            JSON string representation of the parsed ASDL structure
        """
        data = self.to_dict()
        return json.dumps(data, indent=indent, sort_keys=sort_keys, ensure_ascii=False)
    
    def save_json(self, filepath: str, indent: int = 2, sort_keys: bool = True) -> None:
        """
        Save the parsed ASDL structure to a JSON file.
        
        Args:
            filepath: Path where to save the JSON file
            indent: Number of spaces for indentation (default: 2)
            sort_keys: Whether to sort dictionary keys (default: True)
        """
        json_content = self.to_json(indent=indent, sort_keys=sort_keys)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(json_content)
        
        print(f"✅ Saved parsed ASDL structure to: {filepath}")
    
    def print_summary(self) -> None:
        """Print a human-readable summary of the parsed ASDL file."""
        print(f"📄 ASDL File Summary:")
        print(f"   Version: {self.version}")
        print(f"   Top Module: {self.top_module}")
        print(f"   Modules: {len(self.modules)}")
        
        for module_name, module in self.modules.items():
            marker = "🎯" if module_name == self.top_module else "📦"
            print(f"   {marker} {module_name}: {len(module.circuits)} circuits, {len(module.nets)} nets")
        
        if self.models:
            print(f"   🔧 Models: {list(self.models.keys())}") 