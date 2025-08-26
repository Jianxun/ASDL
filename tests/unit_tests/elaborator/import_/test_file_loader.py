"""
Test cases for file_loader.py - File loading with caching and circular dependency detection.

Tests the file loading mechanism, caching behavior, circular import detection,
and integration with the parser system.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from asdl.elaborator.import_.file_loader import FileLoader
from asdl.data_structures import ASDLFile, FileInfo, Module
from asdl.diagnostics import Diagnostic, DiagnosticSeverity


class TestFileLoader:
    """Test cases for file loading with caching and circular dependency detection (Phase 1.2.2)."""
    
    def setup_method(self):
        """Set up test dependencies."""
        # Create a mock parser
        self.mock_parser = Mock()
        self.loader = FileLoader(self.mock_parser)
    
    def test_file_caching_mechanism(self):
        """
        T1.4.1: File Caching Mechanism
        TESTS: Files are cached after first load to avoid duplicate parsing
        VALIDATES: Same file returns cached result on subsequent loads
        ENSURES: Parser is only called once per unique file
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test_module.asdl"
            test_file.write_text("""
file_info:
  top_module: test_module
modules:
  test_mod: {}
""")
            
            # Create mock parsed result
            mock_asdl_file = ASDLFile(
                file_info=FileInfo(top_module="test_module"),
                modules={"test_mod": Module(ports={}, spice_template="test_template")}
            )
            self.mock_parser.parse_file.return_value = (mock_asdl_file, [])
            
            # Load file twice
            result1, diag1 = self.loader.load_file(test_file)
            result2, diag2 = self.loader.load_file(test_file)
            
            # Should return same cached result
            assert result1 is result2  # Same object instance (cached)
            assert len(diag1) == 0
            assert len(diag2) == 0
            
            # Parser should only be called once (use resolved path for comparison)
            self.mock_parser.parse_file.assert_called_once_with(str(test_file.resolve()))
    
    def test_circular_dependency_detection(self):
        """
        T1.4.2: Circular Dependency Detection
        TESTS: Detection of circular imports during loading process
        VALIDATES: Circular dependencies are caught and reported
        ENSURES: Loading stops with appropriate error diagnostic
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create file A that imports B
            file_a = temp_path / "module_a.asdl"
            file_a.write_text("""
file_info:
  top_module: module_a
imports:
  module_b: module_b.asdl
modules:
  mod_a: {}
""")
            
            # Create file B that imports A (circular)
            file_b = temp_path / "module_b.asdl"  
            file_b.write_text("""
file_info:
  top_module: module_b
imports:
  module_a: module_a.asdl
modules:
  mod_b: {}
""")
            
            # Mock parser to return files with imports
            def mock_parse_file(filepath):
                if "module_a.asdl" in filepath:
                    return ASDLFile(
                        file_info=FileInfo(top_module="module_a"),
                        imports={"module_b": "module_b.asdl"},
                        modules={"mod_a": Module(ports={}, spice_template="template_a")}
                    ), []
                elif "module_b.asdl" in filepath:
                    return ASDLFile(
                        file_info=FileInfo(top_module="module_b"), 
                        imports={"module_a": "module_a.asdl"},
                        modules={"mod_b": Module(ports={}, spice_template="template_b")}
                    ), []
            
            self.mock_parser.parse_file.side_effect = mock_parse_file
            
            # Try to load file A when A is already in the loading stack (simulating circular import)
            # For this test, we'll simulate the circular detection logic
            result, diagnostics = self.loader.load_file_with_dependency_check(
                file_a, 
                loading_stack=[file_a.resolve()]  # Simulate A is already being loaded (circular)
            )
            
            # Should detect circular dependency
            assert result is None
            assert len(diagnostics) == 1
            assert diagnostics[0].code == "E0442"
            assert "Circular Import Detected" in diagnostics[0].title
            assert file_a.name in diagnostics[0].details  # Check filename appears in cycle description
    
    def test_parser_integration(self):
        """
        T1.4.3: Parser Integration
        TESTS: Integration with ASDL parser for file loading
        VALIDATES: Parser errors are propagated correctly
        ENSURES: File loading handles parser failures gracefully
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "invalid_syntax.asdl"
            test_file.write_text("invalid: yaml: content")
            
            # Mock parser to return error
            parser_diagnostic = Diagnostic(
                code="P001",
                title="YAML Parse Error",
                details="Invalid YAML syntax",
                severity=DiagnosticSeverity.ERROR
            )
            self.mock_parser.parse_file.return_value = (None, [parser_diagnostic])
            
            # Load file with parser error
            result, diagnostics = self.loader.load_file(test_file)
            
            # Should return None and propagate parser diagnostics
            assert result is None
            assert len(diagnostics) == 1
            assert diagnostics[0].code == "P001"
            assert diagnostics[0].title == "YAML Parse Error"
    
    def test_missing_file_handling(self):
        """
        T1.4.4: Missing File Handling
        TESTS: Behavior when trying to load non-existent file
        VALIDATES: Appropriate error handling for missing files
        ENSURES: Clear diagnostic message for file not found
        """
        non_existent_file = Path("/non/existent/path/missing.asdl")
        
        # Try to load non-existent file
        result, diagnostics = self.loader.load_file(non_existent_file)
        
        # Should return None with file not found diagnostic
        assert result is None
        assert len(diagnostics) == 1
        assert diagnostics[0].code == "E0441"
        assert "Import File Not Found" in diagnostics[0].title
        assert str(non_existent_file) in diagnostics[0].details
        
        # Parser should not be called for non-existent files
        self.mock_parser.parse_file.assert_not_called()
    
    def test_cache_independence_per_file(self):
        """
        T1.4.5: Cache Independence Per File
        TESTS: Different files have independent cache entries
        VALIDATES: Caching doesn't interfere between different files
        ENSURES: Each unique file path has its own cache entry
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create two different files
            file1 = temp_path / "module1.asdl"
            file1.write_text("""
file_info:
  top_module: module1
modules:
  mod1: {}
""")
            
            file2 = temp_path / "module2.asdl"
            file2.write_text("""
file_info:
  top_module: module2
modules:
  mod2: {}
""")
            
            # Create different mock results for each file
            mock_file1 = ASDLFile(
                file_info=FileInfo(top_module="module1"),
                modules={"mod1": Module(ports={}, spice_template="template1")}
            )
            mock_file2 = ASDLFile(
                file_info=FileInfo(top_module="module2"), 
                modules={"mod2": Module(ports={}, spice_template="template2")}
            )
            
            def mock_parse_file(filepath):
                if "module1.asdl" in filepath:
                    return mock_file1, []
                elif "module2.asdl" in filepath:
                    return mock_file2, []
                    
            self.mock_parser.parse_file.side_effect = mock_parse_file
            
            # Load both files
            result1, _ = self.loader.load_file(file1)
            result2, _ = self.loader.load_file(file2)
            
            # Should be different objects
            assert result1 is not result2
            assert result1.file_info.top_module == "module1"
            assert result2.file_info.top_module == "module2"
            
            # Parser should be called twice (once per file)
            assert self.mock_parser.parse_file.call_count == 2