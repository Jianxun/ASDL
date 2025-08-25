"""
Test PySpice integration with SPICE generator using real ASDL files.

These tests validate that our generated SPICE netlists can be successfully
parsed by PySpice and contain the expected circuit elements.
"""

import pytest
from pathlib import Path
from src.asdl.parser import ASDLParser
from src.asdl.generator import SPICEGenerator
from src.asdl.spice_validator import parse_spice_netlist
from src.asdl.spice_validator import PYSPICE_AVAILABLE


@pytest.fixture
def inverter_asdl():
    """Load the inverter ASDL test fixture."""
    parser = ASDLParser()
    fixtures_dir = Path(__file__).parent.parent.parent / "fixtures"
    inverter_path = fixtures_dir / "inverter.yml"
    asdl_file, diagnostics = parser.parse_file(str(inverter_path))
    
    # Return tuple for compatibility with existing tests
    return asdl_file, diagnostics


def test_pyspice_parses_inverter_netlist(inverter_asdl):
    """Test that PySpice can parse the generated inverter SPICE netlist."""
    from pathlib import Path
    
    # Unpack the ASDL file and diagnostics
    asdl_file, diagnostics = inverter_asdl 
    
    # Skip test if parsing failed
    if asdl_file is None:
        pytest.skip(f"Parser failed with diagnostics: {diagnostics}")
    
    # Generate SPICE from the real inverter ASDL
    generator = SPICEGenerator()
    spice_output, diagnostics = generator.generate(asdl_file)
    
    print("Generated SPICE:")
    print(spice_output)
    
    # Save results for manual inspection
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    
    # Save ASDL data using package serializer (handles Enums/Paths)
    from src.asdl.serialization import asdl_to_json_string
    (results_dir / "inverter_asdl.json").write_text(
        asdl_to_json_string(asdl_file), encoding="utf-8"
    )
    
    # Save generated SPICE netlist
    with open(results_dir / "inverter_netlist.spice", "w") as f:
        f.write(spice_output)
    
    print(f"Saved inspection files to: {results_dir}")
    print(f"- ASDL JSON: {results_dir / 'inverter_asdl.json'}")
    print(f"- SPICE Netlist: {results_dir / 'inverter_netlist.spice'}")
    
    # Parse with PySpice - should not raise an exception
    if not PYSPICE_AVAILABLE:
        pytest.skip("PySpice not available in environment")
    circuit = parse_spice_netlist(spice_output)
    
    # Verify circuit parses successfully 
    assert circuit is not None
    
    # Verify the main circuit instantiation is present
    assert hasattr(circuit, '_elements')
    assert 'XMAIN' in circuit._elements
    
    # Verify we generated proper hierarchical subcircuit syntax
    # Expected ports from inverter.yml: in, out, vss, vdd (YAML declaration order)
    assert '.subckt inverter in out vss vdd' in spice_output


def test_pyspice_validates_subcircuit_ports(inverter_asdl):
    """Test that the inverter subcircuit definition has the correct port syntax."""
    # Unpack the ASDL file and diagnostics
    asdl_file, diagnostics = inverter_asdl 
    
    # Skip test if parsing failed
    if asdl_file is None:
        pytest.skip(f"Parser failed with diagnostics: {diagnostics}")
    
    # Generate SPICE from the real inverter ASDL
    generator = SPICEGenerator()
    spice_output, diagnostics = generator.generate(asdl_file)

    # Parse with PySpice to ensure it's syntactically valid
    if not PYSPICE_AVAILABLE:
        pytest.skip("PySpice not available in environment")
    circuit = parse_spice_netlist(spice_output)

    # Verify the main circuit has the subcircuit instantiation
    assert hasattr(circuit, '_elements')
    assert 'XMAIN' in circuit._elements

    # Verify the subcircuit definition syntax in raw SPICE
    # Expected ports from inverter.yml: in, out, vss, vdd (YAML declaration order)
    assert '.subckt inverter in out vss vdd' in spice_output


def test_pyspice_validation_catches_malformed_spice():
    """Test that PySpice parsing catches malformed SPICE syntax."""
    # Intentionally malformed SPICE
    bad_spice = """Bad Circuit
R1 node1 node2  # Missing model and value
.end
"""
    
    # Should raise ValueError when parsing fails
    if not PYSPICE_AVAILABLE:
        pytest.skip("PySpice not available in environment")
    with pytest.raises(ValueError, match="SPICE.*failed"):
        parse_spice_netlist(bad_spice)

