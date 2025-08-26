"""
Test unified parser architecture (T0.4).

Tests the parser's ability to handle unified modules and imports section
while rejecting the legacy models section format.
"""

import pytest
from src.asdl.parser import ASDLParser
from src.asdl.data_structures import ASDLFile, Module
from src.asdl.diagnostics import DiagnosticSeverity


class TestUnifiedParsing:
    """Test parser handling of unified module architecture."""
    
    def test_models_section_rejected(self):
        """
        TESTS: Parser rejects ASDL files with models section
        VALIDATES: Clean break from legacy format
        ENSURES: No ambiguity about supported format
        """
        yaml_content = """
file_info:
  top_module: "test"
models:
  nmos_old:
    type: pdk_device
    ports: ["D", "G", "S", "B"]
    device_line: "M_nmos D G S B nfet_03v3"
modules: {}
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)
        
        # Should still parse but generate warning about unknown section
        assert asdl_file is not None
        assert len(diagnostics) == 1
        assert diagnostics[0].code == "P0701"  # Unknown top-level section
        assert diagnostics[0].title == "Unknown Top-Level Section"
        assert "'models'" in diagnostics[0].details
        assert diagnostics[0].severity == DiagnosticSeverity.WARNING
        
        # Models section should be ignored - not parsed into ASDLFile
        assert not hasattr(asdl_file, 'models') or asdl_file.modules == {}
    
    def test_unified_module_parsing(self):
        """
        TESTS: Single parsing path for all module types
        VALIDATES: Simplified parser logic without type-specific branches
        ENSURES: Consistent parsing behavior regardless of module type
        """
        yaml_content = """
file_info:
  top_module: "test_circuit"
modules:
  # Primitive module
  nfet_03v3:
    ports:
      D: {dir: in_out, type: voltage}
      G: {dir: in, type: voltage}
      S: {dir: in_out, type: voltage}
      B: {dir: in_out, type: voltage}
    parameters: {L: "0.28u", W: "3u", M: 1}
    spice_template: "MN {D} {G} {S} {B} nfet_03v3 L={L} W={W} m={M}"
    pdk: "gf180mcu"
    
  # Hierarchical module
  inverter:
    ports:
      in: {dir: in, type: voltage}
      out: {dir: out, type: voltage}
      vdd: {dir: in, type: voltage}
      vss: {dir: in, type: voltage}
    instances:
      M1:
        model: nfet_03v3
        mappings: {D: out, G: in, S: vss, B: vss}
        parameters: {M: 1}
      M2:
        model: nfet_03v3  # Would normally be pfet, but using nfet for simplicity
        mappings: {D: out, G: in, S: vdd, B: vdd}
        parameters: {M: 2}
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)
        
        assert asdl_file is not None
        assert not diagnostics
        
        # Verify primitive module
        nfet = asdl_file.modules["nfet_03v3"]
        assert nfet.spice_template is not None
        assert nfet.instances is None
        assert nfet.pdk == "gf180mcu"
        assert "MN {D} {G} {S} {B}" in nfet.spice_template
        
        # Verify hierarchical module
        inverter = asdl_file.modules["inverter"]
        assert inverter.instances is not None
        assert inverter.spice_template is None
        assert inverter.pdk is None
        assert "M1" in inverter.instances
        assert "M2" in inverter.instances
    
    def test_parser_enforces_mutual_exclusion(self):
        """
        TESTS: Parser validates spice_template XOR instances constraint
        VALIDATES: Early error detection for malformed modules
        ENSURES: Clear diagnostic messages for constraint violations
        """
        yaml_content = """
file_info:
  top_module: "test"
modules:
  invalid_module:
    ports:
      in: {dir: in, type: voltage}
      out: {dir: out, type: voltage}
    spice_template: "X{name} {in} {out} invalid_device"
    instances:
      M1:
        model: some_model
        mappings: {in: in, out: out}
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)
        
        # Should fail to parse the invalid module
        assert len(diagnostics) == 1
        assert diagnostics[0].code == "P107"  # Module Type Conflict
        assert diagnostics[0].title == "Module Type Conflict"
        assert "cannot have both" in diagnostics[0].details
        assert "spice_template" in diagnostics[0].details
        assert "instances" in diagnostics[0].details
        assert diagnostics[0].severity == DiagnosticSeverity.ERROR
        
        # Module should not be in parsed result
        assert asdl_file is not None
        assert "invalid_module" not in asdl_file.modules
    
    def test_parser_requires_implementation(self):
        """
        TESTS: Parser rejects modules with neither spice_template nor instances
        VALIDATES: All modules must have valid implementation
        ENSURES: Clear error for incomplete module definitions
        """
        yaml_content = """
