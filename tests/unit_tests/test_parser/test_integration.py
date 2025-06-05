"""
Integration tests for ASDL parsing with complex examples.

Tests parsing of real-world circuits like the OTA example.
"""

import pytest
from pathlib import Path
from asdl import ASDLParser, ASDLParseError


class TestIntegration:
    """Test ASDL parsing with complex, real-world examples."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ASDLParser()
    
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
    