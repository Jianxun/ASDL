"""
Tests for SPICE device generation functionality.

This module tests the conversion of ASDL device instances to SPICE device lines.
"""

import pytest
from src.asdl.data_structures import DeviceModel, DeviceType, Instance, ASDLFile, FileInfo, Module
from src.asdl.generator import SPICEGenerator


class TestDeviceGeneration:
    """Test SPICE device line generation."""

    def test_generate_simple_resistor(self):
        """Test basic resistor device line generation."""
        # Create a simple resistor model
        resistor_model = DeviceModel(
            model="RES_1K",
            type=DeviceType.RESISTOR,
            ports=["plus", "minus"],  # Standard two-terminal ports
            params={},
            description="1k resistor model"
        )
        
        # Create an instance of the resistor
        resistor_instance = Instance(
            model="res_1k",
            mappings={"plus": "net1", "minus": "net2"},
            parameters={"value": "1k"}
        )
        
        # Create minimal ASDL file structure
        file_info = FileInfo(
            top_module="test_circuit",
            doc="Test circuit for resistor generation",
            revision="1.0",
            author="test",
            date="2024-01-01"
        )
        
        test_module = Module(
            doc="Test module",
            ports={},
            instances={"R1": resistor_instance},
            nets=None,
            parameters=None
        )
        
        asdl_file = ASDLFile(
            file_info=file_info,
            models={"res_1k": resistor_model},
            modules={"test_circuit": test_module}
        )
        
        # Generate SPICE
        generator = SPICEGenerator()
        spice_output = generator.generate(asdl_file)
        
        # Verify hierarchical subcircuit generation
        # Model should generate as subcircuit with internal device
        assert ".subckt res_1k plus minus" in spice_output
        assert "R plus minus RES_1K" in spice_output
        assert ".ends" in spice_output
        
        # Instance should generate as subcircuit call
        assert "X_R1 net1 net2 res_1k value=1k" in spice_output

    def test_generate_capacitor(self):
        """Test capacitor device line generation."""
        # Create a capacitor model
        capacitor_model = DeviceModel(
            model="CAP_1PF",
            type=DeviceType.CAPACITOR,
            ports=["plus", "minus"],
            params={},
            description="1pF capacitor model"
        )
        
        # Create an instance of the capacitor
        capacitor_instance = Instance(
            model="cap_1pf",
            mappings={"plus": "in", "minus": "gnd"},
            parameters={"value": "1p"}
        )
        
        # Create minimal ASDL file structure
        file_info = FileInfo(
            top_module="test_circuit",
            doc="Test circuit for capacitor generation",
            revision="1.0",
            author="test",
            date="2024-01-01"
        )
        
        test_module = Module(
            doc="Test module with capacitor",
            ports={},
            instances={"C1": capacitor_instance},
            nets=None,
            parameters=None
        )
        
        asdl_file = ASDLFile(
            file_info=file_info,
            models={"cap_1pf": capacitor_model},
            modules={"test_circuit": test_module}
        )
        
        # Generate SPICE
        generator = SPICEGenerator()
        spice_output = generator.generate(asdl_file)
        
        # Verify hierarchical subcircuit generation
        # Model should generate as subcircuit with internal device
        assert ".subckt cap_1pf plus minus" in spice_output
        assert "C plus minus CAP_1PF" in spice_output
        assert ".ends" in spice_output
        
        # Instance should generate as subcircuit call
        assert "X_C1 in gnd cap_1pf value=1p" in spice_output

    def test_generate_inductor(self):
        """Test inductor device line generation."""
        # Create an inductor model
        inductor_model = DeviceModel(
            model="IND_1NH",
            type=DeviceType.INDUCTOR,
            ports=["plus", "minus"],
            params={},
            description="1nH inductor model"
        )
        
        # Create an instance of the inductor
        inductor_instance = Instance(
            model="ind_1nh",
            mappings={"plus": "rf_in", "minus": "rf_out"},
            parameters={"value": "1n"}
        )
        
        # Create minimal ASDL file structure
        file_info = FileInfo(
            top_module="test_circuit",
            doc="Test circuit for inductor generation",
            revision="1.0",
            author="test",
            date="2024-01-01"
        )
        
        test_module = Module(
            doc="Test module with inductor",
            ports={},
            instances={"L1": inductor_instance},
            nets=None,
            parameters=None
        )
        
        asdl_file = ASDLFile(
            file_info=file_info,
            models={"ind_1nh": inductor_model},
            modules={"test_circuit": test_module}
        )
        
        # Generate SPICE
        generator = SPICEGenerator()
        spice_output = generator.generate(asdl_file)
        
        # Verify hierarchical subcircuit generation
        # Model should generate as subcircuit with internal device
        assert ".subckt ind_1nh plus minus" in spice_output
        assert "L plus minus IND_1NH" in spice_output
        assert ".ends" in spice_output
        
        # Instance should generate as subcircuit call
        assert "X_L1 rf_in rf_out ind_1nh value=1n" in spice_output

    def test_generate_device_with_parameters(self):
        """Test device generation with multiple parameters (like MOSFET)."""
        # Create an NMOS model with correct SPICE node order: Drain, Gate, Source, Bulk
        nmos_model = DeviceModel(
            model="nch_lvt",
            type=DeviceType.NMOS,
            ports=["D", "G", "S", "B"],  # SPICE order: Drain, Gate, Source, Bulk
            params={"L": "0.1u"},  # Default parameter
            description="NMOS transistor model"
        )

        # Create an instance of the NMOS with specific parameters
        nmos_instance = Instance(
            model="nmos_device",
            mappings={"D": "drain", "G": "gate", "S": "source", "B": "bulk"},
            parameters={"W": "1u", "M": "4"}  # Instance-specific parameters
        )
        
        # Create minimal ASDL file structure
        file_info = FileInfo(
            top_module="test_circuit",
            doc="Test circuit for NMOS generation",
            revision="1.0",
            author="test",
            date="2024-01-01"
        )
        
        test_module = Module(
            doc="Test module with NMOS",
            ports={},
            instances={"MN1": nmos_instance},
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
        
        # Verify hierarchical subcircuit generation
        # Model should generate as subcircuit with internal device
        assert ".subckt nmos_device D G S B" in spice_output
        assert ".param L=0.1u" in spice_output
        assert "MN D G S B nch_lvt L=0.1u" in spice_output
        assert ".ends" in spice_output
        
        # Instance should generate as subcircuit call with parameters
        assert "X_MN1 drain gate source bulk nmos_device M=4 W=1u" in spice_output

    def test_generate_device_invalid_model(self):
        """Test error handling for missing model references."""
        # Create an instance that references a non-existent model
        invalid_instance = Instance(
            model="nonexistent_model",
            mappings={"p": "net1", "n": "net2"},
            parameters={"value": "1k"}
        )
        
        # Create minimal ASDL file structure
        file_info = FileInfo(
            top_module="test_circuit",
            doc="Test circuit for error handling",
            revision="1.0",
            author="test",
            date="2024-01-01"
        )
        
        test_module = Module(
            doc="Test module with invalid reference",
            ports={},
            instances={"X1": invalid_instance},
            nets=None,
            parameters=None
        )
        
        asdl_file = ASDLFile(
            file_info=file_info,
            models={},  # Empty models dict - no model available
            modules={"test_circuit": test_module}
        )
        
        # Generate SPICE - should raise ValueError
        generator = SPICEGenerator()
        with pytest.raises(ValueError, match="Unknown model reference"):
            generator.generate(asdl_file)

    def test_device_template_extensibility(self):
        """Test that the template system handles new device types gracefully."""
        # Create a diode model (uses the template system)
        diode_model = DeviceModel(
            model="D1N4148",
            type=DeviceType.DIODE,
            ports=["a", "c"],
            params={"Is": "1e-14", "N": "1.0"},
            description="Standard diode model"
        )
        
        # Create an instance of the diode
        diode_instance = Instance(
            model="diode_1",
            mappings={"a": "anode", "c": "cathode"},
            parameters={"temp": "27"}  # Instance-specific parameter
        )
        
        # Create minimal ASDL file structure
        file_info = FileInfo(
            top_module="test_circuit",
            doc="Test circuit for diode generation",
            revision="1.0",
            author="test",
            date="2024-01-01"
        )
        
        test_module = Module(
            doc="Test module with diode",
            ports={},
            instances={"D1": diode_instance},
            nets=None,
            parameters=None
        )
        
        asdl_file = ASDLFile(
            file_info=file_info,
            models={"diode_1": diode_model},
            modules={"test_circuit": test_module}
        )
        
        # Generate SPICE
        generator = SPICEGenerator()
        spice_output = generator.generate(asdl_file)
        
        # Verify hierarchical subcircuit generation
        # Model should generate as subcircuit with internal device
        assert ".subckt diode_1 a c" in spice_output
        assert ".param Is=1e-14" in spice_output
        assert ".param N=1.0" in spice_output
        assert "D a c D1N4148 Is=1e-14 N=1.0" in spice_output
        assert ".ends" in spice_output
        
        # Instance should generate as subcircuit call with parameters
        assert "X_D1 anode cathode diode_1 temp=27" in spice_output

    def test_spice_node_ordering_verification(self):
        """Test that all device types generate nodes in correct SPICE order."""
        
        # Test PMOS: Should follow same order as NMOS (Drain, Gate, Source, Bulk)
        pmos_model = DeviceModel(
            model="pch_lvt",
            type=DeviceType.PMOS,
            ports=["D", "G", "S", "B"],  # SPICE order: Drain, Gate, Source, Bulk
            params={"L": "0.18u"},
            description="PMOS transistor model"
        )

        pmos_instance = Instance(
            model="pmos_device",
            mappings={"D": "vdd", "G": "gate_n", "S": "out", "B": "vdd"},
        )
        
        # Test Resistor: Two terminals (plus/minus standard naming)
        resistor_model = DeviceModel(
            model="RES_MODEL",
            type=DeviceType.RESISTOR,
            ports=["plus", "minus"],
            params={},
        )
        
        resistor_instance = Instance(
            model="res_model",
            mappings={"plus": "vin", "minus": "vout"},
            parameters={"value": "10k"}
        )
        
        # Test Capacitor: Plus/minus standard naming
        capacitor_model = DeviceModel(
            model="CAP_MODEL",
            type=DeviceType.CAPACITOR,
            ports=["plus", "minus"],
            params={},
        )
        
        capacitor_instance = Instance(
            model="cap_model",
            mappings={"plus": "signal", "minus": "gnd"},
            parameters={"value": "100f"}
        )
        
        # Test Inductor: Plus/minus standard naming
        inductor_model = DeviceModel(
            model="IND_MODEL",
            type=DeviceType.INDUCTOR,
            ports=["plus", "minus"],
            params={},
        )
        
        inductor_instance = Instance(
            model="ind_model",
            mappings={"plus": "rf_in", "minus": "rf_out"},
            parameters={"value": "10n"}
        )
        
        # Create test module with all devices
        file_info = FileInfo(
            top_module="node_order_test",
            doc="Test for SPICE node ordering",
            revision="1.0",
            author="test",
            date="2024-01-01"
        )
        
        test_module = Module(
            doc="Node order verification module",
            ports={},
            instances={
                "MP1": pmos_instance,
                "R1": resistor_instance,
                "C1": capacitor_instance,
                "L1": inductor_instance
            },
            nets=None,
            parameters=None
        )
        
        asdl_file = ASDLFile(
            file_info=file_info,
            models={
                "pmos_device": pmos_model,
                "res_model": resistor_model,
                "cap_model": capacitor_model,
                "ind_model": inductor_model
            },
            modules={"node_order_test": test_module}
        )
        
        # Generate SPICE
        generator = SPICEGenerator()
        spice_output = generator.generate(asdl_file)
        
        # Verify hierarchical subcircuit generation and node ordering
        # All devices should be inside their respective subcircuits
        
        # Verify PMOS subcircuit and internal device node order
        assert ".subckt pmos_device D G S B" in spice_output
        assert "MP D G S B pch_lvt" in spice_output
        assert "X_MP1 vdd gate_n out vdd pmos_device" in spice_output
        
        # Verify resistor subcircuit and internal device node order
        assert ".subckt res_model plus minus" in spice_output
        assert "R plus minus RES_MODEL" in spice_output
        assert "X_R1 vin vout res_model value=10k" in spice_output
        
        # Verify capacitor subcircuit and internal device node order
        assert ".subckt cap_model plus minus" in spice_output
        assert "C plus minus CAP_MODEL" in spice_output
        assert "X_C1 signal gnd cap_model value=100f" in spice_output
        
        # Verify inductor subcircuit and internal device node order
        assert ".subckt ind_model plus minus" in spice_output
        assert "L plus minus IND_MODEL" in spice_output
        assert "X_L1 rf_in rf_out ind_model value=10n" in spice_output 