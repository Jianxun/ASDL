"""
Field and section validation utilities.

Extracts validation functionality from the monolithic parser
with exact preservation of validation logic and P103/P201 diagnostic generation.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from ...data_structures import Locatable
from ...diagnostics import Diagnostic, DiagnosticSeverity


class FieldValidator:
    """Handles section and field validation."""
    
    @staticmethod
    def validate_section_is_dict(data: Any, section_name: str, diagnostics: List[Diagnostic], file_path: Optional[Path]) -> bool:
        """
        Validate section is dictionary type.
        
        Exact implementation from _validate_section_is_dict() method.
        Preserves P103 diagnostic generation.
        
        Args:
            data: Data to validate
            section_name: Name of section for error message
            diagnostics: List to append errors to
            file_path: Optional file path for location tracking
            
        Returns:
            True if valid dictionary, False otherwise
        """
        if not isinstance(data, dict):
            diagnostics.append(Diagnostic(
                code="P0202",
                title="Invalid Section Type",
                details=f"The '{section_name}' section must be a dictionary (mapping), but found {type(data).__name__}.",
                severity=DiagnosticSeverity.ERROR,
                location=Locatable(start_line=1, start_col=1, file_path=file_path),  # Fallback location
                suggestion=f"Ensure the '{section_name}' key is followed by a correctly indented set of key-value pairs."
            ))
            return False
        return True

    @staticmethod  
    def validate_unknown_fields(data: Dict[str, Any], context: str, allowed_fields: List[str], 
                               diagnostics: List[Diagnostic], loc: Locatable) -> None:
        """
        Validate that no unknown fields are present in the data.
        
        Exact implementation from _validate_unknown_fields() method.
        Preserves P201 warning generation.
        
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
                    code="P0702",
                    title="Unknown Field",
                    details=f"{context} contains unknown field '{field_name}' which is not a recognized field.",
                    severity=DiagnosticSeverity.WARNING,
                    location=loc,
                    suggestion=f"Remove the '{field_name}' field or check for typos. Recognized fields are: {', '.join(sorted(allowed_fields))}."
                ))