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

.defaults: &DEF
  NMOS: &NMOS {model: nmos_unit, B: VSS}

modules:
  simple:
    nets: {in: in, out: out, vdd: io, vss: io}
    parameters: {M: 1}
    circuits:
      - {<<: *NMOS, name: MN1, S: vss, D: out, G: in, M: "${M}"}
"""
        
        asdl_file = self.parser.parse_string(yaml_content)
        
        # Check file-level properties
        assert asdl_file.version == "ASDL v1.0"
        assert asdl_file.top_module == "simple"
        assert "NMOS" in asdl_file.defaults
        
        # Check module
        assert "simple" in asdl_file.modules
        simple_module = asdl_file.modules["simple"]
        
        assert simple_module.name == "simple"
        assert simple_module.nets == {"in": "in", "out": "out", "vdd": "io", "vss": "io"}
        assert simple_module.parameters == {"M": 1}
        assert len(simple_module.circuits) == 1
        
        # Check circuit
        circuit = simple_module.circuits[0]
        assert circuit.name == "MN1"
        assert circuit.model == "nmos_unit"
        assert circuit.parameters["S"] == "vss"
        assert circuit.parameters["D"] == "out"
        assert circuit.parameters["G"] == "in"
        assert circuit.parameters["M"] == "${M}"  # Not resolved yet
    
    def test_parse_ota_file(self):
        """Test parsing the actual OTA example file."""
        ota_file = Path("examples/ota_two_stg.yaml")
        
        if not ota_file.exists():
            pytest.skip(f"OTA example file not found: {ota_file}")
        
        asdl_file = self.parser.parse_file(ota_file)
        
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
        circuit_names = [c.name for c in ota_module.circuits if c.name]
        assert "vbn_gen" in circuit_names
        assert "stage1" in circuit_names
        assert "stage2" in circuit_names
        
        # Verify parameter substitution was preserved as strings
        stage1_circuit = next(c for c in ota_module.circuits if c.name == "stage1")
        assert stage1_circuit.parameters["M"]["diff"] == "${M.diff}"
        assert stage1_circuit.parameters["M"]["tail"] == "${M.tail}"
    
    def test_parse_circuits_list_format(self):
        """Test parsing circuits in list format."""
        yaml_content = """
modules:
  test:
    circuits:
      - {name: MN1, model: nmos_unit, S: vss, D: out, G: in}
      - {name: MP1, model: pmos_unit, S: vdd, D: out, G: in}
"""
        
        asdl_file = self.parser.parse_string(yaml_content)
        test_module = asdl_file.modules["test"]
        
        assert len(test_module.circuits) == 2
        assert test_module.circuits[0].name == "MN1"
        assert test_module.circuits[0].model == "nmos_unit"
        assert test_module.circuits[1].name == "MP1"
        assert test_module.circuits[1].model == "pmos_unit"
    
    def test_parse_circuits_dict_format(self):
        """Test parsing circuits in dictionary format."""
        yaml_content = """
modules:
  test:
    circuits:
      diff: {model: diff_pair_nmos, M: 2}
      tail: {model: nmos_unit, name: MN_TAIL, S: vss, G: vbn}
"""
        
        asdl_file = self.parser.parse_string(yaml_content)
        test_module = asdl_file.modules["test"]
        
        assert len(test_module.circuits) == 2
        
        # First circuit should get name from dict key
        diff_circuit = next(c for c in test_module.circuits if c.name == "diff")
        assert diff_circuit.model == "diff_pair_nmos"
        assert diff_circuit.parameters["M"] == 2
        
        # Second circuit has explicit name
        tail_circuit = next(c for c in test_module.circuits if c.name == "MN_TAIL")
        assert tail_circuit.model == "nmos_unit"
        assert tail_circuit.parameters["S"] == "vss"
    
    def test_parse_invalid_yaml(self):
        """Test error handling for invalid YAML."""
        invalid_yaml = """
modules:
  test:
    circuits:
      - {name: MN1, model: nmos_unit
        # Missing closing brace
"""
        
        with pytest.raises(ASDLParseError, match="YAML parsing error"):
            self.parser.parse_string(invalid_yaml)
    
    def test_parse_missing_file(self):
        """Test error handling for missing file."""
        with pytest.raises(ASDLParseError, match="File not found"):
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
modules:
  leaf:
    circuits:
      - {name: MN1, model: nmos_unit}
  
  parent:
    circuits:
      - {name: sub1, model: leaf}
      - {name: MN2, model: pmos_unit}
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

modules:
  test:
    nets: {in: in, out: out}
    parameters: {M: 2, W: "10u"}
    circuits:
      - {name: MN1, model: nmos_unit, S: vss, D: out, G: in, M: "${M}"}
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
        circuit = parsed_json['modules']['test']['circuits'][0]
        assert circuit['parameters']['M'] == "${M}"  # Preserved as string 