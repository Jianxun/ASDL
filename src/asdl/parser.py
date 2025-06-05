"""
ASDL YAML Parser

Converts ASDL YAML files into structured data model objects.
Handles YAML parsing and basic validation.
"""

import yaml
from typing import Dict, List, Any

from .models import ASDLFile, ASDLModule, Circuit

class ASDLParseError(Exception):
    """Custom exception for ASDL parsing errors."""
    pass


class ASDLParser:
    """Parser for ASDL YAML files."""
    
    def parse_string(self, yaml_content: str) -> ASDLFile:
        """
        Parse ASDL content from a YAML string.
        
        Args:
            yaml_content: YAML string containing ASDL content
            
        Returns:
            Parsed ASDLFile object
            
        Raises:
            ASDLParseError: If parsing fails
        """
        try:
            # Parse YAML with full loader to handle ${var} expressions
            # This is needed because safe_load can't parse unquoted ${...} in flow mappings
            data = yaml.load(yaml_content, Loader=yaml.FullLoader)
            
            if data is None:
                raise ASDLParseError("Empty YAML content")
            
            if not isinstance(data, dict):
                raise ASDLParseError("ASDL content must be a YAML dictionary")
            
            return self._parse_asdl_data(data)
            
        except yaml.YAMLError as e:
            raise ASDLParseError(f"YAML parsing error: {e}")
        except Exception as e:
            raise ASDLParseError(f"Parsing error: {e}")
    
    def _parse_asdl_data(self, data: Dict[str, Any]) -> ASDLFile:
        """Convert parsed YAML dictionary to ASDLFile object."""
        # Extract file-level metadata
        version = data.get('.version', '')
        top_module = data.get('.top_module', '')
        models = data.get('models', {})
        
        # Parse modules
        modules_data = data.get('modules', {})
        if not isinstance(modules_data, dict):
            raise ASDLParseError("'modules' must be a dictionary")
        
        modules = {}
        for module_name, module_data in modules_data.items():
            try:
                modules[module_name] = self._parse_module(module_name, module_data)
            except Exception as e:
                raise ASDLParseError(f"Error parsing module '{module_name}': {e}")
        
        return ASDLFile(
            version=version,
            top_module=top_module,
            models=models,
            modules=modules
        )
    
    def _parse_module(self, name: str, data: Dict[str, Any]) -> ASDLModule:
        """Parse a single module definition."""
        if not isinstance(data, dict):
            raise ASDLParseError(f"Module '{name}' must be a dictionary")
        
        # Parse nets
        nets = self._parse_nets(data.get('nets', {}))
        
        # Parse parameters
        parameters = data.get('parameters', {})
        
        # Parse circuits
        circuits = self._parse_circuits(data.get('circuits', {}))
        
        # Parse notes
        notes = data.get('notes', {})
        
        return ASDLModule(
            name=name,
            nets=nets,
            parameters=parameters,
            circuits=circuits,
            notes=notes
        )
    
    def _parse_nets(self, nets_data: Any) -> Dict[str, str]:
        """Parse the nets section of a module."""
        if not nets_data:
            return {}
        
        if not isinstance(nets_data, dict):
            raise ASDLParseError("'nets' must be a dictionary")
        
        # Handle pattern expansion in net declarations
        # For now, store as-is and handle expansion later
        nets = {}
        for net_name, role in nets_data.items():
            nets[net_name] = role
        
        return nets
    
    def _parse_circuits(self, circuits_data: Any) -> List[Circuit]:
        """Parse the circuits section of a module."""
        if not circuits_data:
            return []
        
        if not isinstance(circuits_data, dict):
            raise ASDLParseError("'circuits' must be a dictionary")
        
        circuits = []
        circuit_names = set()
        
        for circuit_name, circuit_data in circuits_data.items():
            try:
                circuit = self._parse_circuit_item(circuit_data)
                
                # Use the dictionary key as the circuit name if not explicitly set
                if not circuit.name:
                    circuit.name = circuit_name
                
                # Check for unique names
                if circuit.name in circuit_names:
                    raise ASDLParseError(f"Duplicate circuit name: '{circuit.name}'")
                circuit_names.add(circuit.name)
                
                circuits.append(circuit)
            except Exception as e:
                raise ASDLParseError(f"Error parsing circuit '{circuit_name}': {e}")
        
        return circuits
    
    def _parse_circuit_item(self, circuit_data: Any) -> Circuit:
        """Parse a single circuit item (device or submodule instance)."""
        if not isinstance(circuit_data, dict):
            raise ASDLParseError("Circuit item must be a dictionary")
        
        # Make a copy to avoid modifying the original data
        data = circuit_data.copy()
        
        # Extract known keys
        name = data.pop('name', None)
        model = data.pop('model', None)
        nets = data.pop('nets', {})
        
        # Everything else goes into parameters
        parameters = data
        
        return Circuit(
            name=name,
            model=model,
            nets=nets,
            parameters=parameters
        ) 