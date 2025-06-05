"""
Tests for JSON export functionality.

Tests the JSON serialization capabilities of parsed ASDL files.
"""

import pytest
import json
from asdl import ASDLParser, ASDLParseError


class TestJSONExport:
    """Test JSON export functionality for parsed ASDL files."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ASDLParser()
    
    def test_json_export(self):
        """Test JSON export functionality."""
        yaml_content = """
.version: "ASDL v1.0"
.top_module: test

models:
  nmos_unit: {model: nfet_3v3, L: 0.18u, W: 2u}

modules:
  test:
    nets: {in: in, out: out}
    parameters: {M: 2, W: "10u"}
    circuits:
      MN1:
        model: nmos_unit
        nets: {S: vss, D: out, G: in, B: VSS}
        M: "${M}"
    notes:
      layout: "test layout note"
"""
        
        asdl_file = self.parser.parse_string(yaml_content)
        
        # Test to_dict method
        data = asdl_file.to_dict()
        assert isinstance(data, dict)
        assert data['version'] == "ASDL v1.0"
        assert data['top_module'] == "test"
        assert 'modules' in data
        assert 'test' in data['modules']
        assert 'models' in data
        assert 'nmos_unit' in data['models']
        
        # Test to_json method
        json_str = asdl_file.to_json()
        assert isinstance(json_str, str)
        assert '"version": "ASDL v1.0"' in json_str
        assert '"top_module": "test"' in json_str
        
        # Test that JSON is valid by parsing it back
        parsed_json = json.loads(json_str)
        assert parsed_json['version'] == "ASDL v1.0"
        assert parsed_json['modules']['test']['parameters']['M'] == 2
        
        # Test that patterns and parameter substitutions are preserved
        circuit = parsed_json['modules']['test']['circuits']['MN1']
        assert circuit['parameters']['M'] == "${M}"  # Preserved as string 