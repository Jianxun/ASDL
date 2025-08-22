"""
YAML loading with location tracking and error diagnostics.

Extracts YAML loading functionality from the monolithic parser
with exact preservation of error handling and diagnostic generation.
"""

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from typing import Any, List, Optional, Tuple
from pathlib import Path

from ...data_structures import Locatable
from ...diagnostics import Diagnostic, DiagnosticSeverity


class YAMLLoader:
    """Handles YAML loading with location tracking and error diagnostics."""
    
    def __init__(self):
        """Initialize YAML loader with ruamel.yaml configuration."""
        self._yaml = YAML(typ='rt')
        self._yaml.composer.anchors = {}  # Silence anchor warnings
    
    def load_with_diagnostics(self, content: str, file_path: Optional[Path]) -> Tuple[Any, List[Diagnostic]]:
        """
        Load YAML content and return data with any parsing diagnostics.
        
        Args:
            content: YAML content as string
            file_path: Optional path to file for location tracking
            
        Returns:
            Tuple of (parsed_data, diagnostics_list)
            Returns (None, diagnostics) if parsing fails
        """
        diagnostics: List[Diagnostic] = []
        
        try:
            data = self._yaml.load(content)
            return data, diagnostics
        except YAMLError as e:
            # Generate P100 diagnostic exactly as current implementation
            loc = None
            if e.problem_mark:  # type: ignore
                loc = Locatable(
                    file_path=file_path,
                    start_line=e.problem_mark.line + 1,  # type: ignore
                    start_col=e.problem_mark.column + 1,  # type: ignore
                )
            
            diagnostics.append(
                Diagnostic(
                    code="P100",
                    title="Invalid YAML Syntax",
                    details=f"The file could not be parsed because of a syntax error: {e.problem}",  # type: ignore
                    severity=DiagnosticSeverity.ERROR,
                    location=loc,
                    suggestion="Review the file for syntax errors, paying close attention to indentation and the use of special characters."
                )
            )
            return None, diagnostics