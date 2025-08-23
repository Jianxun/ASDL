"""
Test cases for path_resolver.py - ASDL_PATH resolution and file discovery.

Tests the ASDL_PATH environment variable parsing, search path resolution order,
and file discovery logic for import resolution.
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import sys

# Add src to path for testing
test_dir = Path(__file__).parent
project_root = test_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from asdl.elaborator.import_.path_resolver import PathResolver


class TestPathResolver:
    """Test cases for ASDL_PATH resolution and file discovery (Phase 1.2.2)."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.resolver = PathResolver()
    
    def test_asdl_path_parsing_unix(self):
        """
        T1.3.1: ASDL_PATH Environment Variable Parsing (Unix)
        TESTS: Colon-separated path parsing on Unix systems
        VALIDATES: Path splitting works correctly
        ENSURES: Multiple paths are parsed from environment variable
        """
        test_paths = "/pdks:/workspace/third_party:/home/user/libs"
        
        with patch.dict(os.environ, {'ASDL_PATH': test_paths}):
            with patch('os.name', 'posix'):
                paths = self.resolver.get_search_paths()
        
        expected_paths = [
            Path("/pdks"),
            Path("/workspace/third_party"),
            Path("/home/user/libs")
        ]
        
        # Should include ASDL_PATH entries plus built-in defaults
        asdl_path_entries = paths[:3]  # First 3 should be from ASDL_PATH
        assert asdl_path_entries == expected_paths
    
    @patch('os.name', 'nt')  # Windows
    def test_asdl_path_parsing_windows(self):
        """
        T1.3.2: ASDL_PATH Environment Variable Parsing (Windows)
        TESTS: Semicolon-separated path parsing on Windows systems
        VALIDATES: Cross-platform path handling
        ENSURES: Windows path separators work correctly
        """
        test_paths = r"C:\pdks;D:\workspace\third_party;C:\Users\user\libs"
        
        with patch.dict(os.environ, {'ASDL_PATH': test_paths}):
            paths = self.resolver.get_search_paths()
        
        expected_paths = [
            Path(r"C:\pdks"),
            Path(r"D:\workspace\third_party"),
            Path(r"C:\Users\user\libs")
        ]
        
        # Should include ASDL_PATH entries plus built-in defaults
        asdl_path_entries = paths[:3]  # First 3 should be from ASDL_PATH
        assert asdl_path_entries == expected_paths
    
    def test_search_path_resolution_order(self):
        """
        T1.3.3: Search Path Resolution Order
        TESTS: CLI args → config → environment → defaults precedence
        VALIDATES: Proper resolution order is maintained
        ENSURES: Higher priority paths come first
        """
        # Test with all sources
        cli_paths = ["/cli/path1", "/cli/path2"]
        config_paths = ["/config/path1", "/config/path2"]
        env_path = "/env/path1:/env/path2"
        
        with patch.dict(os.environ, {'ASDL_PATH': env_path}):
            with patch('os.name', 'posix'):
                paths = self.resolver.get_search_paths(
                    cli_paths=cli_paths,
                    config_paths=config_paths
                )
        
        # Should be: CLI, config, env, defaults
        assert paths[:2] == [Path("/cli/path1"), Path("/cli/path2")]
        assert paths[2:4] == [Path("/config/path1"), Path("/config/path2")]
        assert paths[4:6] == [Path("/env/path1"), Path("/env/path2")]
        
        # Check built-in defaults are at the end
        assert Path(".") in paths
        assert Path("libs") in paths
        assert Path("third_party") in paths
    
    def test_file_discovery_and_probing(self):
        """
        T1.3.4: File Discovery and Probing
        TESTS: File existence checking across search paths
        VALIDATES: First-match-wins behavior
        ENSURES: File discovery works correctly
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create directory structure
            (temp_path / "pdks" / "gf180mcu_std_tiles").mkdir(parents=True)
            (temp_path / "workspace" / "gf180mcu_std_tiles").mkdir(parents=True)
            
            # Create file only in the second path
            test_file = temp_path / "workspace" / "gf180mcu_std_tiles" / "devices.asdl"
            test_file.write_text("# Test ASDL file")
            
            # Set up search paths (first path doesn't have the file)
            search_paths = [
                temp_path / "pdks",
                temp_path / "workspace"
            ]
            
            # Should find file in second path (first-match-wins)
            resolved_path = self.resolver.resolve_file_path(
                "gf180mcu_std_tiles/devices.asdl", 
                search_paths
            )
            
            assert resolved_path == test_file.resolve()  # Compare resolved paths
    
    def test_file_not_found_returns_none(self):
        """
        T1.3.5: File Not Found Handling
        TESTS: Behavior when file doesn't exist in any search path
        VALIDATES: Graceful handling of missing files
        ENSURES: Returns None when file cannot be found
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            search_paths = [Path(temp_dir)]
            
            # Try to resolve non-existent file
            resolved_path = self.resolver.resolve_file_path(
                "nonexistent/file.asdl",
                search_paths
            )
            
            assert resolved_path is None
    
    def test_built_in_defaults_included(self):
        """
        T1.3.6: Built-in Default Paths
        TESTS: Built-in search paths are always included
        VALIDATES: Default paths (./,  ./libs, ./third_party) present
        ENSURES: Fallback paths exist when no other configuration
        """
        # Clear environment to test defaults only
        with patch.dict(os.environ, {}, clear=True):
            paths = self.resolver.get_search_paths()
        
        # Check that built-in defaults are present
        path_strings = [str(p) for p in paths]
        assert "." in path_strings or str(Path(".")) in path_strings
        assert "libs" in path_strings or str(Path("libs")) in path_strings  
        assert "third_party" in path_strings or str(Path("third_party")) in path_strings