file_info:
  top_module: "test"
modules:
  empty_module:
    ports:
      in: {dir: in, type: voltage}
      out: {dir: out, type: voltage}
    parameters: {gain: 1.0}
    # Missing both spice_template and instances
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)
        
        # Should fail to parse the empty module
        assert len(diagnostics) == 1
        assert diagnostics[0].code == "P108"  # Incomplete Module Definition
        assert diagnostics[0].title == "Incomplete Module Definition"
        assert "must have either" in diagnostics[0].details
        assert "spice_template" in diagnostics[0].details
        assert "instances" in diagnostics[0].details
        assert diagnostics[0].severity == DiagnosticSeverity.ERROR
        
        # Module should not be in parsed result
        assert asdl_file is not None
        assert "empty_module" not in asdl_file.modules
    
    def test_imports_section_parsing(self):
        """
        TESTS: Basic imports section recognition and parsing
        VALIDATES: Foundation for import system syntax
        ENSURES: Proper data structure population for import resolution
        """
        yaml_content = """
file_info:
  top_module: "test_design"
imports:
  pdk_primitives: libs/pdk/primitives.asdl
  std_devices: libs/tiles/devices.asdl
  amplifiers: libs/analog/amps.asdl
modules:
  test_circuit:
    instances:
      M1:
        model: pdk_primitives.nfet_03v3
        mappings: {D: out, G: in, S: gnd, B: gnd}
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)
        
        assert asdl_file is not None
        assert not diagnostics
        
        # Verify imports parsing
        assert asdl_file.imports is not None
        assert len(asdl_file.imports) == 3
        assert asdl_file.imports["pdk_primitives"] == "libs/pdk/primitives.asdl"
        assert asdl_file.imports["std_devices"] == "libs/tiles/devices.asdl"
        assert asdl_file.imports["amplifiers"] == "libs/analog/amps.asdl"
    
    def test_invalid_import_entries(self):
        """
        TESTS: Parser validates import format and generates errors for invalid syntax
        VALIDATES: Early detection of malformed import declarations
        ENSURES: Clear diagnostic messages for import format violations
        """
        yaml_content = """
file_info:
  top_module: "test"
imports:
  valid_import: lib/valid.asdl
  invalid_import: 42
  another_invalid: lib/invalid.txt
modules: {}
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)
        
        assert asdl_file is not None
        
        # Should have 2 import errors: P0501 (type) and P0502 (extension)
        p0501 = [d for d in diagnostics if d.code == "P0501"]
        p0502 = [d for d in diagnostics if d.code == "P0502"]
        assert len(p0501) == 1
        assert len(p0502) == 1
        assert all(d.severity == DiagnosticSeverity.ERROR for d in (p0501 + p0502))
        
        # Valid import should still be parsed
        assert asdl_file.imports is not None
        assert "valid_import" in asdl_file.imports
        assert "invalid_import" not in asdl_file.imports
        assert "another_invalid" not in asdl_file.imports
    
    def test_empty_imports_section(self):
        """
        TESTS: Parser handles empty imports section gracefully
        VALIDATES: Optional imports section behavior
        ENSURES: No imports is valid state
        """
        yaml_content = """
file_info:
  top_module: "simple_module"
modules:
  local_module:
    spice_template: "R{name} {n1} {n2} {R}"
    parameters: {R: "1k"}
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)
        
        assert asdl_file is not None
        assert not diagnostics
        assert asdl_file.imports is None  # No imports section
        assert len(asdl_file.modules) == 1
    
    def test_unified_parser_preserves_location_info(self):
        """
        TESTS: Location tracking works with unified parsing architecture
        VALIDATES: Diagnostics can point to specific locations in modules and imports
        ENSURES: Error messages are helpful for debugging
        """
        yaml_content = """
file_info:
  top_module: "test"
imports:
  test_lib: libs/valid.asdl
modules:
  test_module:
    spice_template: "R{name} {n1} {n2} {R}"
    parameters: {R: "1k"}
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)
        
        assert asdl_file is not None
        assert not diagnostics
        
        # Check that module location info is preserved
        module = asdl_file.modules["test_module"]
        assert module.start_line is not None
        assert module.start_col is not None