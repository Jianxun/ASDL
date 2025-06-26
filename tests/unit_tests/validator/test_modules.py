"""
Test Module parsing functionality.

Tests the modules section parsing including:
- Module definitions with ports, instances, nets
- Port parsing with direction and signal types
- Instance parsing with mappings and parameters
- Nets parsing and handling
- Module parameters and documentation
- Unknown field handling and future-proofing
"""

import pytest
from pathlib import Path
import sys

# Add src to path for testing
test_dir = Path(__file__).parent
project_root = test_dir.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from asdl.parser import ASDLParser
from asdl.data_structures import (
    ASDLFile, Module, Port, PortDirection, SignalType, 
    Instance, Nets, PortConstraints
)


class TestModulesParsing:
    """Test Module section parsing."""
    
    def test_parse_basic_module(self):
        """Test parsing a basic module with ports and instances."""
        yaml_content = """
file_info:
  top_module: "inverter"
  doc: ""
  revision: ""
  author: ""
  date: ""

models:
  nch:
    model: "nch_lvt"
    type: "nmos"
    ports: ["G", "D", "S", "B"]

modules:
  inverter:
    doc: "Basic CMOS inverter"
    ports:
      in:
        dir: "in"
        type: "voltage"
      out:
        dir: "out"
        type: "voltage"
      vdd:
        dir: "in"
        type: "voltage"
      vss:
        dir: "in"
        type: "voltage"
    instances:
      MN1:
        model: "nch"
        mappings:
          G: "in"
          D: "out"
          S: "vss"
          B: "vss"
        parameters:
          W: "1u"
          L: "0.1u"
"""
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)
        
        assert len(asdl_file.modules) == 1
        assert "inverter" in asdl_file.modules
        
        inverter = asdl_file.modules["inverter"]
        assert isinstance(inverter, Module)
        assert inverter.doc == "Basic CMOS inverter"
        
        # Check ports
        assert len(inverter.ports) == 4
        assert "in" in inverter.ports
        assert "out" in inverter.ports
        
        in_port = inverter.ports["in"]
        assert in_port.dir == PortDirection.IN
        assert in_port.type == SignalType.VOLTAGE
        
        out_port = inverter.ports["out"]
        assert out_port.dir == PortDirection.OUT
        assert out_port.type == SignalType.VOLTAGE
        
        # Check instances
        assert len(inverter.instances) == 1
        assert "MN1" in inverter.instances
        
        mn1 = inverter.instances["MN1"]
        assert mn1.model == "nch"
        assert mn1.mappings == {"G": "in", "D": "out", "S": "vss", "B": "vss"}
        assert mn1.parameters == {"W": "1u", "L": "0.1u"}
    
    def test_parse_module_minimal(self):
        """Test parsing module with minimal fields."""
        yaml_content = """
file_info:
  top_module: "minimal"
  doc: ""
  revision: ""
  author: ""
  date: ""

models: {}

modules:
  minimal: {}
"""
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)
        
        minimal = asdl_file.modules["minimal"]
        assert minimal.doc is None
        assert minimal.ports is None
        assert minimal.nets is None
        assert minimal.parameters is None
        assert minimal.instances is None
    
    def test_parse_all_port_directions(self):
        """Test parsing ports with all supported directions."""
        yaml_content = """
file_info:
  top_module: "test"
  doc: ""
  revision: ""
  author: ""
  date: ""

models: {}

modules:
  test_ports:
    ports:
      input_port:
        dir: "in"
        type: "voltage"
      output_port:
        dir: "out"
        type: "voltage"
      inout_port:
        dir: "in_out"
        type: "voltage"
"""
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)
        
        ports = asdl_file.modules["test_ports"].ports
        assert ports["input_port"].dir == PortDirection.IN
        assert ports["output_port"].dir == PortDirection.OUT
        assert ports["inout_port"].dir == PortDirection.IN_OUT
    
    def test_parse_all_signal_types(self):
        """Test parsing ports with all supported signal types."""
        yaml_content = """
file_info:
  top_module: "test"
  doc: ""
  revision: ""
  author: ""
  date: ""

models: {}

modules:
  test_signals:
    ports:
      voltage_port:
        dir: "in"
        type: "voltage"
      current_port:
        dir: "in"
        type: "current"
      digital_port:
        dir: "in"
        type: "digital"
"""
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)
        
        ports = asdl_file.modules["test_signals"].ports
        assert ports["voltage_port"].type == SignalType.VOLTAGE
        assert ports["current_port"].type == SignalType.CURRENT
        assert ports["digital_port"].type == SignalType.DIGITAL
    
    def test_parse_port_with_constraints(self):
        """Test parsing ports with constraint specifications."""
        yaml_content = """
file_info:
  top_module: "test"
  doc: ""
  revision: ""
  author: ""
  date: ""

models: {}

modules:
  constrained_module:
    ports:
      constrained_port:
        dir: "in"
        type: "voltage"
        constraints:
          min_voltage: "0V"
          max_voltage: "3.3V"
          impedance: "50Ω"
"""
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)
        
        port = asdl_file.modules["constrained_module"].ports["constrained_port"]
        assert port.constraints is not None
        assert isinstance(port.constraints, PortConstraints)
        
        # Check that constraint data is preserved
        constraints = port.constraints.constraints
        assert constraints["min_voltage"] == "0V"
        assert constraints["max_voltage"] == "3.3V"
        assert constraints["impedance"] == "50Ω"
    
    def test_parse_nets_internal(self):
        """Test parsing nets with internal net declarations."""
        yaml_content = """
file_info:
  top_module: "test"
  doc: ""
  revision: ""
  author: ""
  date: ""

models: {}

modules:
  with_nets:
    ports:
      in: {dir: "in", type: "voltage"}
      out: {dir: "out", type: "voltage"}
    nets:
      internal:
        - "internal_node1"
        - "internal_node2"
        - "bias_net"
"""
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)
        
        module = asdl_file.modules["with_nets"]
        assert module.nets is not None
        assert isinstance(module.nets, Nets)
        assert module.nets.internal == ["internal_node1", "internal_node2", "bias_net"]
        
        # Test the get_all_nets method
        port_names = list(module.ports.keys())
        all_nets = module.nets.get_all_nets(port_names)
        expected_nets = ["in", "out", "internal_node1", "internal_node2", "bias_net"]
        assert set(all_nets) == set(expected_nets)
    
    def test_parse_module_parameters(self):
        """Test parsing modules with parameters."""
        yaml_content = """
file_info:
  top_module: "test"
  doc: ""
  revision: ""
  author: ""
  date: ""

models: {}

modules:
  parameterized:
    parameters:
      W_N: "1u"
      W_P: "2u"
      L: "0.1u"
      M: 1
      bias_current: "10uA"
      complex_param:
        sub_param1: "value1"
        sub_param2: [1, 2, 3]
"""
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)
        
        module = asdl_file.modules["parameterized"]
        params = module.parameters
        assert params["W_N"] == "1u"
        assert params["W_P"] == "2u"
        assert params["L"] == "0.1u"
        assert params["M"] == 1
        assert params["bias_current"] == "10uA"
        assert "complex_param" in params
        assert params["complex_param"]["sub_param1"] == "value1"
    
    def test_parse_instance_with_intent(self):
        """Test parsing instances with intent metadata."""
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

