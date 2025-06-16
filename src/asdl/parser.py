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

import yaml
import warnings
from typing import Dict, Any, Optional, Set, List
from pathlib import Path

from .data_structures import (
    ASDLFile, FileInfo, DeviceModel, DeviceType, 
    Module, Port, PortDirection, SignalType, PortConstraints,
    Nets, Instance
)


class ASDLParser:
    """
    YAML parser for ASDL files with future-proofing capabilities.
    
    Parses ASDL YAML content into structured data while preserving:
    - Pattern syntax in port names and instance mappings
    - Parameter expressions in values  
    - Intent metadata as free-form dictionaries
    - Unknown fields for forward compatibility
    - Schema version differences
    """
    
    def __init__(self, strict_mode: bool = False, preserve_unknown: bool = True):
        """
        Initialize parser with configuration options.
        
        Args:
            strict_mode: If True, raise errors for unknown fields. If False, warn only.
            preserve_unknown: If True, preserve unknown fields in extensible structures.
        """
        self.strict_mode = strict_mode
        self.preserve_unknown = preserve_unknown
        self._warnings: List[str] = []
    
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
            
        # Clear warnings from previous parse
        self._warnings = []
        
        # Parse each section with future-proofing
        file_info = self._parse_file_info(data)
        models = self._parse_models(data.get('models', {}))
        modules = self._parse_modules(data.get('modules', {}))
        
        # Check for unknown top-level fields
        known_top_level = {'file_info', 'design_info', 'models', 'modules'}
        self._check_unknown_fields(data, known_top_level, "top-level")
        
        # Report warnings if any
        if self._warnings:
            for warning in self._warnings:
                warnings.warn(warning, UserWarning)
        
        return ASDLFile(
            file_info=file_info,
            models=models,
            modules=modules
        )
    
    def _check_unknown_fields(self, data: Dict[str, Any], known_fields: Set[str], context: str) -> None:
        """
        Check for unknown fields and handle according to parser configuration.
        
        Args:
            data: Dictionary to check
            known_fields: Set of expected field names
            context: Context string for error messages
        """
        unknown_fields = set(data.keys()) - known_fields
        if unknown_fields:
            message = f"Unknown fields in {context}: {unknown_fields}"
            if self.strict_mode:
                raise ValueError(message)
            else:
                self._warnings.append(message)
    
    def _parse_file_info(self, data: Dict[str, Any]) -> FileInfo:
        """
        Parse file_info section with backward compatibility.
        
        Handles both 'file_info' (v0.4) and 'design_info' (legacy) for backwards compatibility.
        """
        # Handle both legacy 'design_info' and new 'file_info' keys
        file_info_data = data.get('file_info')
        if file_info_data is None:
            file_info_data = data.get('design_info', {})
        
        # Validate required fields
        if not isinstance(file_info_data, dict):
            raise ValueError("file_info/design_info must be a dictionary")
        
        # Known fields for this version
        known_fields = {'top_module', 'doc', 'revision', 'author', 'date'}
        self._check_unknown_fields(file_info_data, known_fields, "file_info")
        
        return FileInfo(
            top_module=file_info_data.get('top_module', ''),
            doc=file_info_data.get('doc', ''),
            revision=file_info_data.get('revision', ''),
            author=file_info_data.get('author', ''),
            date=file_info_data.get('date', '')
        )
    
    def _parse_models(self, data: Dict[str, Any]) -> Dict[str, DeviceModel]:
        """Parse models section with robust field handling."""
        models = {}
        for model_alias, model_data in data.items():
            if not isinstance(model_data, dict):
                raise ValueError(f"Model '{model_alias}' must be a dictionary")
            
            # Known fields for DeviceModel (including new fields)
            known_fields = {'model', 'type', 'ports', 'params', 'description', 'doc', 'device_line', 'parameters'}
            self._check_unknown_fields(model_data, known_fields, f"model '{model_alias}'")
            
            # Parse device type with validation
            device_type_str = model_data.get('type', 'nmos')
            try:
                device_type = DeviceType(device_type_str)
            except ValueError:
                raise ValueError(f"Invalid device type '{device_type_str}' in model '{model_alias}'. "
                               f"Valid types: {[dt.value for dt in DeviceType]}")
            
            models[model_alias] = DeviceModel(
                type=device_type,
                ports=model_data.get('ports', []),
                doc=model_data.get('doc'),
                # NEW fields
                device_line=model_data.get('device_line'),
                parameters=model_data.get('parameters'),
                # LEGACY fields (for backward compatibility)
                model=model_data.get('model'),
                params=model_data.get('params'),
                description=model_data.get('description')  # Legacy field
            )
        return models
    
    def _parse_modules(self, data: Dict[str, Any]) -> Dict[str, Module]:
        """Parse modules section with comprehensive field handling."""
        modules = {}
        for module_id, module_data in data.items():
            if not isinstance(module_data, dict):
                raise ValueError(f"Module '{module_id}' must be a dictionary")
            
            # Known fields for Module
            known_fields = {'doc', 'ports', 'nets', 'parameters', 'instances'}
            self._check_unknown_fields(module_data, known_fields, f"module '{module_id}'")
            
            modules[module_id] = Module(
                doc=module_data.get('doc'),
                ports=self._parse_ports(module_data.get('ports'), module_id) if 'ports' in module_data else None,
                nets=self._parse_nets(module_data.get('nets'), module_id),
                parameters=module_data.get('parameters'),
                instances=self._parse_instances(module_data.get('instances'), module_id) if 'instances' in module_data else None
            )
        return modules
    
    def _parse_ports(self, data: Optional[Dict[str, Any]], context: str) -> Optional[Dict[str, Port]]:
        """Parse ports section with validation."""
        if data is None:
            return None
            
        ports = {}
        for port_name, port_data in data.items():
            if isinstance(port_data, dict):
                # Known fields for Port
                known_fields = {'dir', 'type', 'constraints'}
                self._check_unknown_fields(port_data, known_fields, f"port '{port_name}' in {context}")
                
                # Parse direction with validation
                direction_str = port_data.get('dir', 'in')
                try:
                    direction = PortDirection(direction_str)
                except ValueError:
                    raise ValueError(f"Invalid port direction '{direction_str}' for port '{port_name}'. "
                                   f"Valid directions: {[pd.value for pd in PortDirection]}")
                
                # Parse signal type with validation  
                signal_type_str = port_data.get('type', 'voltage')
                try:
                    signal_type = SignalType(signal_type_str)
                except ValueError:
                    raise ValueError(f"Invalid signal type '{signal_type_str}' for port '{port_name}'. "
                                   f"Valid types: {[st.value for st in SignalType]}")
                
                ports[port_name] = Port(
                    dir=direction,
                    type=signal_type,
                    constraints=self._parse_constraints(port_data.get('constraints'), f"port '{port_name}'")
                )
            else:
                # Handle legacy compact port format if needed
                self._warnings.append(f"Port '{port_name}' uses non-dictionary format, assuming defaults")
                ports[port_name] = Port(
                    dir=PortDirection.IN,
                    type=SignalType.VOLTAGE
                )
        return ports
    
    def _parse_constraints(self, data: Any, context: str) -> Optional[PortConstraints]:
        """
        Parse port constraints (placeholder implementation).
        
        Stores constraint data as-is for future processing.
        """
        if data is None:
            return None
        
        # Simple placeholder - store constraints as-is
        return PortConstraints(constraints=data)
    
    def _parse_nets(self, data: Any, context: str) -> Optional[Nets]:
        """Parse nets section with future-proofing."""
        if data is None:
            return None
        
        if isinstance(data, dict):
            # Known fields for Nets
            known_fields = {'internal'}
            self._check_unknown_fields(data, known_fields, f"nets in {context}")
            
            return Nets(internal=data.get('internal'))
        else:
            self._warnings.append(f"Non-dictionary nets format in {context}, treating as internal list")
            if isinstance(data, list):
                return Nets(internal=data)
            else:
                return Nets(internal=[str(data)])
    
    def _parse_instances(self, data: Optional[Dict[str, Any]], context: str) -> Optional[Dict[str, Instance]]:
        """Parse instances section with intent preservation."""
        if data is None:
            return None
            
        instances = {}
        for instance_id, instance_data in data.items():
            if not isinstance(instance_data, dict):
                raise ValueError(f"Instance '{instance_id}' in {context} must be a dictionary")
            
            # Known fields for Instance
            known_fields = {'model', 'mappings', 'parameters', 'intent'}
            unknown_fields = set(instance_data.keys()) - known_fields
            
            # Handle unknown fields specially for instances
            intent_data = instance_data.get('intent', {})
            if unknown_fields and self.preserve_unknown:
                # Move unknown fields to intent for preservation
                if not isinstance(intent_data, dict):
                    intent_data = {}
                for field in unknown_fields:
                    intent_data[f"_unknown_{field}"] = instance_data[field]
                self._warnings.append(f"Unknown fields in instance '{instance_id}' moved to intent: {unknown_fields}")
            else:
                self._check_unknown_fields(instance_data, known_fields, f"instance '{instance_id}' in {context}")
            
            instances[instance_id] = Instance(
                model=instance_data.get('model', ''),
                mappings=instance_data.get('mappings', {}),
                parameters=instance_data.get('parameters'),
                intent=intent_data if intent_data else None
            )
        return instances 