"""
Test unified parser architecture (T0.4).

Tests the parser's ability to handle unified modules and imports section
while rejecting the legacy models section format.
"""

import pytest
from src.asdl.parser import ASDLParser
from src.asdl.data_structures import ASDLFile, Module


class TestUnifiedParsing:
    """Test parser handling of unified module architecture."""
    
    # P0701 covered in per-code test file
    
    def test_unified_module_parsing(self):
        """
        TESTS: Basic module parsing with both primitive and hierarchical modules
        VALIDATES: Core parser functionality for all module types
        ENSURES: Proper data structure population and validation
        """
        yaml_content = """
file_info:
  top_module: "test_design"
modules:
  # Primitive module
  nfet_03v3:
    ports:
      D: {dir: in_out, type: signal}
      G: {dir: in_out, type: signal}
      S: {dir: in_out, type: signal}
      B: {dir: in_out, type: signal}
    parameters: {L: "0.28u", W: "3u", M: 1}
    spice_template: "MN {D} {G} {S} {B} nfet_03v3 L={L} W={W} m={M}"
    pdk: "gf180mcu"
    
  # Hierarchical module
  inverter:
    ports:
      in: {dir: in, type: signal}
      out: {dir: out, type: signal}
      vdd: {dir: in, type: signal}
      vss: {dir: in, type: signal}
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
    
    # Location-tracking assertions are centralized in test_location_tracking.py