modules:
  with_intent:
    instances:
      M1:
        model: "nch"
        mappings: {G: "gate", D: "drain", S: "source", B: "bulk"}
        parameters: {W: "2u", L: "0.1u"}
        intent:
          purpose: "input differential pair"
          matching: "critical"
          layout_hint: "symmetric placement"
          design_note: "This transistor must be matched"
"""
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)
        
        instance = asdl_file.modules["with_intent"].instances["M1"]
        assert instance.intent is not None
        assert instance.intent["purpose"] == "input differential pair"
        assert instance.intent["matching"] == "critical"
        assert instance.intent["layout_hint"] == "symmetric placement"
        assert instance.intent["design_note"] == "This transistor must be matched"
    
    def test_parse_invalid_port_direction(self):
        """Test error handling for invalid port direction."""
        yaml_content = """
file_info:
  top_module: "test"
  doc: ""
  revision: ""
  author: ""
  date: ""

models: {}

modules:
  bad_port:
    ports:
      invalid_dir_port:
        dir: "invalid_direction"
        type: "voltage"
"""
        parser = ASDLParser()
        
        with pytest.raises(ValueError, match="Invalid port direction 'invalid_direction'"):
            parser.parse_string(yaml_content)
    
    def test_parse_invalid_signal_type(self):
        """Test error handling for invalid signal type."""
        yaml_content = """
file_info:
  top_module: "test"
  doc: ""
  revision: ""
  author: ""
  date: ""

models: {}

modules:
  bad_signal:
    ports:
      invalid_type_port:
        dir: "in"
        type: "invalid_signal_type"
"""
        parser = ASDLParser()
        
        with pytest.raises(ValueError, match="Invalid signal type 'invalid_signal_type'"):
            parser.parse_string(yaml_content)
    
    def test_parse_module_not_dictionary(self):
        """Test error handling when module definition is not a dictionary."""
        yaml_content = """
file_info:
  top_module: "test"
  doc: ""
  revision: ""
  author: ""
  date: ""

models: {}

modules:
  bad_module: "not a dictionary"
"""
        parser = ASDLParser()
        
        with pytest.raises(ValueError, match="Module 'bad_module' must be a dictionary"):
            parser.parse_string(yaml_content)
    
    def test_parse_instance_not_dictionary(self):
        """Test error handling when instance definition is not a dictionary."""
        yaml_content = """
file_info:
  top_module: "test"
  doc: ""
  revision: ""
  author: ""
  date: ""

models: {}

modules:
  bad_instance:
    instances:
      bad_inst: "not a dictionary"
"""
        parser = ASDLParser()
        
        with pytest.raises(ValueError, match="Instance 'bad_inst' in bad_instance must be a dictionary"):
            parser.parse_string(yaml_content)
    
    def test_parse_unknown_fields_in_instance_preserved(self):
        """Test that unknown fields in instances are moved to intent."""
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

modules:
  future_instance:
    instances:
      M1:
        model: "nch"
        mappings: {G: "g", D: "d", S: "s", B: "b"}
        parameters: {W: "1u", L: "0.1u"}
        intent: {purpose: "amplifier"}
        # Future fields
        layout_constraints: {symmetry: true}
        simulation_corners: ["tt", "ss", "ff"]
"""
        parser = ASDLParser(strict_mode=False, preserve_unknown=True)
        
        with pytest.warns(UserWarning, match="Unknown fields in instance 'M1' moved to intent"):
            asdl_file = parser.parse_string(yaml_content)
        
        instance = asdl_file.modules["future_instance"].instances["M1"]
        intent = instance.intent
        
        # Original intent preserved
        assert intent["purpose"] == "amplifier"
        
        # Unknown fields moved to intent with prefix
        assert "_unknown_layout_constraints" in intent
        assert "_unknown_simulation_corners" in intent
        assert intent["_unknown_layout_constraints"]["symmetry"] is True
        assert intent["_unknown_simulation_corners"] == ["tt", "ss", "ff"]
    
    def test_parse_empty_modules_section(self):
        """Test parsing with empty modules section."""
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
        
        assert isinstance(asdl_file.modules, dict)
        assert len(asdl_file.modules) == 0 