"""
Tests for basic ASDL parsing functionality.

Tests the fundamental parsing capabilities with simple examples.
"""

import pytest
from asdl import ASDLParser, ASDLParseError


class TestBasicParsing:
    """Test basic ASDL parsing functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ASDLParser()
    
    def test_parse_simple_module(self):
        """Test parsing a simple module from string."""
        yaml_content = """
.version: "ASDL v1.0"
.top_module: simple

models:
  nmos_unit: {model: nfet_3v3, L: 0.18u, W: 2u, NF: 2}

modules:
  simple:
    nets: {in: in, out: out, vdd: io, vss: io}
    parameters: {M: 1}
    circuits:
      MN1:
        model: nmos_unit
        nets: {S: vss, D: out, G: in, B: VSS}
        M: "${M}"
"""
        
        asdl_file = self.parser.parse_string(yaml_content)
        
        # Check file-level properties
        assert asdl_file.version == "ASDL v1.0"
        assert asdl_file.top_module == "simple"
        assert "nmos_unit" in asdl_file.models
        assert asdl_file.models["nmos_unit"]["model"] == "nfet_3v3"
        
        # Check module
        assert "simple" in asdl_file.modules
        simple_module = asdl_file.modules["simple"]
        
        assert simple_module.name == "simple"
        assert simple_module.nets == {"in": "in", "out": "out", "vdd": "io", "vss": "io"}
        assert simple_module.parameters == {"M": 1}
        assert len(simple_module.circuits) == 1
        
        # Check circuit
        circuit = simple_module.circuits["MN1"]
        assert circuit.name is None  # Name is redundant when it matches the key
        assert circuit.model == "nmos_unit"
        assert circuit.nets["S"] == "vss"
        assert circuit.nets["D"] == "out"
        assert circuit.nets["G"] == "in"
        assert circuit.nets["B"] == "VSS"
        assert circuit.parameters["M"] == "${M}"  # Not resolved yet

    def test_parse_circuits_dict_format(self):
        """Test parsing circuits in dictionary format."""
        yaml_content = """
models:
  nmos_unit: {model: nfet_3v3, L: 0.18u, W: 2u}
  pmos_unit: {model: pfet_3v3, L: 0.18u, W: 4u}

modules:
  test:
    circuits:
      MN1:
        model: nmos_unit
        nets: {S: vss, D: out, G: in, B: VSS}
      MP1:
        model: pmos_unit
        nets: {S: vdd, D: out, G: in, B: VDD}
"""
        
        asdl_file = self.parser.parse_string(yaml_content)
        test_module = asdl_file.modules["test"]
        
        assert len(test_module.circuits) == 2
        
        # Check circuits by name
        mn1_circuit = test_module.circuits["MN1"]
        assert mn1_circuit.name is None  # Name matches key, so it's None
        assert mn1_circuit.model == "nmos_unit"
        assert mn1_circuit.nets["S"] == "vss"
        
        mp1_circuit = test_module.circuits["MP1"]
        assert mp1_circuit.name is None  # Name matches key, so it's None
        assert mp1_circuit.model == "pmos_unit"
        assert mp1_circuit.nets["S"] == "vdd"
    
    def test_parse_circuits_with_explicit_name(self):
        """Test parsing circuits with explicit name field."""
        yaml_content = """
models:
  nmos_unit: {model: nfet_3v3, L: 0.18u, W: 2u}

modules:
  test:
    circuits:
      diff: {model: diff_pair_nmos, M: 2}
      tail: 
        name: MN_TAIL
        model: nmos_unit
        nets: {S: vss, G: vbn, D: out, B: VSS}
"""
        
        asdl_file = self.parser.parse_string(yaml_content)
        test_module = asdl_file.modules["test"]
        
        assert len(test_module.circuits) == 2
        
        # First circuit should get name from dict key
        diff_circuit = test_module.circuits["diff"]
        assert diff_circuit.name is None  # No explicit name, key is used
        assert diff_circuit.model == "diff_pair_nmos"
        assert diff_circuit.parameters["M"] == 2
        
        # Second circuit has explicit name different from key
        tail_circuit = test_module.circuits["tail"]
        assert tail_circuit.name == "MN_TAIL"  # Explicit name differs from key
        assert tail_circuit.model == "nmos_unit"
        assert tail_circuit.nets["S"] == "vss"

    def test_module_dependencies(self):
        """Test module dependency detection."""
        yaml_content = """
models:
  nmos_unit: {model: nfet_3v3, L: 0.18u, W: 2u}
  pmos_unit: {model: pfet_3v3, L: 0.18u, W: 4u}

modules:
  leaf:
    circuits:
      MN1:
        model: nmos_unit
        nets: {S: vss, D: out, G: in, B: VSS}
  
  parent:
    circuits:
      sub1: {model: leaf}
      MN2:
        model: pmos_unit
        nets: {S: vdd, D: out, G: in, B: VDD}
"""
        
        asdl_file = self.parser.parse_string(yaml_content)
        
        # leaf module has no dependencies
        assert asdl_file.get_module_dependencies("leaf") == []
        
        # parent module depends on leaf
        assert asdl_file.get_module_dependencies("parent") == ["leaf"] 