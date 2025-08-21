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
    ASDLFile, FileInfo, ImportDeclaration,
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
        self._yaml.composer.anchors = {} # Silence anchor warnings
    
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
            
        return self.parse_string(content, file_path)
    
    def parse_string(self, yaml_content: str, file_path: Optional[Path] = None) -> Tuple[Optional[ASDLFile], List[Diagnostic]]:
        """
        Parse an ASDL YAML string into data structures.
        
        Args:
            yaml_content: YAML content as a string.
            file_path: Optional path to the file for location tracking.
            
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
                    file_path=file_path,
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
            loc = Locatable(start_line=1, start_col=1, file_path=file_path)
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
                location=Locatable(start_line=1, start_col=1, file_path=file_path),
                suggestion="Add a 'file_info' section with at least a 'top_module' key."
            ))
            return None, diagnostics

        yaml_data = cast(YAMLObject, data)
            
        file_info = self._parse_file_info(yaml_data, 'file_info', file_path)
        imports = self._parse_imports(yaml_data.get('imports', {}), diagnostics, file_path)
        modules = self._parse_modules(yaml_data.get('modules', {}), diagnostics, file_path)
        
        # Check for unknown top-level sections
        allowed_keys = {'file_info', 'imports', 'modules'}
        if isinstance(data, dict):
            for key in data.keys():
                if key not in allowed_keys:
                    loc = self._get_locatable_from_key(yaml_data, key, file_path)
                    diagnostics.append(Diagnostic(
                        code="P200",
                        title="Unknown Top-Level Section",
                        details=f"The top-level section '{key}' is not a recognized ASDL section.",
                        severity=DiagnosticSeverity.WARNING,
                        location=loc,
                        suggestion=f"Recognized sections are: {', '.join(allowed_keys)}. Please check for a typo or remove the section if it is not needed."
                    ))
        
        asdl_file = ASDLFile(
            file_info=file_info,
            imports=imports,
            modules=modules
        )
        return asdl_file, diagnostics
    
    def _get_locatable_from_key(self, parent_data: YAMLObject, key: str, file_path: Optional[Path]) -> Locatable:
        """Extracts a full Locatable object from a ruamel.yaml key."""
        loc = Locatable(file_path=file_path)
        try:
            # .lc.key(key) returns a tuple of (line, col) for the key
            key_line, key_col = parent_data.lc.key(key)
            loc.start_line = key_line + 1
            loc.start_col = key_col + 1

            # The end location is harder. We can get the location of the value node.
            value_node = parent_data[key]
            if hasattr(value_node, 'lc') and hasattr(value_node.lc, 'end_mark') and value_node.lc.end_mark is not None:
                end_mark = value_node.lc.end_mark
                loc.end_line = end_mark.line + 1
                loc.end_col = end_mark.column + 1
            elif loc.start_line is not None and loc.start_col is not None:
                # Fallback: for scalars, the end is on the same line.
                # This is an approximation.
                loc.end_line = loc.start_line
                loc.end_col = loc.start_col + len(key)
        except (AttributeError, KeyError, TypeError):
            # Fallback for objects that don't have detailed location info
            pass
        return loc

    def _parse_file_info(self, parent_data: YAMLObject, key: str, file_path: Optional[Path]) -> FileInfo:
        """Parse the file_info section."""
        data = parent_data.get(key, {})
        loc = self._get_locatable_from_key(parent_data, key, file_path)

        return FileInfo(
            **loc.__dict__,
            top_module=data.get('top_module'),
            doc=data.get('doc'),
            revision=data.get('revision'),
            author=data.get('author'),
            date=data.get('date'),
            metadata=data.get('metadata')
        )
    
    def _parse_imports(self, data: Any, diagnostics: List[Diagnostic], file_path: Optional[Path]) -> Optional[Dict[str, ImportDeclaration]]:
        """Parse the imports section."""
        if not data:
            return None
            
        if not self._validate_section_is_dict(data, 'imports', diagnostics, file_path):
            return None

        imports = {}
        yaml_data = cast(YAMLObject, data)
        for alias, qualified_source in yaml_data.items():
            loc = self._get_locatable_from_key(yaml_data, alias, file_path)
            
            # Parse qualified_source which can be library.filename or library.filename@version
            version = None
            if isinstance(qualified_source, str) and '@' in qualified_source:
                qualified_source, version = qualified_source.split('@', 1)
            
            # Validate import format: alias: library.filename[@version]
            if not isinstance(qualified_source, str) or '.' not in qualified_source:
                diagnostics.append(Diagnostic(
                    code="P106",
                    title="Invalid Import Format",
                    details=f"Import '{alias}' has invalid format. Expected 'library.filename[@version]'.",
                    severity=DiagnosticSeverity.ERROR,
                    location=loc,
                    suggestion="Use format 'alias: library.filename' or 'alias: library.filename@version'."
                ))
                continue
                
            imports[alias] = ImportDeclaration(
                **loc.__dict__,
                alias=alias,
                qualified_source=qualified_source,
                version=version
            )
        return imports
    
    def _parse_modules(self, data: Any, diagnostics: List[Diagnostic], file_path: Optional[Path]) -> Dict[str, Module]:
        """Parse the modules section with unified primitive/hierarchical architecture."""
        if not self._validate_section_is_dict(data, 'modules', diagnostics, file_path):
            return {}

        modules = {}
        yaml_data = cast(YAMLObject, data)
        for module_id, module_data in yaml_data.items():
            loc = self._get_locatable_from_key(yaml_data, module_id, file_path)
            
            # Parse all fields
            spice_template = module_data.get('spice_template')
            instances = self._parse_instances(module_data.get('instances'), diagnostics, file_path)
            
            # Validate mutual exclusion: spice_template XOR instances
            has_spice_template = spice_template is not None
            has_instances = instances is not None
            
            if has_spice_template and has_instances:
                diagnostics.append(Diagnostic(
                    code="P107",
                    title="Module Type Conflict",
                    details=f"Module '{module_id}' cannot have both 'spice_template' and 'instances'. Choose one: primitive (spice_template) or hierarchical (instances).",
                    severity=DiagnosticSeverity.ERROR,
                    location=loc,
                    suggestion="Remove either 'spice_template' (to make hierarchical) or 'instances' (to make primitive)."
                ))
                continue
                
            if not has_spice_template and not has_instances:
                diagnostics.append(Diagnostic(
                    code="P108",
                    title="Incomplete Module Definition",
                    details=f"Module '{module_id}' must have either 'spice_template' (primitive) or 'instances' (hierarchical).",
                    severity=DiagnosticSeverity.ERROR,
                    location=loc,
                    suggestion="Add either 'spice_template' for primitive modules or 'instances' for hierarchical modules."
                ))
                continue
            
            # Resolve parameters and variables with dual syntax support
            parameters = self._resolve_parameters_field(
                module_data, f"Module '{module_id}'", diagnostics, loc
            )
            variables = self._resolve_variables_field(
                module_data, f"Module '{module_id}'", diagnostics, loc
            )
            
            # Check for unknown fields in module
            self._validate_unknown_fields(
                module_data, 
                f"Module '{module_id}'",
                ['doc', 'ports', 'internal_nets', 'parameters', 'params', 'variables', 'vars', 
                 'spice_template', 'instances', 'pdk', 'metadata'],
                diagnostics, 
                loc
            )
            
            modules[module_id] = Module(
                **loc.__dict__,
                doc=module_data.get('doc'),
                ports=self._parse_ports(module_data.get('ports'), diagnostics, file_path),
                internal_nets=module_data.get('internal_nets'),
                parameters=parameters,
                variables=variables,
                spice_template=spice_template,
                instances=instances,
                pdk=module_data.get('pdk'),
                metadata=module_data.get('metadata')
            )
        return modules
    
    def _parse_ports(self, data: Any, diagnostics: List[Diagnostic], file_path: Optional[Path]) -> Optional[Dict[str, Port]]:
        """Parse the ports section of a module."""
        if not data:
            return None
        ports = {}
        yaml_data = cast(YAMLObject, data)
        for port_name, port_data in yaml_data.items():
            loc = self._get_locatable_from_key(yaml_data, port_name, file_path)
            
            # Validate required fields
            dir_val = port_data.get('dir')
            if not dir_val:
                diagnostics.append(Diagnostic(
                    code="P104", 
                    title="Missing Required Field", 
                    details=f"Port '{port_name}' is missing the required 'dir' field.", 
                    severity=DiagnosticSeverity.ERROR,
                    location=loc
                ))
                continue
    
            type_val = port_data.get('type')
            if not type_val:
                diagnostics.append(Diagnostic(
                    code="P104", 
                    title="Missing Required Field", 
                    details=f"Port '{port_name}' is missing the required 'type' field.", 
                    severity=DiagnosticSeverity.ERROR,
                    location=loc
                ))
                continue

            # Check for unknown fields in port
            self._validate_unknown_fields(
                port_data,
                f"Port '{port_name}'",
                ['dir', 'type', 'constraints', 'metadata'],
                diagnostics,
                loc
            )

            try:
                ports[port_name] = Port(
                    **loc.__dict__,
                    dir=PortDirection(dir_val.lower()),
                    type=SignalType(type_val.lower()),
                    constraints=self._parse_constraints(port_data.get('constraints')),
                    metadata=port_data.get('metadata')
                )
            except Exception as e:
                diagnostics.append(Diagnostic(
                    code="P105",
                    title="Port Parsing Error",
                    details=f"An error occurred while parsing port '{port_name}': {e}",
                    severity=DiagnosticSeverity.ERROR,
                    location=loc,
                    suggestion="Review the port definition for correctness and try again later."
                ))
        return ports
    
    def _parse_constraints(self, data: Any) -> Optional[PortConstraints]:
        """Parse port constraints (currently a placeholder)."""
        if not data:
            return None
        return PortConstraints(constraints=data)
    
    def _parse_instances(self, data: Any, diagnostics: List[Diagnostic], file_path: Optional[Path]) -> Optional[Dict[str, Instance]]:
        """Parse the instances section of a module."""
        if not data:
            return None
        instances = {}
        yaml_data = cast(YAMLObject, data)
        for instance_name, instance_data in yaml_data.items():
            loc = self._get_locatable_from_key(yaml_data, instance_name, file_path)

            model_val = instance_data.get('model')
            if not model_val:
                diagnostics.append(Diagnostic(
                    code="P104", 
                    title="Missing Required Field", 
                    details=f"Instance '{instance_name}' is missing the required 'model' field.",
                    severity=DiagnosticSeverity.ERROR,
                    location=loc
                ))
                continue

            # Resolve parameters with dual syntax support
            parameters = self._resolve_parameters_field(
                instance_data, f"Instance '{instance_name}'", diagnostics, loc
            )
            
            # Check for unknown fields in instance
            self._validate_unknown_fields(
                instance_data,
                f"Instance '{instance_name}'",
                ['model', 'mappings', 'doc', 'parameters', 'params', 'metadata'],
                diagnostics,
                loc
            )
            
            instances[instance_name] = Instance(
                **loc.__dict__,
                model=model_val,
                mappings=instance_data.get('mappings'),
                doc=instance_data.get('doc'),
                parameters=parameters,
                metadata=instance_data.get('metadata')
            )
        return instances

    def _resolve_parameters_field(self, data: Dict[str, Any], context: str, diagnostics: List[Diagnostic], loc: Locatable) -> Optional[Dict[str, Any]]:
        """
        Resolve parameters field with dual syntax support.
        
        Supports both 'parameters' (canonical) and 'params' (abbreviated).
        Generates warning if both are present.
        
        Args:
            data: Dictionary containing module/instance data
            context: Context string for error messages (e.g., "Module 'test_mod'")
            diagnostics: List to append warnings to
            loc: Location information for diagnostics
            
        Returns:
            Resolved parameters dictionary or None if neither field present
        """
        parameters = data.get('parameters')
        params = data.get('params')
        
        if parameters is not None and params is not None:
            # Both forms present - generate warning and prefer canonical
            diagnostics.append(Diagnostic(
                code="P301",
                title="Dual Parameter Syntax",
                details=f"{context} contains both 'parameters' and 'params' fields. Using 'parameters' and ignoring 'params'.",
                severity=DiagnosticSeverity.WARNING,
                location=loc,
                suggestion="Use either 'parameters' (canonical) or 'params' (abbreviated), but not both."
            ))
            return parameters
        elif parameters is not None:
            return parameters
        elif params is not None:
            return params
        else:
            return None

    def _resolve_variables_field(self, data: Dict[str, Any], context: str, diagnostics: List[Diagnostic], loc: Locatable) -> Optional[Dict[str, Any]]:
        """
        Resolve variables field with dual syntax support.
        
        Supports both 'variables' (canonical) and 'vars' (abbreviated).
        Generates warning if both are present.
        
        Args:
            data: Dictionary containing module data  
            context: Context string for error messages (e.g., "Module 'test_mod'")
            diagnostics: List to append warnings to
            loc: Location information for diagnostics
            
        Returns:
            Resolved variables dictionary or None if neither field present
        """
        variables = data.get('variables')
        vars_abbrev = data.get('vars')
        
        if variables is not None and vars_abbrev is not None:
            # Both forms present - generate warning and prefer canonical
            diagnostics.append(Diagnostic(
                code="P302",
                title="Dual Variables Syntax",
                details=f"{context} contains both 'variables' and 'vars' fields. Using 'variables' and ignoring 'vars'.",
                severity=DiagnosticSeverity.WARNING,
                location=loc,
                suggestion="Use either 'variables' (canonical) or 'vars' (abbreviated), but not both."
            ))
            return variables
        elif variables is not None:
            return variables
        elif vars_abbrev is not None:
            return vars_abbrev
        else:
            return None

    def _validate_section_is_dict(self, data: Any, section_name: str, diagnostics: List[Diagnostic], file_path: Optional[Path]) -> bool:
        """Validates that a section's data is a dictionary."""
        if not isinstance(data, dict):
            diagnostics.append(Diagnostic(
                code="P103",
                title="Invalid Section Type",
                details=f"The '{section_name}' section must be a dictionary (mapping), but found {type(data).__name__}.",
                severity=DiagnosticSeverity.ERROR,
                location=Locatable(start_line=1, start_col=1, file_path=file_path), # Fallback location
                suggestion=f"Ensure the '{section_name}' key is followed by a correctly indented set of key-value pairs."
            ))
            return False
        return True 

    def _validate_unknown_fields(self, data: Dict[str, Any], context: str, allowed_fields: List[str], diagnostics: List[Diagnostic], loc: Locatable) -> None:
        """
        Validate that no unknown fields are present in the data.
        
        Args:
            data: Dictionary containing the fields to validate
            context: Context string for error messages (e.g., "Module 'test_mod'")
            allowed_fields: List of recognized field names
            diagnostics: List to append warnings to
            loc: Location information for diagnostics
        """
        if not isinstance(data, dict):
            return
            
        for field_name in data.keys():
            if field_name not in allowed_fields:
                diagnostics.append(Diagnostic(
                    code="P201",
                    title="Unknown Field",
                    details=f"{context} contains unknown field '{field_name}' which is not a recognized field.",
                    severity=DiagnosticSeverity.WARNING,
                    location=loc,
                    suggestion=f"Remove the '{field_name}' field or check for typos. Recognized fields are: {', '.join(sorted(allowed_fields))}."
                ))