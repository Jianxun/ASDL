"""
Tests for two-level port resolution functionality.

This module tests that instance port mappings are order-independent
and are correctly resolved to model-defined port order.
"""

import pytest
from pathlib import Path
from src.asdl.parser import ASDLParser
from src.asdl.generator import SPICEGenerator


class TestPortResolution:
    """Test two-level port resolution functionality."""

    def test_port_mapping_order_independence(self):
        """Test that reordered instance mappings produce identical SPICE output."""
        parser = ASDLParser()
        fixtures_dir = Path(__file__).parent.parent.parent / "fixtures"
        
        # Parse original inverter with standard mapping order
        original_path = fixtures_dir / "inverter.yml"
        original_asdl = parser.parse_file(str(original_path))
        
        # Parse reordered inverter with different mapping order
        reordered_path = fixtures_dir / "inverter_reordered.yml"
        reordered_asdl = parser.parse_file(str(reordered_path))
        
        # Generate SPICE from both
        generator = SPICEGenerator()
        original_spice = generator.generate(original_asdl)
        reordered_spice = generator.generate(reordered_asdl)
        
        print("Original SPICE:")
        print(original_spice)
        print("\nReordered SPICE:")
        print(reordered_spice)
        
        # The key assertion: both should produce identical subcircuit calls
        # despite different mapping order in YAML
        assert 'X_MP in out vdd vdd pmos_unit M=2' in original_spice
        assert 'X_MP in out vdd vdd pmos_unit M=2' in reordered_spice
        assert 'X_MN in out vss vss nmos_unit M=2' in original_spice
        assert 'X_MN in out vss vss nmos_unit M=2' in reordered_spice
        
        # Both should have identical model subcircuits
        assert '.subckt nmos_unit G D S B' in original_spice
        assert '.subckt nmos_unit G D S B' in reordered_spice
        assert '.subckt pmos_unit G D S B' in original_spice
        assert '.subckt pmos_unit G D S B' in reordered_spice
        
        # Verify the primitive devices inside models are identical
        assert 'MN D G S B nfet_03v3 L=0.5u W=4u nf=2' in original_spice
        assert 'MN D G S B nfet_03v3 L=0.5u W=4u nf=2' in reordered_spice
        assert 'MP D G S B pfet_03v3 L=0.5u W=5u nf=2' in original_spice
        assert 'MP D G S B pfet_03v3 L=0.5u W=5u nf=2' in reordered_spice

    def test_port_resolution_with_missing_mapping(self):
        """Test error handling when instance mapping is missing a required port."""
        from src.asdl.data_structures import DeviceModel, DeviceType, Instance, ASDLFile, FileInfo, Module
        
        # Create NMOS model with 4 ports
        nmos_model = DeviceModel(
            model="nch_lvt",
            type=DeviceType.NMOS,
            ports=["G", "D", "S", "B"],
            params={"W": "1u", "L": "0.1u"},
            description="NMOS transistor model"
        )
        
        # Create instance missing the bulk connection
        incomplete_instance = Instance(
            model="nmos_device",
            mappings={"G": "gate", "D": "drain", "S": "source"},  # Missing B
            parameters={"M": "2"}
        )
        
        # Create test structure
        file_info = FileInfo(
            top_module="test_circuit",
            doc="Test circuit for missing port mapping",
            revision="1.0",
            author="test",
            date="2024-01-01"
        )
        
        test_module = Module(
            doc="Test module",
            ports={},
            instances={"MN1": incomplete_instance},
            nets=None,
            parameters=None
        )
        
        asdl_file = ASDLFile(
            file_info=file_info,
            models={"nmos_device": nmos_model},
            modules={"test_circuit": test_module}
        )
        
        # Generate SPICE
        generator = SPICEGenerator()
        spice_output = generator.generate(asdl_file)
        
        # Should generate UNCONNECTED for missing port
        assert 'X_MN1 gate drain source UNCONNECTED nmos_device M=2' in spice_output

    def test_level1_port_resolution(self):
        """Test Level 1: Model ports to SPICE device order (strict)."""
        # This tests that the primitive device inside the model subcircuit
        # uses the correct SPICE port order regardless of model port order
        
        from src.asdl.data_structures import DeviceModel, DeviceType
        
        # Create NMOS model with specific port order
        nmos_model = DeviceModel(
            model="nch_lvt",
            type=DeviceType.NMOS,
            ports=["G", "D", "S", "B"],  # Model port order
            params={"W": "1u", "L": "0.1u"},
            description="NMOS transistor model"
        )
        
        generator = SPICEGenerator()
        model_subckt = generator.generate_model_subcircuit("nmos_unit", nmos_model)
        
        print("Generated model subcircuit:")
        print(model_subckt)
        
        # Verify Level 1: Identity mapping within model subcircuit
        assert '.subckt nmos_unit G D S B' in model_subckt
        assert 'MN D G S B nch_lvt W=1u L=0.1u' in model_subckt
        
        # The SPICE device order is preserved: D G S B (Drain Gate Source Bulk)
        # This is the strict SPICE device requirement

    def test_invalid_port_mapping_validation(self):
        """Test validation of invalid port mappings in module instances."""
        from src.asdl.data_structures import (DeviceModel, DeviceType, Instance, ASDLFile, 
                                               FileInfo, Module, Port, PortDirection, SignalType)
        
        # Create a module with specific ports
        test_module = Module(
            doc="Test module with two ports",
            ports={
                "input": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                "output": Port(dir=PortDirection.OUT, type=SignalType.VOLTAGE)
            },
            instances={},
            nets=None,
            parameters=None
        )
        
        # Create instance with invalid port mappings
        invalid_instance = Instance(
            model="test_module",
            mappings={
                "wrong_port": "net1",    # Invalid port name
                "another_bad": "net2"    # Invalid port name  
            },
            parameters=None
        )
        
        # Create test structure
        file_info = FileInfo(
            top_module="main_circuit",
            doc="Test circuit for port mapping validation",
            revision="1.0",
            author="test",
            date="2024-01-01"
        )
        
        main_module = Module(
            doc="Main test module",
            ports={},
            instances={"BAD_INST": invalid_instance},
            nets=None,
            parameters=None
        )
        
        asdl_file = ASDLFile(
            file_info=file_info,
            models={},
            modules={
                "test_module": test_module,
                "main_circuit": main_module
            }
        )
        
        # Generate SPICE - should raise ValueError for invalid ports
        generator = SPICEGenerator()
        with pytest.raises(ValueError, match="maps to invalid ports"):
            generator.generate(asdl_file)

    def test_mixed_valid_invalid_port_mappings(self):
        """Test validation when some ports are valid and some are invalid."""
        from src.asdl.data_structures import (DeviceModel, DeviceType, Instance, ASDLFile, 
                                               FileInfo, Module, Port, PortDirection, SignalType)
        
        # Create a module with specific ports
        test_module = Module(
            doc="Test module with defined ports",
            ports={
                "input": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                "output": Port(dir=PortDirection.OUT, type=SignalType.VOLTAGE),
                "enable": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE)
            },
            instances={},
            nets=None,
            parameters=None
        )
        
        # Create instance with mixed valid/invalid mappings
        mixed_instance = Instance(
            model="test_module",
            mappings={
                "input": "input_net",      # Valid
                "invalid_port": "bad_net", # Invalid
                "output": "output_net"     # Valid
            },
            parameters=None
        )
        
        # Create test structure
        file_info = FileInfo(
            top_module="main_circuit",
            doc="Test circuit for mixed port mapping validation",
            revision="1.0",
            author="test",
            date="2024-01-01"
        )
        
        main_module = Module(
            doc="Main test module",
            ports={},
            instances={"MIXED_INST": mixed_instance},
            nets=None,
            parameters=None
        )
        
        asdl_file = ASDLFile(
            file_info=file_info,
            models={},
            modules={
                "test_module": test_module,
                "main_circuit": main_module
            }
        )
        
        # Generate SPICE - should raise ValueError identifying the invalid port
        generator = SPICEGenerator()
        with pytest.raises(ValueError) as exc_info:
            generator.generate(asdl_file)
        
        # Verify the error message contains the invalid port name
        assert "invalid_port" in str(exc_info.value)
        assert "MIXED_INST" in str(exc_info.value) 