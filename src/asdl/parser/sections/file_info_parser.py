"""
FileInfo section parser.

Extracts FileInfo section parsing functionality from the monolithic parser
with exact preservation of field extraction logic.
"""

from typing import Optional
from pathlib import Path

from ...data_structures import FileInfo
from ..core.locatable_builder import LocatableBuilder, YAMLObject


class FileInfoParser:
    """Handles FileInfo section parsing."""
    
    def __init__(self, locatable_builder: LocatableBuilder):
        """Initialize with location builder dependency."""
        self.locatable_builder = locatable_builder
    
    def parse(self, parent_data: YAMLObject, key: str, file_path: Optional[Path]) -> FileInfo:
        """
        Parse FileInfo section.
        
        Exact implementation from _parse_file_info() method.
        Pure field extraction, no validation logic.
        
        Args:
            parent_data: YAML object containing the file_info section
            key: Key name ('file_info')
            file_path: Optional file path for location tracking
            
        Returns:
            FileInfo object with extracted data
        """
        data = parent_data.get(key, {})
        loc = self.locatable_builder.from_yaml_key(parent_data, key, file_path)

        return FileInfo(
            **loc.__dict__,
            top_module=data.get('top_module'),
            doc=data.get('doc'),
            revision=data.get('revision'),
            author=data.get('author'),
            date=data.get('date'),
            metadata=data.get('metadata')
        )