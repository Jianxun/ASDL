"""
Simplified import parser for MVP.

Handles direct file path imports without complex ImportDeclaration objects.
Validates .asdl file extension and basic format requirements.
"""

from typing import Any, Dict, List, Optional, cast
from pathlib import Path

from ...diagnostics import Diagnostic, DiagnosticSeverity
from ..core.locatable_builder import LocatableBuilder, YAMLObject
from ..resolvers.field_validator import FieldValidator


class ImportParser:
    """Handles simplified import parsing with file path validation."""
    
    def __init__(self, locatable_builder: LocatableBuilder, field_validator: FieldValidator):
        """Initialize with dependencies."""
        self.locatable_builder = locatable_builder
        self.field_validator = field_validator
    
    def parse(self, data: Any, diagnostics: List[Diagnostic], file_path: Optional[Path]) -> Optional[Dict[str, str]]:
        """
        Parse simplified imports section.
        
        MVP implementation using direct file paths.
        Validates .asdl file extension requirement.
        
        Args:
            data: Import section data
            diagnostics: List to append diagnostics to
            file_path: Optional file path for location tracking
            
        Returns:
            Dictionary of alias -> file_path mappings or None if no imports
        """
        if not data:
            return None
            
        if not self.field_validator.validate_section_is_dict(data, 'imports', diagnostics, file_path):
            return None

        imports = {}
        yaml_data = cast(YAMLObject, data)
        for alias, file_path_str in yaml_data.items():
            loc = self.locatable_builder.from_yaml_key(yaml_data, alias, file_path)
            
            # Validate import format: alias: path/to/file.asdl
            if not isinstance(file_path_str, str):
                diagnostics.append(Diagnostic(
                    code="I0501",
                    title="Invalid Import Path Type",
                    details=f"Import '{alias}' path must be a string, got {type(file_path_str).__name__}.",
                    severity=DiagnosticSeverity.ERROR,
                    location=loc,
                    suggestion="Use format 'alias: path/to/file.asdl'."
                ))
                continue
                
            # Validate .asdl extension
            if not file_path_str.endswith('.asdl'):
                diagnostics.append(Diagnostic(
                    code="I0502", 
                    title="Invalid Import File Extension",
                    details=f"Import '{alias}' must reference a .asdl file, got '{file_path_str}'.",
                    severity=DiagnosticSeverity.ERROR,
                    location=loc,
                    suggestion="Import paths must end with '.asdl' extension."
                ))
                continue
                
            imports[alias] = file_path_str
        return imports