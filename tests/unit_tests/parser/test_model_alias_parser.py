"""
Test cases for model_alias section parser.

Tests the model_alias syntax validation including P0503 error code generation
for invalid qualified reference format.
"""

import pytest
from pathlib import Path
import sys

# Add src to path for testing
test_dir = Path(__file__).parent
project_root = test_dir.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from asdl.parser.sections.model_alias_parser import ModelAliasParser
from asdl.parser.core.locatable_builder import LocatableBuilder
from asdl.parser.resolvers.field_validator import FieldValidator
from asdl.diagnostics import Diagnostic, DiagnosticSeverity


class TestModelAliasParser:
    """Test cases for model_alias syntax validation (Phase 1.2.1)."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.locatable_builder = LocatableBuilder()
        self.field_validator = FieldValidator()
        self.parser = ModelAliasParser(self.locatable_builder, self.field_validator)
    
    def test_valid_model_alias_parsing(self):
        """
        T1.2.1: Valid Model Alias Syntax
        TESTS: Correct alias.module_name format parsing
        VALIDATES: Qualified references work correctly
        ENSURES: No diagnostics for valid syntax
        """
        data = {
            'nmos_unit': 'std_devices.nmos_unit_short',
            'pmos_unit': 'std_devices.pmos_unit_short', 
            'amp_core': 'amplifiers.two_stage_miller'
        }
        diagnostics = []
        file_path = Path("test.asdl")
        
        result = self.parser.parse(data, diagnostics, file_path)
        
        # Should parse successfully
        assert result is not None
        assert len(diagnostics) == 0
        assert result == {
            'nmos_unit': 'std_devices.nmos_unit_short',
            'pmos_unit': 'std_devices.pmos_unit_short',
            'amp_core': 'amplifiers.two_stage_miller'
        }
    
    def test_invalid_format_missing_dot(self):
        """
        T1.2.2: Invalid Format - Missing Dot
        TESTS: P0503 error for missing dot separator
        VALIDATES: Qualified reference validation works
        ENSURES: Diagnostic generated with proper error code
        """
        data = {
            'nmos_unit': 'std_devices_nmos_unit_short',  # Missing dot
            'valid_alias': 'std_devices.pmos_unit_short'
        }
        diagnostics = []
        file_path = Path("test.asdl")
        
        result = self.parser.parse(data, diagnostics, file_path)
        
        # Should parse partially (skip invalid, keep valid)
        assert result is not None
        assert result == {'valid_alias': 'std_devices.pmos_unit_short'}
        
        # Should generate P0503 diagnostic for invalid format
        assert len(diagnostics) == 1
        diag = diagnostics[0]
        assert diag.code == "P0503"
        assert diag.title == "Invalid Model Alias Format"
        assert "must follow 'alias.module_name' format" in diag.details
        assert diag.severity == DiagnosticSeverity.ERROR
    
    def test_invalid_format_non_string_type(self):
        """
        T1.2.3: Invalid Format - Non-String Type
        TESTS: P0503 error for non-string qualified reference
        VALIDATES: Type validation for model alias values
        ENSURES: Diagnostic generated for type mismatch
        """
        data = {
            'nmos_unit': 123,  # Should be string
            'pmos_unit': ['std_devices', 'pmos_unit_short'],  # Should be string
            'valid_alias': 'std_devices.amp_core'
        }
        diagnostics = []
        file_path = Path("test.asdl")
        
        result = self.parser.parse(data, diagnostics, file_path)
        
        # Should parse partially (skip invalid, keep valid)
        assert result is not None
        assert result == {'valid_alias': 'std_devices.amp_core'}
        
        # Should generate P0503 diagnostic for both invalid types
        assert len(diagnostics) == 2
        
        # Check first diagnostic (int type)
        diag1 = diagnostics[0]
        assert diag1.code == "P0503"
        assert diag1.title == "Invalid Model Alias Format"
        assert "must be a string, got int" in diag1.details
        assert diag1.severity == DiagnosticSeverity.ERROR
        
        # Check second diagnostic (list type)
        diag2 = diagnostics[1]
        assert diag2.code == "P0503"
        assert diag2.title == "Invalid Model Alias Format"
        assert "must be a string, got list" in diag2.details
        assert diag2.severity == DiagnosticSeverity.ERROR
    
    def test_empty_model_alias_section(self):
        """
        T1.2.4: Empty Model Alias Section
        TESTS: Handling of empty/None model_alias section
        VALIDATES: Parser gracefully handles missing section
        ENSURES: No errors for optional section
        """
        diagnostics = []
        file_path = Path("test.asdl")
        
        # Test None data
        result = self.parser.parse(None, diagnostics, file_path)
        assert result is None
        assert len(diagnostics) == 0
        
        # Test empty dict
        result = self.parser.parse({}, diagnostics, file_path)
        assert result == {}
        assert len(diagnostics) == 0