"""
Tests for SPICE generator pipeline structure and ordering.

This module tests that the generator produces correctly ordered SPICE output
that is compatible with ngspice and follows SPICE best practices.
"""

import pytest
from pathlib import Path
from src.asdl.parser import ASDLParser
from src.asdl.generator import SPICEGenerator
from src.asdl.data_structures import FileInfo, Module, Port, Instance, DeviceModel, DeviceType, ASDLFile, PortDirection, SignalType


class TestPipelineStructure:
    """Test SPICE generator pipeline structure and ordering."""

    def test_complete_pipeline_structure(self):
        """Test that the complete SPICE pipeline follows the correct order."""
        parser = ASDLParser()
        fixtures_dir = Path(__file__).parent.parent.parent / "fixtures"
        inverter_path = fixtures_dir / "inverter.yml"
        asdl_file = parser.parse_file(str(inverter_path))
        
        generator = SPICEGenerator()
        spice_output = generator.generate(asdl_file)
        
        lines = spice_output.split('\n')
        non_empty_lines = [line for line in lines if line.strip() and not line.strip().startswith('*')]
        
        print("Pipeline structure:")
        for i, line in enumerate(non_empty_lines):
            print(f"{i+1:2d}: {line}")
        
        # Verify pipeline order
        pipeline_sections = []
        current_section = None
        
        for line in non_empty_lines:
            line = line.strip()
            if line.startswith('.subckt') and 'nmos_unit' in line:
                current_section = 'model_subcircuits'
            elif line.startswith('.subckt') and 'pmos_unit' in line:
                current_section = 'model_subcircuits'
            elif line.startswith('.subckt') and 'inverter' in line:
                current_section = 'module_subcircuits'
            elif line.startswith('XMAIN'):
                current_section = 'main_instantiation'
            elif line == '.end':
                current_section = 'end_statement'
            
            if current_section and current_section not in pipeline_sections:
                pipeline_sections.append(current_section)
        
        # Verify correct pipeline order
        expected_order = [
            'model_subcircuits',
            'module_subcircuits', 
            'main_instantiation',
            'end_statement'
        ]
        
        assert pipeline_sections == expected_order, f"Pipeline order incorrect: {pipeline_sections}"
        
        # Verify ngspice compatibility markers
        assert spice_output.strip().endswith('.end'), "SPICE file should end with .end statement"
        assert '.subckt' in spice_output, "Should contain subcircuit definitions"
        assert '.ends' in spice_output, "Should contain subcircuit endings"

    def test_model_subcircuits_come_first(self):
        """Test that model subcircuits are generated before module subcircuits."""
        parser = ASDLParser()
        fixtures_dir = Path(__file__).parent.parent.parent / "fixtures"
        inverter_path = fixtures_dir / "inverter.yml"
        asdl_file = parser.parse_file(str(inverter_path))
        
        generator = SPICEGenerator()
        spice_output = generator.generate(asdl_file)
        
        # Find positions of different subcircuit types
        nmos_pos = spice_output.find('.subckt nmos_unit')
        pmos_pos = spice_output.find('.subckt pmos_unit')
        inverter_pos = spice_output.find('.subckt inverter')
        
        # Model subcircuits should come before module subcircuits
        assert nmos_pos < inverter_pos, "NMOS model should come before inverter module"
        assert pmos_pos < inverter_pos, "PMOS model should come before inverter module"
        assert nmos_pos != -1 and pmos_pos != -1 and inverter_pos != -1, "All subcircuits should be present"

    def test_hierarchical_instance_calls(self):
        """Test that hierarchical instance calls use correct subcircuit references."""
        parser = ASDLParser()
        fixtures_dir = Path(__file__).parent.parent.parent / "fixtures"
        inverter_path = fixtures_dir / "inverter.yml"
        asdl_file = parser.parse_file(str(inverter_path))
        
        generator = SPICEGenerator()
        spice_output = generator.generate(asdl_file)
        
        # Verify hierarchical calls reference the correct subcircuits
        assert 'X_MP in out vdd vdd pmos_unit M=2' in spice_output
        assert 'X_MN in out vss vss nmos_unit M=2' in spice_output
        assert 'XMAIN in out vss vdd inverter' in spice_output
        
        # Verify that the subcircuits being referenced actually exist
        assert '.subckt pmos_unit G D S B' in spice_output
        assert '.subckt nmos_unit G D S B' in spice_output
        assert '.subckt inverter in out vss vdd' in spice_output

    def test_ngspice_compatibility_features(self):
        """Test specific ngspice compatibility features."""
        parser = ASDLParser()
        fixtures_dir = Path(__file__).parent.parent.parent / "fixtures"
        inverter_path = fixtures_dir / "inverter.yml"
        asdl_file = parser.parse_file(str(inverter_path))
        
        generator = SPICEGenerator()
        spice_output = generator.generate(asdl_file)
        
        # Check for ngspice compatibility features
        lines = spice_output.split('\n')
        
        # Comments should use '*' (SPICE standard)
        comment_lines = [line for line in lines if line.strip().startswith('*')]
        assert len(comment_lines) > 0, "Should have comment lines"
        
        # Proper .subckt/.ends pairing
        subckt_count = spice_output.count('.subckt')
        ends_count = spice_output.count('.ends')
        assert subckt_count == ends_count, f"Unmatched .subckt/.ends: {subckt_count} vs {ends_count}"
        
        # Proper indentation for readability
        indented_lines = [line for line in lines if line.startswith('  ') and line.strip()]
        assert len(indented_lines) > 0, "Should have properly indented subcircuit content"
        
        # X-prefix for subcircuit calls
        x_calls = [line for line in lines if line.strip().startswith('X')]
        assert len(x_calls) > 0, "Should have subcircuit calls with X prefix"

    def test_parameter_handling_in_pipeline(self):
        """Test that parameters are handled correctly throughout the pipeline."""
        parser = ASDLParser()
        fixtures_dir = Path(__file__).parent.parent.parent / "fixtures"
        inverter_path = fixtures_dir / "inverter.yml"
        asdl_file = parser.parse_file(str(inverter_path))
        
        generator = SPICEGenerator()
        spice_output = generator.generate(asdl_file)
        
        # Model parameters should be in model subcircuits with actual PDK device names
        assert 'MN D G S B nfet_03v3 L=0.5u W=4u nf=2' in spice_output
        assert 'MP D G S B pfet_03v3 L=0.5u W=5u nf=2' in spice_output
        
        # Verify parameter declarations in subcircuits
        assert '.param M=1' in spice_output
        
        # Instance parameters should be in subcircuit calls
        assert 'X_MP in out vdd vdd pmos_unit M=2' in spice_output
        assert 'X_MN in out vss vss nmos_unit M=2' in spice_output
        
        # Verify hierarchical structure
        assert '.subckt nmos_unit G D S B' in spice_output
        assert '.subckt pmos_unit G D S B' in spice_output
        assert '.subckt inverter in out vss vdd' in spice_output 

