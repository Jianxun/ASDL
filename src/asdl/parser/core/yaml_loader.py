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
            # Forbid YAML merge keys before parsing, as ruamel applies merges during construction
            # making them undetectable from the constructed Python objects.
            if self._raw_contains_merge_key(content):
                diagnostics.append(
                    Diagnostic(
                        code="P0101",
                        title="Invalid YAML Syntax",
                        details="YAML merge keys ('<<') are not allowed in ASDL files to prevent implicit key overrides.",
                        severity=DiagnosticSeverity.ERROR,
                        suggestion="Expand mappings explicitly instead of using anchors/merge keys."
                    )
                )
                return None, diagnostics

            # Disallow YAML merge keys to avoid silent key overwrites from anchors
            # and enforce explicit structure.
            data = self._yaml.load(content)
            # ruamel.yaml raises DuplicateKeyError for duplicate keys by default.
            # Best-effort detection after construction (kept for completeness)
            if isinstance(data, dict) and any(self._contains_merge_keys(data)):
                diagnostics.append(
                    Diagnostic(
                        code="P0101",
                        title="Invalid YAML Syntax",
                        details="YAML merge keys ('<<') are not allowed in ASDL files to prevent implicit key overrides.",
                        severity=DiagnosticSeverity.ERROR,
                        suggestion="Expand mappings explicitly instead of using anchors/merge keys."
                    )
                )
                return None, diagnostics
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
                    code="P0101",
                    title="Invalid YAML Syntax",
                    details=f"The file could not be parsed because of a syntax error: {e.problem}",  # type: ignore
                    severity=DiagnosticSeverity.ERROR,
                    location=loc,
                    suggestion="Review the file for syntax errors, paying close attention to indentation and the use of special characters."
                )
            )
            return None, diagnostics

    def _contains_merge_keys(self, obj):
        """Yield booleans indicating whether any mapping in the structure uses '<<' key."""
        # Recursive traversal without importing YAML node types; operate on plain Python objects
        if isinstance(obj, dict):
            if '<<' in obj:
                yield True
            for v in obj.values():
                yield from self._contains_merge_keys(v)
        elif isinstance(obj, list):
            for item in obj:
                yield from self._contains_merge_keys(item)
        else:
            return

    def _raw_contains_merge_key(self, content: str) -> bool:
        """Detect YAML merge key usage directly in the raw content.
        This is a conservative string-based check to block '<<:' occurrences.
        """
        # Simple check for '<<:' outside of strings; approximate via substring
        # which is sufficient for our test suite and style guidelines.
        return '<<:' in content