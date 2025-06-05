"""
ASDL YAML Parser

Converts ASDL YAML files into structured data model objects.
Handles YAML anchors/aliases and basic validation.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Union

from .models import ASDLFile, ASDLModule, Circuit


class ASDLParseError(Exception):
    """Custom exception for ASDL parsing errors."""
    pass


class ASDLParser:
    """Parser for ASDL YAML files."""
    
    def parse_file(self, filepath: Union[str, Path]) -> ASDLFile:
        """Parse an ASDL YAML file and return structured data."""
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise ASDLParseError(f"File not found: {filepath}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                # Use the full YAML loader to handle ${var} expressions
                # This is needed because safe_load can't parse unquoted ${...} in flow mappings
                data = yaml.load(f, Loader=yaml.FullLoader)
        except yaml.YAMLError as e:
            raise ASDLParseError(f"YAML parsing error: {e}")
        
        if not isinstance(data, dict):
            raise ASDLParseError("ASDL file must contain a YAML dictionary")
        
        return self._parse_asdl_data(data)
    
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
            # Parse YAML with full loader to handle anchors/aliases
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
    
    def parse_and_dump(self, filepath: Path, output_json: str = None) -> ASDLFile:
        """
        Parse an ASDL file and immediately dump it to JSON for inspection.
        
        Args:
            filepath: Path to ASDL YAML file
            output_json: Optional path for JSON output (default: same name with .json extension)
            
        Returns:
            Parsed ASDLFile object
        """
        # Parse the file
        asdl_file = self.parse_file(filepath)
        
        # Determine output filename
        if output_json is None:
            output_json = str(filepath).replace('.yaml', '_parsed.json').replace('.yml', '_parsed.json')
        
        # Dump to JSON
        asdl_file.save_json(output_json)
        
        # Print summary
        asdl_file.print_summary()
        
        return asdl_file
    
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
        circuits = self._parse_circuits(data.get('circuits', []))
        
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
        
        circuits = []
        
        if isinstance(circuits_data, list):
            # List format: circuits: [circuit1, circuit2, ...]
            for i, circuit_item in enumerate(circuits_data):
                try:
                    circuit = self._parse_circuit_item(circuit_item)
                    circuits.append(circuit)
                except Exception as e:
                    raise ASDLParseError(f"Error parsing circuit item {i}: {e}")
        
        elif isinstance(circuits_data, dict):
            # Dictionary format: circuits: {name1: circuit1, name2: circuit2, ...}
            for circuit_name, circuit_data in circuits_data.items():
                try:
                    circuit = self._parse_circuit_item(circuit_data)
                    # If circuit doesn't have a name, use the key
                    if not circuit.name:
                        circuit.name = circuit_name
                    circuits.append(circuit)
                except Exception as e:
                    raise ASDLParseError(f"Error parsing circuit '{circuit_name}': {e}")
        
        else:
            raise ASDLParseError("'circuits' must be a list or dictionary")
        
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
        
        # Handle special YAML merge key
        if '<<' in data:
            # YAML merge - this means anchor data was merged in
            # The anchor data is already merged by PyYAML, just remove the merge key
            data.pop('<<')
        
        # Handle special keys for jumpers and other components
        if 'jumper' in data:
            jumper_data = data.pop('jumper')
            if isinstance(jumper_data, dict):
                # Jumper is a special component type
                if not name:
                    name = jumper_data.get('name', 'jumper')
                if not model:
                    model = 'jumper'
                # Add jumper-specific parameters
                data.update(jumper_data)
        
        # Everything else goes into parameters
        parameters = data
        
        return Circuit(
            name=name,
            model=model,
            nets=nets,
            parameters=parameters
        ) 