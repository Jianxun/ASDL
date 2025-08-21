"""
Comprehensive unit tests for SPICEGenerator methods.

Tests each generation method individually to ensure complete coverage
of the SPICE generation functionality.
"""

import pytest
from src.asdl.generator import SPICEGenerator
from src.asdl.data_structures import (
    ASDLFile, FileInfo, Module, Instance, Port, PortDirection, 
    SignalType, DeviceModel, PrimitiveType
)


class TestSPICEGeneratorBasics:
    """Test basic SPICEGenerator functionality."""

    def test_generator_initialization(self):
        """Test that SPICEGenerator initializes with correct defaults."""
        generator = SPICEGenerator()
        
        # Check default settings
        assert generator.comment_style == "*"
        assert generator.indent == "  "

    def test_generate_from_device_line_simple(self):
        """Test _generate_from_device_line with simple NMOS device."""
        generator = SPICEGenerator()
        
        # Create a simple NMOS device model
        nmos_model = DeviceModel(
            type=PrimitiveType.PDK_DEVICE,
            ports=["G", "D", "S", "B"],
            device_line="MN {D} {G} {S} {B} nfet_03v3 L={L} W={W}",
            parameters={"L": "0.5u", "W": "4u"}
        )
        
        # Generate device line
        result = generator._generate_from_device_line(nmos_model)
        
        # Should substitute ports with identity mapping and parameters with {param} format
        expected = "MN D G S B nfet_03v3 L={L} W={W}"
        assert result == expected

    def test_generate_model_subcircuit_basic(self):
        """Test generate_model_subcircuit with basic device model."""
        generator = SPICEGenerator()
        
        # Create a basic NMOS device model
        nmos_model = DeviceModel(
            type=PrimitiveType.PDK_DEVICE,
            ports=["G", "D", "S", "B"],
            device_line="MN {D} {G} {S} {B} nfet_03v3 L={L} W={W}",
            parameters={"L": "0.5u", "W": "4u"},
            doc="Basic NMOS transistor"
        )
        
        # Generate model subcircuit
        result = generator.generate_model_subcircuit("nmos_unit", nmos_model)
        
        # Verify structure
        lines = result.split('\n')
        
        # Should start with documentation comment
        assert lines[0] == "* Basic NMOS transistor"
        
        # Should have subcircuit definition with correct ports
        assert lines[1] == ".subckt nmos_unit G D S B"
        
        # Should have parameter declarations
        assert "  .param L=0.5u" in lines
        assert "  .param W=4u" in lines
        
        # Should have device instance
        assert "  MN D G S B nfet_03v3 L={L} W={W}" in lines
        
        # Should end with .ends
        assert lines[-1] == ".ends"

    def test_generate_device_line_basic(self):
        """Test _generate_device_line with device instance."""
        generator = SPICEGenerator()
        
        # Create device model
        nmos_model = DeviceModel(
            type=PrimitiveType.PDK_DEVICE,
            ports=["G", "D", "S", "B"],
            device_line="MN {D} {G} {S} {B} nfet_03v3 L={L} W={W}",
            parameters={"L": "0.5u", "W": "4u"}
        )
        
        # Create device instance
        instance = Instance(
            model="nmos_unit",
            mappings={"G": "gate", "D": "drain", "S": "source", "B": "bulk"},
            parameters={"M": "2"}
        )
        
        # Create ASDL file with model
        asdl_file = ASDLFile(
            file_info=FileInfo(doc="Test", revision="1.0", author="test", date="2024"),
            models={"nmos_unit": nmos_model},
            modules={}
        )
        
        # Generate device line
        result = generator._generate_device_line("M1", instance, asdl_file)
        
        # Should generate subcircuit call with X_ prefix
        expected = "X_M1 gate drain source bulk nmos_unit M=2"
        assert result == expected

    def test_generate_subckt_call_basic(self):
        """Test _generate_subckt_call with module instance."""
        generator = SPICEGenerator()
        
        # Create a simple module
        module = Module(
            doc="Simple buffer",
            ports={
                "in": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                "out": Port(dir=PortDirection.OUT, type=SignalType.VOLTAGE),
                "vdd": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
                "vss": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE)
            }
        )
        
        # Create module instance
        instance = Instance(
            model="buffer",
            mappings={"in": "input", "out": "output", "vdd": "vdd_net", "vss": "vss_net"},
            parameters={"M": "4"}
        )
        
        # Create ASDL file with module
        asdl_file = ASDLFile(
            file_info=FileInfo(doc="Test", revision="1.0", author="test", date="2024"),
            models={},
            modules={"buffer": module}
        )
        
        # Generate subcircuit call
        result = generator._generate_subckt_call("BUF1", instance, asdl_file)
        
        # Should generate subcircuit call with X_ prefix and correct port order
        expected = "X_BUF1 input output vdd_net vss_net buffer M=4"
        assert result == expected

    def test_generate_subckt_basic(self):
        """Test generate_subckt with simple module containing device instance."""
        generator = SPICEGenerator()
        
        # Create device model
        nmos_model = DeviceModel(
            type=PrimitiveType.PDK_DEVICE,
            ports=["G", "D", "S", "B"],
            device_line="MN {D} {G} {S} {B} nfet_03v3 L={L} W={W}",
            parameters={"L": "0.5u", "W": "4u"}
        )
        
        # Create module with device instance
        module = Module(
            doc="Simple inverter",
            ports={
                "in": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                "out": Port(dir=PortDirection.OUT, type=SignalType.VOLTAGE),
                "vss": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE)
            },
            instances={
                "M1": Instance(
                    model="nmos_unit",
                    mappings={"G": "in", "D": "out", "S": "vss", "B": "vss"}
                )
            },
            parameters={"M": "1"}
        )
        
        # Create ASDL file
        asdl_file = ASDLFile(
            file_info=FileInfo(doc="Test", revision="1.0", author="test", date="2024"),
            models={"nmos_unit": nmos_model},
            modules={"inverter": module}
        )
        
        # Generate subcircuit
        result = generator.generate_subckt(module, "inverter", asdl_file)
        
        lines = result.split('\n')
        
        # Should start with documentation
        assert lines[0] == "* Simple inverter"
        
        # Should have subcircuit definition with correct port order
        assert lines[1] == ".subckt inverter in out vss"
        
        # Should have parameter declaration
        assert "  .param M=1" in lines
        
        # Should have device instance call
        assert "  X_M1 in out vss vss nmos_unit" in lines
        
        # Should end with .ends
        assert lines[-1] == ".ends"

    def test_generate_complete_netlist(self):
        """Test complete SPICE netlist generation with main entry point."""
        generator = SPICEGenerator()
        
        # Create device model
        nmos_model = DeviceModel(
            type=PrimitiveType.PDK_DEVICE,
            ports=["G", "D", "S", "B"],
            device_line="MN {D} {G} {S} {B} nfet_03v3 L={L} W={W}",
            parameters={"L": "0.5u", "W": "4u"}
        )
        
        # Create module
        module = Module(
            doc="Test inverter",
            ports={
                "in": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                "out": Port(dir=PortDirection.OUT, type=SignalType.VOLTAGE),
                "vss": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE)
            },
            instances={
                "M1": Instance(
                    model="nmos_unit",
                    mappings={"G": "in", "D": "out", "S": "vss", "B": "vss"}
                )
            }
        )
        
        # Create ASDL file
        asdl_file = ASDLFile(
            file_info=FileInfo(
                top_module="inverter",
                doc="Test design",
                revision="v1.0",
                author="test_author",
                date="2024-01-01"
            ),
            models={"nmos_unit": nmos_model},
            modules={"inverter": module}
        )
        
        # Generate complete SPICE netlist
        result = generator.generate(asdl_file)
        
        # Verify header information
        assert "* SPICE netlist generated from ASDL" in result
        assert "* Design: Test design" in result
        assert "* Top module: inverter" in result
        assert "* Author: test_author" in result
        assert "* Date: 2024-01-01" in result
        assert "* Revision: v1.0" in result
        
        # Should have model subcircuit first
        assert "* Model subcircuit definitions" in result
        assert ".subckt nmos_unit G D S B" in result
        
        # Should have module subcircuit second
        assert ".subckt inverter in out vss" in result
        
        # Should have main instantiation
        assert "* Main circuit instantiation" in result
        assert "XMAIN in out vss inverter" in result
        
        # Should end with .end
        assert result.strip().endswith(".end")

    def test_generated_spice_is_parseable(self):
        """Test that generated SPICE can be parsed by PySpice for validation."""
        from src.asdl.spice_validator import parse_spice_netlist, PYSPICE_AVAILABLE
        
        if not PYSPICE_AVAILABLE:
            pytest.skip("PySpice not available for SPICE validation")
        
        generator = SPICEGenerator()
        
        # Create device model
        nmos_model = DeviceModel(
            type=PrimitiveType.PDK_DEVICE,
            ports=["G", "D", "S", "B"],
            device_line="MN {D} {G} {S} {B} nfet_03v3 L={L} W={W}",
            parameters={"L": "0.5u", "W": "4u"}
        )
        
        # Create module
        module = Module(
            doc="PySpice test inverter",
            ports={
                "in": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                "out": Port(dir=PortDirection.OUT, type=SignalType.VOLTAGE),
                "vss": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE)
            },
            instances={
                "M1": Instance(
                    model="nmos_unit",
                    mappings={"G": "in", "D": "out", "S": "vss", "B": "vss"}
                )
            }
        )
        
        # Create ASDL file
        asdl_file = ASDLFile(
            file_info=FileInfo(
                top_module="test_inv",
                doc="PySpice validation test",
                revision="v1.0",
                author="test",
                date="2024-01-01"
            ),
            models={"nmos_unit": nmos_model},
            modules={"test_inv": module}
        )
        
        # Generate SPICE netlist
        spice_output, diagnostics = generator.generate(asdl_file)
        
        # Parse with PySpice - should not raise an exception
        circuit = parse_spice_netlist(spice_output)
        
        # Verify circuit parses successfully
        assert circuit is not None
        assert hasattr(circuit, '_elements')
        
        # Verify expected elements are present
        assert 'XMAIN' in circuit._elements 