"""
Main ASDL parser with modular architecture.

Refactored from monolithic parser.py to use modular components
while preserving exact existing behavior and API.
"""

from typing import Dict, Any, Optional, List, Tuple, cast
from pathlib import Path

from ..data_structures import ASDLFile, Locatable
from ..diagnostics import Diagnostic, DiagnosticSeverity
from .core import YAMLLoader, LocatableBuilder
from .resolvers import DualSyntaxResolver, FieldValidator
from .sections import FileInfoParser, ImportParser, ModelAliasParser, PortParser, InstanceParser, ModuleParser


class ASDLParser:
    """
    YAML parser for ASDL files with modular architecture.
    
    This parser is responsible only for converting ASDL YAML content into
    the raw data structures defined in `data_structures.py`. It does not
    perform any semantic validation. It uses `ruamel.yaml` to allow for
    the future possibility of tracking line numbers for diagnostics.
    """
    
    def __init__(self, preserve_unknown: bool = True, *, emit_empty_file_info: bool = False):
        """
        Initialize the parser with dependency injection.
        
        Args:
            preserve_unknown: If True, preserve unknown fields in extensible structures.
            emit_empty_file_info: If True, emit informational diagnostic P0103 for empty files.
        """
        self.preserve_unknown = preserve_unknown
        self.emit_empty_file_info = emit_empty_file_info
        
        # Create all utility components
        self.yaml_loader = YAMLLoader()
        self.locatable_builder = LocatableBuilder()
        self.field_validator = FieldValidator()
        self.dual_syntax_resolver = DualSyntaxResolver()
        
        # Create section parsers with dependencies
        self.file_info_parser = FileInfoParser(self.locatable_builder)
        self.import_parser = ImportParser(self.locatable_builder, self.field_validator)
        self.model_alias_parser = ModelAliasParser(self.locatable_builder, self.field_validator)
        self.port_parser = PortParser(self.locatable_builder, self.field_validator)
        self.instance_parser = InstanceParser(self.locatable_builder, self.field_validator, self.dual_syntax_resolver)
        self.module_parser = ModuleParser(self.port_parser, self.instance_parser,
                                        self.dual_syntax_resolver, self.field_validator, self.locatable_builder)
    
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
        Parse an ASDL YAML string into data structures - refactored to use modular parsers.
        
        Args:
            yaml_content: YAML content as a string.
            file_path: Optional path to the file for location tracking.
            
        Returns:
            A tuple containing an ASDLFile object or None, and a list of diagnostics.
        """
        diagnostics: List[Diagnostic] = []
        
        # 1. YAML loading with error handling
        data, yaml_diagnostics = self.yaml_loader.load_with_diagnostics(yaml_content, file_path)
        diagnostics.extend(yaml_diagnostics)
        if data is None:
            # If no YAML errors were emitted and the content is effectively empty,
            # optionally emit an informational diagnostic P0103 and return.
            if (
                self.emit_empty_file_info
                and not diagnostics
                and (yaml_content.strip() == "" or yaml_content.strip() == "---")
            ):
                diagnostics.append(Diagnostic(
                    code="P0103",
                    title="Empty File",
                    details="The ASDL file is empty. There is nothing to parse.",
                    severity=DiagnosticSeverity.INFO,
                    location=Locatable(start_line=1, start_col=1, file_path=file_path),
                ))
            return None, diagnostics
        
        if data is None:
            # This can happen for an empty file
            return None, diagnostics

        # 2. Root validation (XCCSS codes)
        if not isinstance(data, dict):
            loc = Locatable(start_line=1, start_col=1, file_path=file_path)
            diagnostics.append(Diagnostic(
                code="P0102",
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
                code="P0201",
                title="Missing Required Section",
                details="'file_info' is a mandatory section and must be present at the top level of the ASDL file.",
                severity=DiagnosticSeverity.ERROR,
                location=Locatable(start_line=1, start_col=1, file_path=file_path),
                suggestion="Add a 'file_info' section with at least a 'top_module' key."
            ))
            return None, diagnostics

        # 3. Section parsing with new parsers
        yaml_data = cast(YAMLObject, data)
        file_info = self.file_info_parser.parse(yaml_data, 'file_info', file_path)
        imports = self.import_parser.parse(yaml_data.get('imports', {}), diagnostics, file_path)
        model_alias = self.model_alias_parser.parse(yaml_data.get('model_alias', {}), diagnostics, file_path)
        modules = self.module_parser.parse(yaml_data.get('modules', {}), diagnostics, file_path)
        
        # 4. Unknown top-level section validation (XCCSS P0701)
        allowed_keys = {'file_info', 'imports', 'model_alias', 'modules'}
        if isinstance(data, dict):
            for key in data.keys():
                if key not in allowed_keys:
                    loc = self.locatable_builder.from_yaml_key(yaml_data, key, file_path)
                    diagnostics.append(Diagnostic(
                        code="P0701",
                        title="Unknown Top-Level Section",
                        details=f"The top-level section '{key}' is not a recognized ASDL section.",
                        severity=DiagnosticSeverity.WARNING,
                        location=loc,
                        suggestion=f"Recognized sections are: {', '.join(allowed_keys)}. Please check for a typo or remove the section if it is not needed."
                    ))
        
        # 5. ASDLFile construction
        asdl_file = ASDLFile(
            file_info=file_info,
            imports=imports,
            model_alias=model_alias,
            modules=modules
        )
        return asdl_file, diagnostics


# Import the YAMLObject protocol for type checking
from .core.locatable_builder import YAMLObject