"""
Location information extraction utilities.

Extracts location information building functionality from the monolithic parser
with exact preservation of ruamel.yaml location tracking logic.
"""

from typing import Optional, Protocol
from pathlib import Path

from ...data_structures import Locatable


class LCInfo(Protocol):
    """Protocol for ruamel.yaml's line/column info object."""
    line: int
    col: int

    def key(self, key) -> tuple[Optional[int], Optional[int]]: ...
    def value(self, key) -> tuple[Optional[int], Optional[int]]: ...
    def item(self, index: int) -> tuple[Optional[int], Optional[int]]: ...


class YAMLObject(Protocol):
    """Protocol for ruamel.yaml's loaded objects with location info."""
    lc: LCInfo

    def get(self, key, default=None): ...
    def items(self): ...
    def __getitem__(self, key): ...
    def __contains__(self, key) -> bool: ...


class LocatableBuilder:
    """Utility for extracting location information from YAML objects."""
    
    @staticmethod
    def from_yaml_key(parent_data: YAMLObject, key: str, file_path: Optional[Path]) -> Locatable:
        """
        Extract Locatable object from ruamel.yaml key.
        
        Exact implementation from _get_locatable_from_key() method.
        No business logic changes.
        
        Args:
            parent_data: YAML object containing the key
            key: Key name to extract location for
            file_path: Optional file path for location tracking
            
        Returns:
            Locatable object with location information
        """
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