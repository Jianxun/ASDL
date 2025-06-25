"""
Test validation of unused modules and models.

These tests ensure that modules and models declared but not instantiated
trigger warnings but don't break netlisting.
"""

import pytest
import warnings
from src.asdl.parser import ASDLParser
from src.asdl.generator import SPICEGenerator


class TestUnusedValidation:
    """Test validation of unused modules and models."""
    
    def test_unused_model_warning(self):
        """Test that unused models trigger warnings but don't break netlisting."""
        yaml_content = """
file_info:
  top_module: "test_module"
  doc: "Test unused model validation"
  revision: "v0.1"
  author: "Test"
  date: "2025-01-01"

models:
  used_model:
    doc: "This model is used"
    type: nmos
    ports: [G, D, S, B]
    device_line: |
      MN {D} {G} {S} {B} nfet_03v3 W=1u L=0.1u
    parameters:
      M: 1
      
  unused_model:
    doc: "This model is NOT used"
    type: pmos
    ports: [G, D, S, B]
    device_line: |
      MP {D} {G} {S} {B} pfet_03v3 W=2u L=0.1u
    parameters:
      M: 1

modules:
  test_module:
    doc: "Module that only uses some models"
    ports:
      in: {dir: in, type: voltage}
      out: {dir: out, type: voltage}
      vss: {dir: in_out, type: voltage}
      vdd: {dir: in_out, type: voltage}
    instances:
      M1:
        model: used_model
        mappings: {G: in, D: out, S: vss, B: vss}
        parameters: {M: 2}
"""
        
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)
        
        generator = SPICEGenerator()
        
        # Should generate warnings for unused model
        with pytest.warns(UserWarning, match="Model 'unused_model' is declared but never instantiated"):
            spice_output = generator.generate(asdl_file)
        
        # Should still generate valid SPICE
        assert ".subckt used_model" in spice_output
        assert ".subckt unused_model" in spice_output  # Still generates definitions
        assert "X_M1" in spice_output
        assert ".end" in spice_output
    
    def test_unused_module_warning(self):
        """Test that unused modules trigger warnings but don't break netlisting."""
        yaml_content = """
file_info:
  top_module: "main_module"
  doc: "Test unused module validation"
  revision: "v0.1"
  author: "Test"
  date: "2025-01-01"

models:
  basic_nmos:
    doc: "Basic NMOS"
    type: nmos
    ports: [G, D, S, B]
    device_line: |
      MN {D} {G} {S} {B} nfet_03v3 W=1u L=0.1u
    parameters:
      M: 1

modules:
  used_module:
    doc: "This module is used"
    ports:
      in: {dir: in, type: voltage}
      out: {dir: out, type: voltage}
      vss: {dir: in_out, type: voltage}
    instances:
      M1:
        model: basic_nmos
        mappings: {G: in, D: out, S: vss, B: vss}
        
  unused_module:
    doc: "This module is NOT used"
    ports:
      a: {dir: in, type: voltage}
      b: {dir: out, type: voltage}
    instances:
      M2:
        model: basic_nmos
        mappings: {G: a, D: b, S: vss, B: vss}
        
  main_module:
    doc: "Main module that only uses some sub-modules"
    ports:
      in: {dir: in, type: voltage}
      out: {dir: out, type: voltage}
      vss: {dir: in_out, type: voltage}
    instances:
      SUB1:
        model: used_module
        mappings: {in: in, out: out, vss: vss}
"""
        
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)
        
        generator = SPICEGenerator()
        
        # Should generate warnings for unused module
        with pytest.warns(UserWarning, match="Module 'unused_module' is declared but never instantiated"):
            spice_output = generator.generate(asdl_file)
        
        # Should still generate valid SPICE
        assert ".subckt used_module" in spice_output
        assert ".subckt unused_module" in spice_output  # Still generates definitions
        assert "X_SUB1" in spice_output
        assert ".end" in spice_output
    
    def test_multiple_unused_warnings(self):
        """Test multiple unused models and modules trigger multiple warnings."""
        yaml_content = """
file_info:
  top_module: "simple_module"
  doc: "Test multiple unused items"
  revision: "v0.1"
  author: "Test"
  date: "2025-01-01"

models:
  used_model:
    doc: "Used model"
    type: nmos
    ports: [G, D, S, B]
    device_line: |
      MN {D} {G} {S} {B} nfet_03v3 W=1u L=0.1u
    parameters:
      M: 1
      
  unused_model_1:
    doc: "Unused model 1"
    type: pmos
    ports: [G, D, S, B]
    device_line: |
      MP {D} {G} {S} {B} pfet_03v3 W=2u L=0.1u
    parameters:
      M: 1
      
  unused_model_2:
    doc: "Unused model 2"
    type: resistor
    ports: [plus, minus]
    device_line: |
      R1 {plus} {minus} R=1k

modules:
  used_module:
    doc: "Used module"
    ports:
      in: {dir: in, type: voltage}
      out: {dir: out, type: voltage}
      vss: {dir: in_out, type: voltage}
    instances:
      M1:
        model: used_model
        mappings: {G: in, D: out, S: vss, B: vss}
        
  unused_module_1:
    doc: "Unused module 1"
    ports:
      a: {dir: in, type: voltage}
      b: {dir: out, type: voltage}
      
  unused_module_2:
    doc: "Unused module 2"
    ports:
      x: {dir: in, type: voltage}
      y: {dir: out, type: voltage}
        
  simple_module:
    doc: "Simple module"
    ports:
      in: {dir: in, type: voltage}
      out: {dir: out, type: voltage}
      vss: {dir: in_out, type: voltage}
    instances:
      SUB1:
        model: used_module
        mappings: {in: in, out: out, vss: vss}
"""
        
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)
        
        generator = SPICEGenerator()
        
        # Capture all warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            spice_output = generator.generate(asdl_file)
            
            # Should have 4 warnings: 2 unused models + 2 unused modules
            warning_messages = [str(warning.message) for warning in w]
            
            # Check for unused models
            assert any("unused_model_1" in msg and "never instantiated" in msg for msg in warning_messages)
            assert any("unused_model_2" in msg and "never instantiated" in msg for msg in warning_messages)
            
            # Check for unused modules
            assert any("unused_module_1" in msg and "never instantiated" in msg for msg in warning_messages)
            assert any("unused_module_2" in msg and "never instantiated" in msg for msg in warning_messages)
        
        # Should still generate valid SPICE
        assert ".end" in spice_output
    
    def test_all_models_used_no_warnings(self):
        """Test that no warnings are generated when all models and modules are used."""
        yaml_content = """
file_info:
  top_module: "complete_module"
  doc: "Test no unused items"
  revision: "v0.1"
  author: "Test"
  date: "2025-01-01"

models:
  nmos_model:
    doc: "NMOS model"
    type: nmos
    ports: [G, D, S, B]
    device_line: |
      MN {D} {G} {S} {B} nfet_03v3 W=1u L=0.1u
    parameters:
      M: 1
      
  pmos_model:
    doc: "PMOS model"
    type: pmos
    ports: [G, D, S, B]
    device_line: |
      MP {D} {G} {S} {B} pfet_03v3 W=2u L=0.1u
    parameters:
      M: 1

modules:
  sub_module:
    doc: "Sub module"
    ports:
      in: {dir: in, type: voltage}
      out: {dir: out, type: voltage}
      vss: {dir: in_out, type: voltage}
      vdd: {dir: in_out, type: voltage}
    instances:
      MN1:
        model: nmos_model
        mappings: {G: in, D: out, S: vss, B: vss}
      MP1:
        model: pmos_model
        mappings: {G: in, D: out, S: vdd, B: vdd}
        
  complete_module:
    doc: "Complete module using everything"
    ports:
      in: {dir: in, type: voltage}
      out: {dir: out, type: voltage}
      vss: {dir: in_out, type: voltage}
      vdd: {dir: in_out, type: voltage}
    instances:
      SUB1:
        model: sub_module
        mappings: {in: in, out: out, vss: vss, vdd: vdd}
"""
        
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)
        
        generator = SPICEGenerator()
        
        # Should NOT generate any warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            spice_output = generator.generate(asdl_file)
            
            # Filter for unused component warnings only
            unused_warnings = [warning for warning in w 
                             if "never instantiated" in str(warning.message)]
            assert len(unused_warnings) == 0
        
        # Should generate valid SPICE
        assert ".end" in spice_output
    
    def test_recursive_module_usage_tracking(self):
        """Test that module usage is tracked recursively through the hierarchy."""
        yaml_content = """
file_info:
  top_module: "top_level"
  doc: "Test recursive usage tracking"
  revision: "v0.1"
  author: "Test"
  date: "2025-01-01"

models:
  basic_device:
    doc: "Basic device"
    type: nmos
    ports: [G, D, S, B]
    device_line: |
      MN {D} {G} {S} {B} nfet_03v3 W=1u L=0.1u
    parameters:
      M: 1

modules:
  leaf_module:
    doc: "Leaf module"
    ports:
      in: {dir: in, type: voltage}
      out: {dir: out, type: voltage}
      vss: {dir: in_out, type: voltage}
    instances:
      DEV1:
        model: basic_device
        mappings: {G: in, D: out, S: vss, B: vss}
        
  intermediate_module:
    doc: "Intermediate module"
    ports:
      in: {dir: in, type: voltage}
      out: {dir: out, type: voltage}
      vss: {dir: in_out, type: voltage}
    instances:
      LEAF1:
        model: leaf_module
        mappings: {in: in, out: out, vss: vss}
        
  unused_intermediate:
    doc: "Unused intermediate module"
    ports:
      a: {dir: in, type: voltage}
      b: {dir: out, type: voltage}
    instances:
      UNUSED_LEAF:
        model: leaf_module  # This should still count as leaf_module being used
        mappings: {in: a, out: b, vss: vss}
        
  top_level:
    doc: "Top level module"
    ports:
      in: {dir: in, type: voltage}
      out: {dir: out, type: voltage}
      vss: {dir: in_out, type: voltage}
    instances:
      INTER1:
        model: intermediate_module
        mappings: {in: in, out: out, vss: vss}
"""
        
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)
        
        generator = SPICEGenerator()
        
        # Should only warn about unused_intermediate, not leaf_module or basic_device
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            spice_output = generator.generate(asdl_file)
            
            # Filter for unused component warnings only
            unused_warnings = [str(warning.message) for warning in w 
                             if "never instantiated" in str(warning.message)]
            
            # Should only have one warning for unused_intermediate
            assert len(unused_warnings) == 1
            assert "unused_intermediate" in unused_warnings[0]
        
        # Should generate valid SPICE
        assert ".end" in spice_output
    
    def test_no_false_positives_for_components_in_unused_modules(self):
        """
        Test that components used within unused modules don't trigger false positive warnings.
        
        This is a regression test for the issue where 'jumper' was flagged as unused
        even though it was used within 'bias_gen', just because 'bias_gen' itself
        was unused.
        """
        yaml_content = """
file_info:
  top_module: "main_circuit"
  doc: "Test no false positives for components in unused modules"
  revision: "v0.1"
  author: "Test"
  date: "2025-01-01"

models:
  jumper:
    doc: "Small resistor net jumper"
    type: resistor
    ports: [plus, minus]
    device_line: |
      R1 {plus} {minus} R=100m

  nmos_unit:
    doc: "NMOS transistor"
    type: nmos
    ports: [G, D, S, B]
    device_line: |
      MN {D} {G} {S} {B} nfet_03v3 L=0.5u W=4u
    parameters:
      M: 1

modules:
  bias_gen:
    doc: "Bias generator - this module is unused"
    ports:
      ibias: {dir: in, type: current}
      vbn: {dir: out, type: voltage}
      vss: {dir: in_out, type: voltage}
      vdd: {dir: in_out, type: voltage}
    instances:
      MN_BIAS:
        model: nmos_unit
        mappings: {G: vbn, D: vbn, S: vss, B: vss}
        parameters: {M: 1}
      J1:
        model: jumper  # jumper is USED here, within bias_gen
        mappings: {plus: ibias, minus: vbn}
        
  main_circuit:
    doc: "Main circuit that doesn't use bias_gen"
    ports:
      in: {dir: in, type: voltage}
      out: {dir: out, type: voltage}
      vss: {dir: in_out, type: voltage}
    instances:
      MN1:
        model: nmos_unit
        mappings: {G: in, D: out, S: vss, B: vss}
"""
        
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)
        
        generator = SPICEGenerator()
        
        # Capture warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            spice_output = generator.generate(asdl_file)
            
            # Filter for unused component warnings only
            unused_warnings = [str(warning.message) for warning in w 
                             if "never instantiated" in str(warning.message)]
            
            # Should only warn about bias_gen (the unused module)
            # Should NOT warn about jumper or nmos_unit (both are instantiated somewhere)
            assert len(unused_warnings) == 1
            assert "bias_gen" in unused_warnings[0]
            
            # Verify no false positives
            assert not any("jumper" in msg for msg in unused_warnings)
            assert not any("nmos_unit" in msg for msg in unused_warnings)
        
        # Should still generate valid SPICE
        assert ".end" in spice_output 