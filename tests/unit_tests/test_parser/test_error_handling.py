"""
Tests for error handling in ASDL parsing.

Tests various error conditions and invalid inputs to ensure proper error reporting.
"""

import pytest
from asdl import ASDLParser, ASDLParseError


class TestErrorHandling:
    """Test error handling for invalid ASDL input."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ASDLParser()
    
    def test_parse_invalid_yaml(self):
        """Test error handling for invalid YAML."""
        invalid_yaml = """
modules:
  test:
    circuits:
      MN1: {model: nmos_unit
        # Missing closing brace
"""
        
        with pytest.raises(ASDLParseError, match="YAML parsing error"):
            self.parser.parse_string(invalid_yaml)
    
    def test_parse_circuits_list_format_error(self):
        """Test error handling for circuits in list format (no longer supported)."""
        yaml_content = """
modules:
  test:
    circuits:
      - {name: MN1, model: nmos_unit}
"""
        
        with pytest.raises(ASDLParseError, match="'circuits' must be a dictionary"):
            self.parser.parse_string(yaml_content)
    
    def test_parse_duplicate_circuit_names(self):
        """Test error handling for duplicate circuit names."""
        yaml_content = """
models:
  nmos_unit: {model: nfet_3v3, L: 0.18u, W: 2u}

modules:
  test:
    circuits:
      circuit1:
        name: MN1
        model: nmos_unit
      circuit2:
        name: MN1  # Duplicate name
        model: nmos_unit
"""
        
        with pytest.raises(ASDLParseError, match="Duplicate circuit name: 'MN1'"):
            self.parser.parse_string(yaml_content)
    
    def test_parse_invalid_structure(self):
        """Test error handling for invalid ASDL structure."""
        # Not a dictionary
        with pytest.raises(ASDLParseError, match="must be a YAML dictionary"):
            self.parser.parse_string("- not a dict")
        
        # Invalid modules section
        invalid_modules = """
modules: "not a dict"
"""
        with pytest.raises(ASDLParseError, match="'modules' must be a dictionary"):
            self.parser.parse_string(invalid_modules) 