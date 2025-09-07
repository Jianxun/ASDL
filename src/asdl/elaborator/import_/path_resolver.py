"""
Path resolver for ASDL import system.

Handles ASDL_PATH environment variable parsing, search path resolution order,
and file discovery logic. Supports cross-platform path handling.
"""

import os
from pathlib import Path
from typing import List, Optional


class PathResolver:
    """Handles ASDL_PATH resolution and file discovery."""
    
    # Built-in default search paths (minimal policy)
    DEFAULT_SEARCH_PATHS = ["."]
    
    def __init__(self):
        """Initialize path resolver."""
        pass
    
    def get_search_paths(
        self, 
        cli_paths: Optional[List[str]] = None,
        config_paths: Optional[List[str]] = None
    ) -> List[Path]:
        """
        Get search paths in resolution order: env → defaults.
        
        Args:
            cli_paths: Deprecated; ignored.
            config_paths: Deprecated; ignored.
            
        Returns:
            List of search paths in priority order
        """
        search_paths: List[Path] = []
        
        # 1. Environment variable ASDL_PATH
        env_paths = self._parse_asdl_path()
        search_paths.extend(env_paths)
        
        # 2. Built-in defaults (lowest priority)
        search_paths.extend([Path(p) for p in self.DEFAULT_SEARCH_PATHS])
        
        return search_paths
    
    def _parse_asdl_path(self) -> List[Path]:
        """
        Parse ASDL_PATH environment variable into list of paths.
        
        Handles cross-platform path separators:
        - Unix/Linux/macOS: colon (:) separated  
        - Windows: semicolon (;) separated
        
        Returns:
            List of paths from ASDL_PATH or empty list if not set
        """
        asdl_path = os.environ.get('ASDL_PATH', '')
        if not asdl_path:
            return []
        
        # Determine path separator based on OS
        if os.name == 'nt':  # Windows
            separator = ';'
        else:  # Unix-like (POSIX)
            separator = ':'
        
        # Split and convert to Path objects
        path_strings = asdl_path.split(separator)
        return [Path(p.strip()) for p in path_strings if p.strip()]
    
    def resolve_file_path(
        self, 
        relative_path: str, 
        search_paths: Optional[List[Path]] = None
    ) -> Optional[Path]:
        """
        Resolve a relative import path to absolute file path.
        
        Uses first-match-wins strategy across search paths.
        
        Args:
            relative_path: Relative path to ASDL file (e.g., "gf180mcu/devices.asdl")
            search_paths: Optional search paths (defaults to get_search_paths())
            
        Returns:
            Absolute path to file if found, None if not found in any search path
        """
        if search_paths is None:
            search_paths = self.get_search_paths()
        
        for search_root in search_paths:
            candidate_path = search_root / relative_path
            if candidate_path.exists() and candidate_path.is_file():
                return candidate_path.resolve()  # Return absolute path
        
        return None
    
    def get_probe_paths(self, relative_path: str, search_paths: Optional[List[Path]] = None) -> List[Path]:
        """
        Get list of paths that would be probed for a given relative path.
        
        Useful for diagnostic error messages showing where a file was searched.
        
        Args:
            relative_path: Relative path to ASDL file
            search_paths: Optional search paths (defaults to get_search_paths())
            
        Returns:
            List of absolute paths that would be checked
        """
        if search_paths is None:
            search_paths = self.get_search_paths()
        
        return [(search_root / relative_path).resolve() for search_root in search_paths]