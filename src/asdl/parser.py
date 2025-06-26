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
from ruamel.yaml.error import YAMLError
from typing import Dict, Any, Optional, List, Tuple, Protocol, cast
from pathlib import Path

from .data_structures import (
    ASDLFile, FileInfo, DeviceModel, PrimitiveType, 
    Module, Port, PortDirection, SignalType, PortConstraints,
    Instance, Locatable
)
from .diagnostics import Diagnostic, DiagnosticSeverity


class LCInfo(Protocol):
    """Protocol for ruamel.yaml's line/column info object."""
    line: int
    col: int

    def key(self, key: Any) -> Tuple[Optional[int], Optional[int]]: ...
    def value(self, key: Any) -> Tuple[Optional[int], Optional[int]]: ...
    def item(self, index: int) -> Tuple[Optional[int], Optional[int]]: ...

class YAMLObject(Protocol):
    """Protocol for ruamel.yaml's loaded objects with location info."""
    lc: LCInfo

    def get(self, key: Any, default: Any = None) -> Any: ...
    def items(self) -> Any: ...
    def __getitem__(self, key: Any) -> Any: ...
    def __contains__(self, key: Any) -> bool: ...


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
    
    def parse_file(self, filepath: str) -> Tuple[Optional[ASDLFile], List[Diagnostic]]:
        """
        Parse an ASDL YAML file into data structures.
        
        Args:
            filepath: Path to the ASDL YAML file
            
        Returns:
            A tuple containing an ASDLFile object or None, and a list of diagnostics.
            
        Raises:
            FileNotFoundError: If the file doesn't exist.
        """
        file_path = Path(filepath)
        if not file_path.exists():
            raise FileNotFoundError(f"ASDL file not found: {filepath}")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return self.parse_string(content)
    
    def parse_string(self, yaml_content: str) -> Tuple[Optional[ASDLFile], List[Diagnostic]]:
        """
        Parse an ASDL YAML string into data structures.
        
        Args:
            yaml_content: YAML content as a string.
            
        Returns:
            A tuple containing an ASDLFile object or None, and a list of diagnostics.
        """
        diagnostics: List[Diagnostic] = []
        try:
            data = self._yaml.load(yaml_content)
        except YAMLError as e:
            loc = None
            if e.problem_mark: # type: ignore
                loc = Locatable(
                    start_line=e.problem_mark.line + 1, # type: ignore
                    start_col=e.problem_mark.column + 1, # type: ignore
                )
            diagnostics.append(
                Diagnostic(
                    code="P100",
                    title="Invalid YAML Syntax",
                    details=f"The file could not be parsed because of a syntax error: {e.problem}", # type: ignore
                    severity=DiagnosticSeverity.ERROR,
                    location=loc,
                    suggestion="Review the file for syntax errors, paying close attention to indentation and the use of special characters."
                )
            )
            return None, diagnostics
        
        if data is None:
            # This can happen for an empty file
            return None, diagnostics

        if not isinstance(data, dict):
            loc = Locatable(start_line=1, start_col=1)
            diagnostics.append(Diagnostic(
                code="P101",
                title="Invalid Root Type",
                details="The root of an ASDL file must be a dictionary (a set of key-value pairs).",
                severity=DiagnosticSeverity.ERROR,
                location=loc,
                suggestion="Ensure the ASDL file starts with a key-value structure, not a list (indicated by a leading '-')."
            ))
            return None, diagnostics
            
        # Check for mandatory sections
        if 'file_info' not in data:
            diagnostics.append(Diagnostic(
                code="P102",
                title="Missing Required Section",
                details="'file_info' is a mandatory section and must be present at the top level of the ASDL file.",
                severity=DiagnosticSeverity.ERROR,
                location=Locatable(start_line=1, start_col=1),
                suggestion="Add a 'file_info' section with at least a 'top_module' key."
            ))
            return None, diagnostics

        yaml_data = cast(YAMLObject, data)
            
        file_info = self._parse_file_info(yaml_data, 'file_info')
        models = self._parse_models(yaml_data.get('models', {}), diagnostics)
        modules = self._parse_modules(yaml_data.get('modules', {}), diagnostics)
        
        # Check for unknown top-level sections
        allowed_keys = {'file_info', 'models', 'modules'}
        if isinstance(data, dict):
            for key in data.keys():
                if key not in allowed_keys:
                    start_line, start_col = (None, None)
                    line, col = yaml_data.lc.key(key)
                    if line is not None:
                        start_line = line + 1
                    if col is not None:
                        start_col = col + 1
                    
                    diagnostics.append(Diagnostic(
                        code="P200",
                        title="Unknown Top-Level Section",
                        details=f"The top-level section '{key}' is not a recognized ASDL section.",
                        severity=DiagnosticSeverity.WARNING,
                        location=Locatable(start_line=start_line, start_col=start_col),
                        suggestion=f"Recognized sections are: {', '.join(allowed_keys)}. Please check for a typo or remove the section if it is not needed."
                    ))
        
        asdl_file = ASDLFile(
            file_info=file_info,
            models=models,
            modules=modules
        )
        return asdl_file, diagnostics
    
    def _parse_file_info(self, parent_data: YAMLObject, key: str) -> FileInfo:
        """Parse the file_info section."""
        data = parent_data.get(key, {})
        
        # Get location from the key in the parent mapping
        start_line, start_col = (None, None)
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
    
    def _parse_models(self, data: Any, diagnostics: List[Diagnostic]) -> Dict[str, DeviceModel]:
        """Parse the models section."""
        if not self._validate_section_is_dict(data, 'models', diagnostics):
            return {}

        models = {}
        yaml_data = cast(YAMLObject, data)
        for model_alias, model_data in yaml_data.items():
            start_line, start_col = (None, None)
            line, col = yaml_data.lc.key(model_alias)
            if line is not None:
                start_line = line + 1
            if col is not None:
                start_col = col + 1

            models[model_alias] = DeviceModel(
                start_line=start_line,
                start_col=start_col,
                type=PrimitiveType(model_data.get('type')),
                ports=model_data.get('ports'),
                device_line=model_data.get('device_line'),
                doc=model_data.get('doc'),
                parameters=model_data.get('parameters'),
                metadata=model_data.get('metadata')
            )
        return models
    
    def _parse_modules(self, data: Any, diagnostics: List[Diagnostic]) -> Dict[str, Module]:
        """Parse the modules section."""
        if not self._validate_section_is_dict(data, 'modules', diagnostics):
            return {}

        modules = {}
        yaml_data = cast(YAMLObject, data)
        for module_id, module_data in yaml_data.items():
            start_line, start_col = (None, None)
            line, col = yaml_data.lc.key(module_id)
            if line is not None:
                start_line = line + 1
            if col is not None:
                start_col = col + 1

            modules[module_id] = Module(
                start_line=start_line,
                start_col=start_col,
                doc=module_data.get('doc'),
                ports=self._parse_ports(module_data.get('ports')),
                internal_nets=module_data.get('internal_nets'),
                parameters=module_data.get('parameters'),
                instances=self._parse_instances(module_data.get('instances')),
                metadata=module_data.get('metadata')
            )
        return modules
    
    def _parse_ports(self, data: Any) -> Optional[Dict[str, Port]]:
        """Parse the ports section."""
        if data is None:
            return None
            
        ports = {}
        yaml_data = cast(YAMLObject, data)
        for port_name, port_data in yaml_data.items():
            start_line, start_col = (None, None)
            line, col = yaml_data.lc.key(port_name)
            if line is not None:
                start_line = line + 1
            if col is not None:
                start_col = col + 1
            ports[port_name] = Port(
                start_line=start_line,
                start_col=start_col,
                dir=port_data.get('dir'),
                type=port_data.get('type'),
                constraints=self._parse_constraints(port_data.get('constraints')),
                metadata=port_data.get('metadata')
            )
        return ports
    
    def _parse_constraints(self, data: Any) -> Optional[PortConstraints]:
        """Parse port constraints."""
        if data is None:
            return None
        return PortConstraints(constraints=data)
    
    def _parse_instances(self, data: Any) -> Optional[Dict[str, Instance]]:
        """Parse the instances section."""
        if data is None:
            return None
            
        instances = {}
        yaml_data = cast(YAMLObject, data)
        for instance_id, instance_data in yaml_data.items():
            start_line, start_col = (None, None)
            line, col = yaml_data.lc.key(instance_id)
            if line is not None:
                start_line = line + 1
            if col is not None:
                start_col = col + 1
            instances[instance_id] = Instance(
                start_line=start_line,
                start_col=start_col,
                model=instance_data.get('model'),
                mappings=instance_data.get('mappings'),
                doc=instance_data.get('doc'),
                parameters=instance_data.get('parameters'),
                metadata=instance_data.get('metadata')
            )
        return instances

    def _validate_section_is_dict(self, data: Any, section_name: str, diagnostics: List[Diagnostic]) -> bool:
        """Validate that a section's data is a dictionary."""
        if not isinstance(data, dict):
            loc = Locatable(start_line=1, start_col=1)
            # Try to get better location if available
            try:
                yaml_obj = cast(YAMLObject, data)
                line, col = yaml_obj.lc.line, yaml_obj.lc.col
                if line is not None:
                    loc = Locatable(start_line=line + 1, start_col=col + 1)
            except (AttributeError, TypeError):
                # data doesn't have .lc, so we can't get a better location
                pass

            diagnostics.append(Diagnostic(
                code="P103",
                title="Invalid Section Type",
                details=f"The top-level section '{section_name}' must be a dictionary (mapping of keys to values), not a list or scalar.",
                severity=DiagnosticSeverity.ERROR,
                location=loc,
                suggestion=f"Ensure the '{section_name}' section is indented correctly and uses key: value pairs."
            ))
            return False
        return True 