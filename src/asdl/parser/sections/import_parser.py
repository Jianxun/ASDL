"""
Import declarations parser.

Extracts import section parsing functionality from the monolithic parser
with exact preservation of validation logic and P106 diagnostic generation.
"""

from typing import Any, Dict, List, Optional, cast
from pathlib import Path

from ...data_structures import ImportDeclaration
from ...diagnostics import Diagnostic, DiagnosticSeverity
from ..core.locatable_builder import LocatableBuilder, YAMLObject
from ..resolvers.field_validator import FieldValidator


class ImportParser:
    """Handles import declarations parsing with format validation."""
    
    def __init__(self, locatable_builder: LocatableBuilder, field_validator: FieldValidator):
        """Initialize with dependencies."""
        self.locatable_builder = locatable_builder
        self.field_validator = field_validator
    
    def parse(self, data: Any, diagnostics: List[Diagnostic], file_path: Optional[Path]) -> Optional[Dict[str, ImportDeclaration]]:
        """
        Parse imports section.
        
        Exact implementation from _parse_imports() method.
        Preserves P106 import format validation.
        Preserves version parsing logic.
        Preserves all error handling.
        
        Args:
            data: Import section data
            diagnostics: List to append diagnostics to
            file_path: Optional file path for location tracking
            
        Returns:
            Dictionary of import declarations or None if no imports
        """
        if not data:
            return None
            
        if not self.field_validator.validate_section_is_dict(data, 'imports', diagnostics, file_path):
            return None

        imports = {}
        yaml_data = cast(YAMLObject, data)
        for alias, qualified_source in yaml_data.items():
            loc = self.locatable_builder.from_yaml_key(yaml_data, alias, file_path)
            
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