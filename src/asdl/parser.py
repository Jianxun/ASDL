"""
ASDL YAML parser implementation.

Parses ASDL YAML files into the core data structures while preserving
patterns and parameter expressions for later processing.

Future-proofing features:
- Preserves unknown fields for forward compatibility
- Flexible constraint and intent handling  
- Schema version detection and adaptation
- Comprehensive validation and error reporting
"""

from ruamel.yaml import YAML
from typing import Dict, Any, Optional, List
from pathlib import Path

from .data_structures import (
    ASDLFile, FileInfo, DeviceModel, PrimitiveType, 
    Module, Port, PortDirection, SignalType, PortConstraints,
    Instance
)


class ASDLParser:
    """
    YAML parser for ASDL files.
    
    This parser is responsible only for converting ASDL YAML content into
    the raw data structures defined in `data_structures.py`. It does not
    perform any semantic validation. It uses `ruamel.yaml` to allow for
    the future possibility of tracking line numbers for diagnostics.
    """
    
    def __init__(self, preserve_unknown: bool = True):
        """
        Initialize the parser.
        
        Args:
            preserve_unknown: If True, preserve unknown fields in extensible structures.
        """
        self.preserve_unknown = preserve_unknown
        self._yaml = YAML(typ='rt')
    
    def parse_file(self, filepath: str) -> ASDLFile:
        """
        Parse an ASDL YAML file into data structures.
        
        Args:
            filepath: Path to the ASDL YAML file
            
        Returns:
            A raw, un-validated ASDL file representation.
            
        Raises:
            FileNotFoundError: If the file doesn't exist.
            ruamel.yaml.YAMLError: If YAML parsing fails.
        """
        file_path = Path(filepath)
        if not file_path.exists():
            raise FileNotFoundError(f"ASDL file not found: {filepath}")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return self.parse_string(content)
    
    def parse_string(self, yaml_content: str) -> ASDLFile:
        """
        Parse an ASDL YAML string into data structures.
        
        Args:
            yaml_content: YAML content as a string.
            
        Returns:
            A raw, un-validated ASDL file representation.
            
        Raises:
            ruamel.yaml.YAMLError: If YAML parsing fails.
        """
        data = self._yaml.load(yaml_content)
        
        if not isinstance(data, dict):
            # This is a fundamental structure check, so it remains in the parser.
            raise ValueError("ASDL file must contain a YAML dictionary")
            
        file_info = self._parse_file_info(data, 'file_info')
        models = self._parse_models(data.get('models', {}))
        modules = self._parse_modules(data.get('modules', {}))
        
        return ASDLFile(
            file_info=file_info,
            models=models,
            modules=modules
        )
    
    def _parse_file_info(self, parent_data: Any, key: str) -> FileInfo:
        """Parse the file_info section."""
        data = parent_data.get(key, {})
        
        # Get location from the key in the parent mapping
        start_line, start_col = (None, None)
        if hasattr(parent_data, 'lc'):
            line, col = parent_data.lc.key(key)
            if line is not None:
                start_line = line + 1 # ruamel.yaml is 0-indexed for lines
            if col is not None:
                start_col = col + 1 # ruamel.yaml is 0-indexed for columns

        return FileInfo(
            start_line=start_line,
            start_col=start_col,
            top_module=data.get('top_module'),
            doc=data.get('doc'),
            revision=data.get('revision'),
            author=data.get('author'),
            date=data.get('date'),
            metadata=data.get('metadata')
        )
    
    def _parse_models(self, data: Dict[str, Any]) -> Dict[str, DeviceModel]:
        """Parse the models section."""
        models = {}
        for model_alias, model_data in data.items():
            models[model_alias] = DeviceModel(
                type=model_data.get('type'),
                ports=model_data.get('ports'),
                device_line=model_data.get('device_line'),
                doc=model_data.get('doc'),
                parameters=model_data.get('parameters'),
                metadata=model_data.get('metadata')
            )
        return models
    
    def _parse_modules(self, data: Dict[str, Any]) -> Dict[str, Module]:
        """Parse the modules section."""
        modules = {}
        for module_id, module_data in data.items():
            modules[module_id] = Module(
                doc=module_data.get('doc'),
                ports=self._parse_ports(module_data.get('ports')),
                internal_nets=module_data.get('internal_nets'),
                parameters=module_data.get('parameters'),
                instances=self._parse_instances(module_data.get('instances')),
                metadata=module_data.get('metadata')
            )
        return modules
    
    def _parse_ports(self, data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Port]]:
        """Parse the ports section."""
        if data is None:
            return None
            
        ports = {}
        for port_name, port_data in data.items():
            ports[port_name] = Port(
                dir=port_data.get('dir'),
                type=port_data.get('type'),
                constraints=self._parse_constraints(port_data.get('constraints'))
            )
        return ports
    
    def _parse_constraints(self, data: Any) -> Optional[PortConstraints]:
        """Parse port constraints."""
        if data is None:
            return None
        return PortConstraints(constraints=data)
    
    def _parse_instances(self, data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Instance]]:
        """Parse the instances section."""
        if data is None:
            return None
            
        instances = {}
        for instance_id, instance_data in data.items():
            instances[instance_id] = Instance(
                model=instance_data.get('model'),
                mappings=instance_data.get('mappings'),
                doc=instance_data.get('doc'),
                parameters=instance_data.get('parameters'),
                metadata=instance_data.get('metadata')
            )
        return instances 