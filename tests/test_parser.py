"""
Tests for the ASDL Parser

Test the basic parsing functionality with simple examples and the OTA circuit.
"""

import pytest
from pathlib import Path

from asdl import ASDLParser, ASDLParseError


class TestASDLParser:
    """Test the ASDLParser class."""
    
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
    
    def test_parse_ota_file(self):
        """Test parsing the actual OTA example file."""
        ota_file = Path("examples/ota_two_stg.yaml")
        
        if not ota_file.exists():
            pytest.skip(f"OTA example file not found: {ota_file}")
        
        # Read file content and parse as string
        with open(ota_file, 'r', encoding='utf-8') as f:
            yaml_content = f.read()
        
        asdl_file = self.parser.parse_string(yaml_content)
        
        # Check file structure
        assert asdl_file.version == "ASDL v1.0"
        assert asdl_file.top_module == "ota"
        
        # Check that all expected modules are present
        expected_modules = [
            "diff_pair_nmos",
            "current_mirror_pmos_1_1", 
            "common_source_amp",
            "bias_vbn_diode",
            "ota_one_stage",
            "ota"
        ]
        
        for module_name in expected_modules:
            assert module_name in asdl_file.modules, f"Missing module: {module_name}"
        
        # Check top module
        ota_module = asdl_file.get_top_module()
        assert ota_module is not None
        assert ota_module.name == "ota"
        
        # Check that OTA has expected nets (including pattern syntax)
        expected_nets = ["in_{p,n}", "out", "iref", "vdd", "vss", "stg1_out"]
        for net in expected_nets:
            assert net in ota_module.nets, f"Missing net: {net}"
            
        # Verify we parsed circuits correctly
        assert len(ota_module.circuits) > 0
        
        # Check specific circuit details
        circuit_names = list(ota_module.circuits.keys())
        assert "vbn_gen" in circuit_names
        assert "stage1" in circuit_names
        assert "stage2" in circuit_names
        
        # Verify parameter substitution was preserved as strings
        stage1_circuit = ota_module.circuits["stage1"]
        assert stage1_circuit.parameters["M"]["diff"] == "${M.diff}"
        assert stage1_circuit.parameters["M"]["tail"] == "${M.tail}"
    
    def test_parse_ota_fixed_file(self):
        """Test parsing the fixed OTA example file with models section."""
        ota_file = Path("examples/ota_two_stg.yaml")
        
        if not ota_file.exists():
            pytest.skip(f"OTA example file not found: {ota_file}")
        
        # Read file content and parse as string
        with open(ota_file, 'r', encoding='utf-8') as f:
            yaml_content = f.read()
        
        asdl_file = self.parser.parse_string(yaml_content)
        
        # Check file structure
        assert asdl_file.version == "ASDL v1.0"
        assert asdl_file.top_module == "ota"
        
        # Check models section
        assert "nmos_unit" in asdl_file.models
        assert "pmos_unit" in asdl_file.models
        assert "cap_unit" in asdl_file.models
        assert "jumper" in asdl_file.models
        
        # Verify model definitions
        nmos_model = asdl_file.models["nmos_unit"]
        assert nmos_model["model"] == "nfet_3v3"
        assert nmos_model["L"] == "0.18u"
        assert nmos_model["W"] == "2u"
        
        # Check that circuits use explicit nets syntax and dictionary format
        diff_pair_module = asdl_file.modules["diff_pair_nmos"]
        assert len(diff_pair_module.circuits) > 0
        
        # Verify the circuit uses the new format
        circuit = list(diff_pair_module.circuits.values())[0]
        assert circuit.model == "nmos_unit"
        assert "nets" in circuit.__dict__ and circuit.nets
        assert "S" in circuit.nets
        assert "D" in circuit.nets
        assert "G" in circuit.nets
        assert "B" in circuit.nets  # Explicit bulk connection
        
        # Verify jumper is now defined as a model instead of special handling
        bias_module = asdl_file.modules["bias_vbn_diode"]
        jumper_circuit = bias_module.circuits["J1"]
        assert jumper_circuit.model == "jumper"
        assert jumper_circuit.nets["p1"] == "iref"
        assert jumper_circuit.nets["p2"] == "vbn"
    
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
    
    def test_parse_missing_file(self):
        """Test that parse_file method no longer exists."""
        # This test verifies that parse_file method was removed
        with pytest.raises(AttributeError):
            self.parser.parse_file("nonexistent.yaml")
    
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
        import json
        parsed_json = json.loads(json_str)
        assert parsed_json['version'] == "ASDL v1.0"
        assert parsed_json['modules']['test']['parameters']['M'] == 2
        
        # Test that patterns and parameter substitutions are preserved
        circuit = parsed_json['modules']['test']['circuits']['MN1']
        assert circuit['parameters']['M'] == "${M}"  # Preserved as string 