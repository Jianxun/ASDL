"""
Test DeviceModel parsing functionality.

Tests the models section parsing including:
- Device model definitions
- Device type validation and extensibility
- Port and parameter parsing
- Unknown field handling
- Model alias handling
"""

import pytest
from pathlib import Path
import sys

# Add src to path for testing
test_dir = Path(__file__).parent
project_root = test_dir.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from asdl.parser import ASDLParser
from asdl.data_structures import ASDLFile, DeviceModel, DeviceType


class TestModelsParsing:
    """Test DeviceModel section parsing."""
    
    def test_parse_basic_nmos_model(self):
        """Test parsing a basic NMOS device model."""
        yaml_content = """
file_info:
  top_module: "test"
  doc: ""
  revision: ""
  author: ""
  date: ""

models:
  nch:
    model: "nch_lvt"
    type: "nmos"
    ports: ["G", "D", "S", "B"]
    params:
      W: "1u"
      L: "0.1u"
      M: 1
    description: "Low-Vt NMOS transistor"

modules: {}
"""
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)
        
        assert len(asdl_file.models) == 1
        assert "nch" in asdl_file.models
        
        nch_model = asdl_file.models["nch"]
        assert isinstance(nch_model, DeviceModel)
        assert nch_model.model == "nch_lvt"
        assert nch_model.type == DeviceType.NMOS
        assert nch_model.ports == ["G", "D", "S", "B"]
        assert nch_model.params == {"W": "1u", "L": "0.1u", "M": 1}
        assert nch_model.description == "Low-Vt NMOS transistor"
    
    def test_parse_multiple_models(self):
        """Test parsing multiple device models."""
        yaml_content = """
file_info:
  top_module: "test"
  doc: ""
  revision: ""
  author: ""
  date: ""

models:
  nch:
    model: "nch_lvt"
    type: "nmos"
    ports: ["G", "D", "S", "B"]
    params: {W: "1u", L: "0.1u"}
  
  pch:
    model: "pch_lvt"
    type: "pmos"
    ports: ["G", "D", "S", "B"]
    params: {W: "2u", L: "0.1u"}
  
  res:
    model: "res_poly"
    type: "resistor"
    ports: ["A", "B"]
    params: {R: "1k"}

modules: {}
"""
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)
        
        assert len(asdl_file.models) == 3
        assert "nch" in asdl_file.models
        assert "pch" in asdl_file.models
        assert "res" in asdl_file.models
        
        # Check each model
        nch = asdl_file.models["nch"]
        assert nch.type == DeviceType.NMOS
        assert nch.model == "nch_lvt"
        
        pch = asdl_file.models["pch"]
        assert pch.type == DeviceType.PMOS
        assert pch.model == "pch_lvt"
        
        res = asdl_file.models["res"]
        assert res.type == DeviceType.RESISTOR
        assert res.model == "res_poly"
    
    def test_parse_model_minimal_fields(self):
        """Test parsing model with minimal required fields."""
        yaml_content = """
file_info:
  top_module: "test"
  doc: ""
  revision: ""
  author: ""
  date: ""

models:
  minimal:
    model: "minimal_device"
    type: "nmos"

modules: {}
"""
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)
        
        minimal_model = asdl_file.models["minimal"]
        assert minimal_model.model == "minimal_device"
        assert minimal_model.type == DeviceType.NMOS
        assert minimal_model.ports == []  # Default empty list
        assert minimal_model.params is None  # Default None
        assert minimal_model.description is None  # Default None
    
    def test_parse_all_device_types(self):
        """Test parsing all supported device types."""
        yaml_content = """
file_info:
  top_module: "test"
  doc: ""
  revision: ""
  author: ""
  date: ""

models:
  nmos_dev:
    model: "nch"
    type: "nmos"
  
  pmos_dev:
    model: "pch"
    type: "pmos"
  
  resistor_dev:
    model: "res"
    type: "resistor"
  
  capacitor_dev:
    model: "cap"
    type: "capacitor"
  
  diode_dev:
    model: "diode"
    type: "diode"
  
  amplifier_dev:
    model: "opamp"
    type: "amplifier"

modules: {}
"""
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)
        
        expected_types = {
            "nmos_dev": DeviceType.NMOS,
            "pmos_dev": DeviceType.PMOS,
            "resistor_dev": DeviceType.RESISTOR,
            "capacitor_dev": DeviceType.CAPACITOR,
            "diode_dev": DeviceType.DIODE,
            "amplifier_dev": DeviceType.AMPLIFIER,
        }
        
        for alias, expected_type in expected_types.items():
            assert asdl_file.models[alias].type == expected_type
    
    def test_parse_unknown_device_type(self):
        """Test parsing with unknown device type (future extensibility)."""
        yaml_content = """
file_info:
  top_module: "test"
  doc: ""
  revision: ""
  author: ""
  date: ""

models:
  future_device:
    model: "quantum_device"
    type: "quantum_dot"

modules: {}
"""
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)
        
        future_model = asdl_file.models["future_device"]
        assert future_model.model == "quantum_device"
        # Should create a pseudo-enum member for unknown type
        assert future_model.type.value == "quantum_dot"
        assert "UNKNOWN_QUANTUM_DOT" in str(future_model.type.name)
    
    def test_model_not_dictionary(self):
        """Test error handling when model definition is not a dictionary."""
        yaml_content = """
file_info:
  top_module: "test"
  doc: ""
  revision: ""
  author: ""
  date: ""

models:
  bad_model: "not a dictionary"

modules: {}
"""
        parser = ASDLParser()
        
        with pytest.raises(ValueError, match="Model 'bad_model' must be a dictionary"):
            parser.parse_string(yaml_content)
    
    def test_models_unknown_fields_lenient(self):
        """Test unknown fields handling in model definitions (lenient mode)."""
        yaml_content = """
file_info:
  top_module: "test"
  doc: ""
  revision: ""
  author: ""
  date: ""

models:
  extended_model:
    model: "nch_extended"
    type: "nmos"
    ports: ["G", "D", "S", "B"]
    params: {W: "1u", L: "0.1u"}
    description: "Extended NMOS"
    # Unknown fields
    spice_lib: "/path/to/lib"
    corner_models: ["tt", "ss", "ff"]
    layout_rules: {min_width: "0.5u"}

modules: {}
"""
        parser = ASDLParser(strict_mode=False)
        
        with pytest.warns(UserWarning, match="Unknown fields in model 'extended_model'"):
            asdl_file = parser.parse_string(yaml_content)
        
        # Should still parse successfully
        model = asdl_file.models["extended_model"]
        assert model.model == "nch_extended"
        assert model.type == DeviceType.NMOS
        assert model.description == "Extended NMOS"
    
    def test_models_unknown_fields_strict(self):
        """Test unknown fields handling in model definitions (strict mode)."""
        yaml_content = """
file_info:
  top_module: "test"
  doc: ""
  revision: ""
  author: ""
  date: ""

models:
  strict_model:
    model: "nch"
    type: "nmos"
    unknown_field: "should cause error"

modules: {}
"""
        parser = ASDLParser(strict_mode=True)
        
        with pytest.raises(ValueError, match="Unknown fields in model 'strict_model'"):
            parser.parse_string(yaml_content)
    
    def test_empty_models_section(self):
        """Test parsing with empty models section."""
        yaml_content = """
file_info:
  top_module: "test"
  doc: ""
  revision: ""
  author: ""
  date: ""

models: {}

modules: {}
"""
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)
        
        assert isinstance(asdl_file.models, dict)
        assert len(asdl_file.models) == 0
    
    def test_complex_model_parameters(self):
        """Test parsing models with complex parameter structures."""
        yaml_content = """
file_info:
  top_module: "test"
  doc: ""
  revision: ""
  author: ""
  date: ""

models:
  complex_model:
    model: "advanced_transistor"
    type: "nmos"
    ports: ["G", "D", "S", "B", "NG"]
    params:
      # Basic parameters
      W: "10u"
      L: "0.1u"
      M: 4
      # Complex parameters
      bias_conditions:
        VGS: "0.8V"
        VDS: "1.2V"
      corner_params:
        - {corner: "tt", W: "10u", L: "0.1u"}
        - {corner: "ss", W: "11u", L: "0.11u"}
      temperature_coeffs: [1.0, 0.001, 0.0001]
    description: "Advanced transistor with complex parameters"

modules: {}
"""
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)
        
        model = asdl_file.models["complex_model"]
        assert model.model == "advanced_transistor"
        assert model.ports == ["G", "D", "S", "B", "NG"]
        
        # Check complex parameters are preserved
        params = model.params
        assert params["W"] == "10u"
        assert params["M"] == 4
        assert "bias_conditions" in params
        assert params["bias_conditions"]["VGS"] == "0.8V"
        assert "corner_params" in params
        assert len(params["corner_params"]) == 2
        assert "temperature_coeffs" in params 