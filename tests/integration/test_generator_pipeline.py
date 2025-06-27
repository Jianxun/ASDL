"""
Integration test for the complete ASDL pipeline: Parser -> Elaborator -> Generator

This test verifies that the refactored generator works with real ASDL files
through the complete pipeline.
"""

import pytest
from pathlib import Path

from src.asdl.parser import ASDLParser
from src.asdl.elaborator import Elaborator  
from src.asdl.generator import SPICEGenerator


class TestGeneratorPipeline:
    """Integration tests for the complete ASDL processing pipeline."""

    def test_diff_pair_nmos_pipeline(self):
        """Test complete pipeline with diff_pair_nmos.yml fixture."""
        
        # Get path to test fixture
        fixture_path = Path(__file__).parent.parent / "fixtures" / "diff_pair_nmos.yml"
        assert fixture_path.exists(), f"Test fixture not found: {fixture_path}"
        
        # Step 1: Parse the ASDL file
        parser = ASDLParser()
        parse_result = parser.parse_file(str(fixture_path))
        
        # Handle parser result (could be tuple with diagnostics)
        if isinstance(parse_result, tuple):
            asdl_file, parse_diagnostics = parse_result
            print(f"Parse diagnostics: {len(parse_diagnostics)}")
            for diag in parse_diagnostics:
                print(f"  {diag}")
        else:
            asdl_file = parse_result
            parse_diagnostics = []
        
        # Verify parsing succeeded
        assert asdl_file is not None, "Parser returned None"
        assert asdl_file.file_info is not None, "File info missing"
        assert asdl_file.models is not None, "Models missing"
        assert asdl_file.modules is not None, "Modules missing"
        
        print(f"✅ Parsing successful - {len(asdl_file.models)} models, {len(asdl_file.modules)} modules")
        
        # Step 2: Elaborate patterns
        elaborator = Elaborator()
        elaborated, elab_diagnostics = elaborator.elaborate(asdl_file)
        
        print(f"Elaboration diagnostics: {len(elab_diagnostics)}")
        for diag in elab_diagnostics:
            print(f"  {diag}")
        
        # Verify elaboration succeeded
        assert elaborated is not None, "Elaborator returned None"
        assert elaborated.file_info is not None, "Elaborated file info missing"
        
        print(f"✅ Elaboration successful")
        
        # Step 3: Generate SPICE
        generator = SPICEGenerator()
        spice_output = generator.generate(elaborated)
        
        assert spice_output is not None, "Generator returned None"
        assert len(spice_output.strip()) > 0, "Generator returned empty output"
        
        print(f"✅ Generation successful - {len(spice_output.splitlines())} lines generated")
        
        # Basic SPICE format verification
        lines = spice_output.splitlines()
        
        # Should have header comments
        assert any("SPICE netlist generated" in line for line in lines), "Missing SPICE header"
        
        # Should have model subcircuits
        assert any(".subckt nmos_unit" in line for line in lines), "Missing nmos_unit subcircuit"
        assert any(".subckt resistor_unit" in line for line in lines), "Missing resistor_unit subcircuit"
        
        # Should have main module subcircuit
        assert any(".subckt diff_pair_nmos" in line for line in lines), "Missing main module subcircuit"
        
        # Should have .end statement
        assert any(".end" in line for line in lines), "Missing .end statement"
        
        # Print the generated SPICE for manual inspection
        print("\n" + "="*60)
        print("GENERATED SPICE NETLIST:")
        print("="*60)
        print(spice_output)
        print("="*60)

    def test_simple_resistor_pipeline(self):
        """Test pipeline with a simple in-memory ASDL structure."""
        
        from src.asdl.data_structures import ASDLFile, FileInfo, DeviceModel, PrimitiveType, Module, Instance
        
        # Create a simple ASDL structure in memory
        file_info = FileInfo(
            top_module="simple_test",
            doc="Simple resistor test circuit",
            revision="1.0",
            author="Test Suite",
            date="2024-01-01"
        )
        
        # Simple resistor model using new device_line approach
        resistor_model = DeviceModel(
            type=PrimitiveType.SPICE_DEVICE,
            ports=["plus", "minus"],
            device_line="R {plus} {minus} {value}",
            doc="Simple resistor model",
            parameters={"value": "1k"}
        )
        
        # Simple resistor instance
        resistor_instance = Instance(
            model="simple_resistor",
            mappings={"plus": "vin", "minus": "vout"},
            parameters={"value": "2k"}  # Override default
        )
        
        # Simple module
        test_module = Module(
            doc="Simple test module",
            ports={},
            instances={"R1": resistor_instance}
        )
        
        # Create ASDL file
        asdl_file = ASDLFile(
            file_info=file_info,
            models={"simple_resistor": resistor_model},
            modules={"simple_test": test_module}
        )
        
        # Test elaboration (should be pass-through for simple case)
        elaborator = Elaborator()
        elaborated, diagnostics = elaborator.elaborate(asdl_file)
        
        assert elaborated is not None, "Elaboration failed"
        assert len(diagnostics) == 0, f"Unexpected diagnostics: {diagnostics}"
        
        # Test generation
        generator = SPICEGenerator()
        spice_output = generator.generate(elaborated)
        
        assert spice_output is not None, "Generation failed"
        
        # Verify key elements
        assert ".subckt simple_resistor plus minus" in spice_output
        assert ".param value=1k" in spice_output  # Model default
        assert "R plus minus {value}" in spice_output  # Device line with ports substituted
        assert "X_R1 vin vout simple_resistor value=2k" in spice_output  # Instance with override
        
        print(f"✅ Simple resistor pipeline test successful")
        print("Generated SPICE:")
        print(spice_output) 