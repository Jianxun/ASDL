"""
Model alias parser for MVP import system.

Handles model_alias section parsing with syntax validation for alias.module_name format.
Validates qualified references and detects format errors.
"""

from typing import Any, Dict, List, Optional, cast
from pathlib import Path
import re

from ...diagnostics import Diagnostic, DiagnosticSeverity
from ..core.locatable_builder import LocatableBuilder, YAMLObject
from ..resolvers.field_validator import FieldValidator


class ModelAliasParser:
    """Handles model_alias section parsing with validation."""
    
    # Regex for valid qualified module reference: alias.module_name
    QUALIFIED_REFERENCE_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*$')
    
    def __init__(self, locatable_builder: LocatableBuilder, field_validator: FieldValidator):
        """Initialize with dependencies."""
        self.locatable_builder = locatable_builder
        self.field_validator = field_validator
    
    def parse(self, data: Any, diagnostics: List[Diagnostic], file_path: Optional[Path]) -> Optional[Dict[str, str]]:
        """
        Parse model_alias section.
        
        MVP implementation with qualified reference validation.
        Validates alias.module_name format requirement.
        
        Args:
            data: Model alias section data
            diagnostics: List to append diagnostics to
            file_path: Optional file path for location tracking
            
        Returns:
            Dictionary of local_alias -> qualified_reference mappings or None if no aliases
        """
        if data is None:
            return None
        
        if not data:  # Empty dict
            return {}
            
        if not self.field_validator.validate_section_is_dict(data, 'model_alias', diagnostics, file_path):
            return None

        model_alias = {}
        yaml_data = cast(YAMLObject, data)
        for local_alias, qualified_ref in yaml_data.items():
            loc = self.locatable_builder.from_yaml_key(yaml_data, local_alias, file_path)
            
            # Validate qualified reference format: local_alias: alias.module_name
            if not isinstance(qualified_ref, str):
                diagnostics.append(Diagnostic(
                    code="P0503",
                    title="Invalid Model Alias Format",
                    details=f"Model alias '{local_alias}' reference must be a string, got {type(qualified_ref).__name__}.",
                    severity=DiagnosticSeverity.ERROR,
                    location=loc,
                    suggestion="Use format 'local_alias: import_alias.module_name'."
                ))
                continue
                
            # Validate alias.module_name pattern
            if not self.QUALIFIED_REFERENCE_PATTERN.match(qualified_ref):
                diagnostics.append(Diagnostic(
                    code="P0503", 
                    title="Invalid Model Alias Format",
                    details=f"Model alias '{local_alias}' reference '{qualified_ref}' must follow 'alias.module_name' format.",
                    severity=DiagnosticSeverity.ERROR,
                    location=loc,
                    suggestion="Use format with dot notation: 'import_alias.module_name'."
                ))
                continue
                
            model_alias[local_alias] = qualified_ref
            
        return model_alias