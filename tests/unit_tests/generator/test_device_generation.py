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
        
        # Verify the resistor device line is generated correctly
        assert "R1 net1 net2 RES_1K 1k" in spice_output

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
        
        # Verify the capacitor device line is generated correctly
        assert "C1 in gnd CAP_1PF 1p" in spice_output

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
        
        # Verify the inductor device line is generated correctly
        assert "L1 rf_in rf_out IND_1NH 1n" in spice_output

    def test_generate_device_with_parameters(self):
        """Test device generation with multiple parameters (like MOSFET)."""
        # Create an NMOS model with correct SPICE node order: Drain, Gate, Source, Bulk
        nmos_model = DeviceModel(
            model="nch_lvt",
            type=DeviceType.NMOS,
            ports=["d", "g", "s", "b"],  # SPICE order: Drain, Gate, Source, Bulk
            params={"L": "0.1u"},  # Default parameter
            description="NMOS transistor model"
        )
        
        # Create an instance of the NMOS with specific parameters
        nmos_instance = Instance(
            model="nmos_device",
            mappings={"d": "drain", "g": "gate", "s": "source", "b": "bulk"},
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
        
        # Verify the NMOS device line with EXACT node order: Drain, Gate, Source, Bulk
        assert "MN1 drain gate source bulk nch_lvt" in spice_output
        assert "L=0.1u" in spice_output
        assert "W=1u" in spice_output
        assert "M=4" in spice_output
        
        # Additional verification: Check exact node order by splitting the line
        lines = spice_output.split('\n')
        nmos_line = None
        for line in lines:
            if line.strip().startswith('MN1'):
                nmos_line = line.strip()
                break
        
        assert nmos_line is not None, "NMOS device line not found"
        parts = nmos_line.split()
        assert len(parts) >= 6, f"NMOS line should have at least 6 parts, got: {parts}"
        assert parts[0] == "MN1", f"Device name should be MN1, got: {parts[0]}"
        assert parts[1] == "drain", f"First node should be drain, got: {parts[1]}"
        assert parts[2] == "gate", f"Second node should be gate, got: {parts[2]}"
        assert parts[3] == "source", f"Third node should be source, got: {parts[3]}"
        assert parts[4] == "bulk", f"Fourth node should be bulk, got: {parts[4]}"
        assert parts[5] == "nch_lvt", f"Model should be nch_lvt, got: {parts[5]}"

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
        
        # Verify the diode device line uses named parameter format
        assert "D1 anode cathode D1N4148" in spice_output
        assert "Is=1e-14" in spice_output
        assert "N=1.0" in spice_output
        assert "temp=27" in spice_output

    def test_spice_node_ordering_verification(self):
        """Test that all device types generate nodes in correct SPICE order."""
        
        # Test PMOS: Should follow same order as NMOS (Drain, Gate, Source, Bulk)
        pmos_model = DeviceModel(
            model="pch_lvt",
            type=DeviceType.PMOS,
            ports=["d", "g", "s", "b"],  # SPICE order: Drain, Gate, Source, Bulk
            params={"L": "0.18u"},
            description="PMOS transistor model"
        )
        
        pmos_instance = Instance(
            model="pmos_device",
            mappings={"d": "vdd", "g": "gate_n", "s": "out", "b": "vdd"},
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
        
        # Parse the output and verify node orders
        lines = spice_output.split('\n')
        
        # Verify PMOS node order: Drain, Gate, Source, Bulk
        pmos_line = None
        for line in lines:
            if line.strip().startswith('MP1'):
                pmos_line = line.strip()
                break
        assert pmos_line is not None
        pmos_parts = pmos_line.split()
        assert pmos_parts[1] == "vdd", f"PMOS drain should be vdd, got: {pmos_parts[1]}"
        assert pmos_parts[2] == "gate_n", f"PMOS gate should be gate_n, got: {pmos_parts[2]}"
        assert pmos_parts[3] == "out", f"PMOS source should be out, got: {pmos_parts[3]}"
        assert pmos_parts[4] == "vdd", f"PMOS bulk should be vdd, got: {pmos_parts[4]}"
        
        # Verify Resistor node order (plus, minus)
        resistor_line = None
        for line in lines:
            if line.strip().startswith('R1'):
                resistor_line = line.strip()
                break
        assert resistor_line is not None
        res_parts = resistor_line.split()
        assert res_parts[1] == "vin", f"Resistor plus terminal should be vin, got: {res_parts[1]}"
        assert res_parts[2] == "vout", f"Resistor minus terminal should be vout, got: {res_parts[2]}"
        
        # Verify Capacitor node order (plus, minus)
        capacitor_line = None  
        for line in lines:
            if line.strip().startswith('C1'):
                capacitor_line = line.strip()
                break
        assert capacitor_line is not None
        cap_parts = capacitor_line.split()
        assert cap_parts[1] == "signal", f"Capacitor plus terminal should be signal, got: {cap_parts[1]}"
        assert cap_parts[2] == "gnd", f"Capacitor minus terminal should be gnd, got: {cap_parts[2]}"
        
        # Verify Inductor node order (plus, minus)
        inductor_line = None
        for line in lines:
            if line.strip().startswith('L1'):
                inductor_line = line.strip()
                break
        assert inductor_line is not None
        ind_parts = inductor_line.split()
        assert ind_parts[1] == "rf_in", f"Inductor plus terminal should be rf_in, got: {ind_parts[1]}"
        assert ind_parts[2] == "rf_out", f"Inductor minus terminal should be rf_out, got: {ind_parts[2]}" 