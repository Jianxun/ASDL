"""
ASDL YAML parser implementation.

Parses ASDL YAML files into the core data structures while preserving
patterns and parameter expressions for later processing.
"""

import yaml
from typing import Dict, Any, Optional
from pathlib import Path

from .data_structures import (
    ASDLFile, FileInfo, DeviceModel, DeviceType, 
    Module, Port, PortDirection, SignalType, PortConstraints,
    NetDeclaration, Instance
)


class ASDLParser:
    """
    YAML parser for ASDL files.
    
    Parses ASDL YAML content into structured data while preserving:
    - Pattern syntax in port names and instance mappings
    - Parameter expressions in values  
    - Intent metadata as free-form dictionaries
    """
    
    def parse_file(self, filepath: str) -> ASDLFile:
        """
        Parse ASDL YAML file into data structures.
        
        Args:
            filepath: Path to the ASDL YAML file
            
        Returns:
            Parsed ASDL file representation
            
        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML parsing fails
            ValueError: If ASDL structure is invalid
        """
        file_path = Path(filepath)
        if not file_path.exists():
            raise FileNotFoundError(f"ASDL file not found: {filepath}")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return self.parse_string(content)
    
    def parse_string(self, yaml_content: str) -> ASDLFile:
        """
        Parse ASDL YAML string into data structures.
        
        Args:
            yaml_content: YAML content as string
            
        Returns:
            Parsed ASDL file representation
            
        Raises:
            yaml.YAMLError: If YAML parsing fails
            ValueError: If ASDL structure is invalid
        """
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Failed to parse YAML: {e}")
        
        if not isinstance(data, dict):
            raise ValueError("ASDL file must contain a YAML dictionary")
            
        # Parse each section
        file_info = self._parse_file_info(data)  # Pass full data to handle both file_info and design_info
        models = self._parse_models(data.get('models', {}))
        modules = self._parse_modules(data.get('modules', {}))
        
        return ASDLFile(
            file_info=file_info,
            models=models,
            modules=modules
        )
    
    def _parse_file_info(self, data: Dict[str, Any]) -> FileInfo:
        """
        Parse file_info section.
        
        Handles both 'file_info' (v0.4) and 'design_info' (legacy) for backwards compatibility.
        """
        # Handle both legacy 'design_info' and new 'file_info' keys
        file_info_data = data.get('file_info')
        if file_info_data is None:
            file_info_data = data.get('design_info', {})
        
        # Validate required fields
        if not isinstance(file_info_data, dict):
            raise ValueError("file_info/design_info must be a dictionary")
        
        return FileInfo(
            top_module=file_info_data.get('top_module', ''),
            doc=file_info_data.get('doc', ''),
            revision=file_info_data.get('revision', ''),
            author=file_info_data.get('author', ''),
            date=file_info_data.get('date', '')
        )
    
    def _parse_models(self, data: Dict[str, Any]) -> Dict[str, DeviceModel]:
        """Parse models section."""
        # TODO: Implement models parsing
        models = {}
        for model_alias, model_data in data.items():
            # Placeholder implementation
            models[model_alias] = DeviceModel(
                model=model_data.get('model', ''),
                type=DeviceType(model_data.get('type', 'nmos')),
                ports=model_data.get('ports', []),
                params=model_data.get('params', {}),
                description=model_data.get('description')
            )
        return models
    
    def _parse_modules(self, data: Dict[str, Any]) -> Dict[str, Module]:
        """Parse modules section.""" 
        # TODO: Implement modules parsing
        modules = {}
        for module_id, module_data in data.items():
            # Placeholder implementation
            modules[module_id] = Module(
                doc=module_data.get('doc'),
                ports=self._parse_ports(module_data.get('ports', {})),
                nets=self._parse_nets(module_data.get('nets')),
                parameters=module_data.get('parameters'),
                instances=self._parse_instances(module_data.get('instances', {}))
            )
        return modules
    
    def _parse_ports(self, data: Dict[str, Any]) -> Dict[str, Port]:
        """Parse ports section."""
        # TODO: Implement port parsing
        ports = {}
        for port_name, port_data in data.items():
            if isinstance(port_data, dict):
                ports[port_name] = Port(
                    dir=PortDirection(port_data.get('dir', 'in')),
                    type=SignalType(port_data.get('type', 'voltage')),
                    constraints=self._parse_constraints(port_data.get('constraints'))
                )
        return ports
    
    def _parse_constraints(self, data: Any) -> Optional[PortConstraints]:
        """Parse port constraints."""
        if data is None:
            return None
        return PortConstraints(constraints=data)
    
    def _parse_nets(self, data: Any) -> Optional[NetDeclaration]:
        """Parse nets section."""
        if data is None:
            return None
        if isinstance(data, dict):
            return NetDeclaration(internal=data.get('internal'))
        return None
    
    def _parse_instances(self, data: Dict[str, Any]) -> Dict[str, Instance]:
        """Parse instances section."""
        # TODO: Implement instance parsing  
        instances = {}
        for instance_id, instance_data in data.items():
            instances[instance_id] = Instance(
                model=instance_data.get('model', ''),
                mappings=instance_data.get('mappings', {}),
                parameters=instance_data.get('parameters'),
                intent=instance_data.get('intent')
            )
        return instances 