class TestParameterPropagation:
    """Test parameter propagation in module instances."""
    
    def test_module_instance_parameter_propagation(self):
        """Test that module instances correctly propagate parameters to subcircuit calls."""
        
        # Create ASDL with hierarchical parameter passing
        file_info = FileInfo(top_module="main_circuit", doc="Test parameter propagation", revision="v1.0", author="Test", date="2024-01-01")
        
        # Simple amplifier module with M parameter
        amplifier_module = Module(
            doc="Simple amplifier",
            ports={
                "in": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                "out": Port(dir=PortDirection.OUT, type=SignalType.VOLTAGE),
                "vdd": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
                "vss": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE)
            },
            parameters={"M": 1},  # Default amplification
            instances={
                "MP": Instance(
                    model="pmos_unit",
                    mappings={"G": "in", "D": "out", "S": "vdd", "B": "vdd"},
                    parameters={"M": "{M}*2"}  # Use module parameter
                ),
                "MN": Instance(
                    model="nmos_unit", 
                    mappings={"G": "in", "D": "out", "S": "vss", "B": "vss"},
                    parameters={"M": "{M}"}
                )
            }
        )
        
        # Main circuit that instantiates amplifier with specific parameters
        main_module = Module(
            doc="Main circuit with parameter overrides",
            ports={
                "input": Port(dir="in", type="voltage"),
                "output": Port(dir="out", type="voltage"),
                "vdd": Port(dir="in_out", type="voltage"),
                "vss": Port(dir="in_out", type="voltage")
            },
            parameters={"AMP_SIZE": 4},  # Top-level parameter
            instances={
                "AMP1": Instance(
                    model="amplifier",
                    mappings={"in": "input", "out": "output", "vdd": "vdd", "vss": "vss"},
                    parameters={"M": "{AMP_SIZE}"}  # Pass parameter to sub-module
                )
            }
        )
        
        # Device models
        nmos_model = DeviceModel(
            doc="NMOS transistor", 
            type=DeviceType.NMOS,
            ports=["G", "D", "S", "B"],
            device_line="MN {D} {G} {S} {B} nfet_03v3 W=1u L=0.18u",
            parameters={"M": 1}
        )
        
        pmos_model = DeviceModel(
            doc="PMOS transistor",
            type=DeviceType.PMOS, 
            ports=["G", "D", "S", "B"],
            device_line="MP {D} {G} {S} {B} pfet_03v3 W=1u L=0.18u",
            parameters={"M": 1}
        )
        
        asdl_file = ASDLFile(
            file_info=file_info,
            models={"nmos_unit": nmos_model, "pmos_unit": pmos_model},
            modules={"amplifier": amplifier_module, "main_circuit": main_module}
        )
        
        # Generate SPICE
        generator = SPICEGenerator()
        spice_output = generator.generate(asdl_file)
        
        # Verify parameter propagation in module instance call
        assert "X_AMP1 input output vdd vss amplifier M={AMP_SIZE}" in spice_output
        
        # Verify top-level parameter declaration
        assert ".param AMP_SIZE=4" in spice_output
        
        # Verify sub-module parameter declaration 
        assert ".param M=1" in spice_output
        
        # Verify that this is a hierarchical structure
        assert ".subckt amplifier in out vdd vss" in spice_output
        assert ".subckt main_circuit input output vdd vss" in spice_output 