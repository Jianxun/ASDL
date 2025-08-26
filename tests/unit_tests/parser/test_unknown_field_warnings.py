"""
Tests for P201: Unknown Field warning generation.

These tests verify that the parser generates appropriate warnings
for unknown/unrecognized fields in modules, ports, and instances.
"""

import pytest
from src.asdl.parser import ASDLParser
from src.asdl.diagnostics import DiagnosticSeverity

class TestUnknownFieldWarnings:
    """Test P201: Unknown Field warning generation."""

    def test_unknown_field_in_module(self):
        """Test that P201 is generated for unknown fields in module definitions."""
        yaml_content = """
file_info:
  top_module: "test"
modules:
  test_module:
    spice_template: "X_test test_model"
    unknown_field: "this should generate a warning"
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)

        assert asdl_file is not None
        assert len(diagnostics) == 1
        diagnostic = diagnostics[0]
        assert diagnostic.code == "P0702"
        assert diagnostic.severity == DiagnosticSeverity.WARNING
        assert "unknown_field" in diagnostic.details
        assert "not a recognized" in diagnostic.details

    def test_unknown_field_in_port(self):
        """Test that P201 is generated for unknown fields in port definitions."""
        yaml_content = """
file_info:
  top_module: "test"
modules:
  test_module:
    ports:
      test_port:
        dir: in
        type: voltage
        unknown_port_field: "this should generate a warning"
    spice_template: "X_test test_model"
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)

        assert asdl_file is not None
        assert len(diagnostics) == 1
        diagnostic = diagnostics[0]
        assert diagnostic.code == "P0702"
        assert diagnostic.severity == DiagnosticSeverity.WARNING
        assert "unknown_port_field" in diagnostic.details

    def test_unknown_field_in_instance(self):
        """Test that P201 is generated for unknown fields in instance definitions."""
        yaml_content = """
file_info:
  top_module: "test"
modules:
  test_module:
    instances:
      test_instance:
        model: "some_model"
        mappings: {}
        unknown_instance_field: "this should generate a warning"
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)

        assert asdl_file is not None
        assert len(diagnostics) == 1
        diagnostic = diagnostics[0]
        assert diagnostic.code == "P0702"
        assert diagnostic.severity == DiagnosticSeverity.WARNING
        assert "unknown_instance_field" in diagnostic.details

    def test_multiple_unknown_fields_generate_multiple_warnings(self):
        """Test that multiple unknown fields generate multiple P201 warnings."""
        yaml_content = """
file_info:
  top_module: "test"
modules:
  test_module:
    spice_template: "X_test test_model"
    unknown_field1: "warning 1"
    unknown_field2: "warning 2"
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)

        assert asdl_file is not None
        assert len(diagnostics) == 2
        codes = [d.code for d in diagnostics]
        assert all(code == "P0702" for code in codes)
        fields = [d.details for d in diagnostics]
        assert any("unknown_field1" in field for field in fields)
        assert any("unknown_field2" in field for field in fields)

    def test_no_warning_for_known_fields(self):
        """Test that no P201 warnings are generated for recognized fields."""
        yaml_content = """
file_info:
  top_module: "test"
modules:
  test_module:
    doc: "A test module"
    ports:
      in:
        dir: in
        type: voltage
        constraints: {}
        metadata: {}
    parameters: {}
    variables: {}
    spice_template: "X_test in test_model"
    pdk: "test_pdk"
    metadata: {}
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)

        assert asdl_file is not None
        assert len(diagnostics) == 0  # No warnings for known fields