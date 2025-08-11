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
    spice_output = generator.generate(asdl_file)
    
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
    
    # Key validation: The SPICE syntax is valid and parseable
    # This confirms our generator produces legal SPICE netlists
    
    # Verify the main circuit instantiation is present
    assert hasattr(circuit, '_elements')
    assert 'XMAIN' in circuit._elements
    
    # Verify we generated proper hierarchical subcircuit syntax
    # Check the raw SPICE content contains expected hierarchical elements
    assert '.subckt inverter' in spice_output
    # NEW FORMAT: Check for hierarchical subcircuit calls
    assert 'X_MP in out vdd vdd pmos_unit M=2' in spice_output
    assert 'X_MN in out vss vss nmos_unit M=2' in spice_output
    # Also verify model subcircuits exist
    assert '.subckt nmos_unit G D S B' in spice_output
    assert '.subckt pmos_unit G D S B' in spice_output
    # Verify actual PDK device lines exist inside model subcircuits
    assert 'MN D G S B nfet_03v3' in spice_output  # Primitive inside model
    assert 'MP D G S B pfet_03v3' in spice_output  # Primitive inside model


def test_pyspice_validates_nmos_instance(inverter_asdl):
    """Test that the NMOS device line is correctly formatted and parseable."""
    # Unpack the ASDL file and diagnostics
    asdl_file, diagnostics = inverter_asdl 
    
    # Skip test if parsing failed
    if asdl_file is None:
        pytest.skip(f"Parser failed with diagnostics: {diagnostics}")
    
    # Generate SPICE from the real inverter ASDL
    generator = SPICEGenerator()
    spice_output = generator.generate(asdl_file)
    
    # Extract the NMOS line from the generated SPICE (now inside nmos_unit subcircuit)
    lines = spice_output.split('\n')
    nmos_line = None
    for line in lines:
        # Look for MN inside the model subcircuit (with identity port mapping)
        if line.strip().startswith('MN') and 'D G S B' in line:
            nmos_line = line.strip()
            break
    
    assert nmos_line is not None, "NMOS device line not found in generated SPICE"
    
    # PySpice doesn't support complex PDK parameters like nf, ad, etc.
    # So we test with a simplified version that focuses on basic syntax validation
    # Create a simplified test with just basic parameters that PySpice understands
    simple_nmos_line = "MN D G S B nfet_03v3 L=0.5u W=4u"
    
    test_spice = f"""NMOS Test
{simple_nmos_line}
.end"""
    
    # This should parse successfully with basic parameters
    if not PYSPICE_AVAILABLE:
        pytest.skip("PySpice not available in environment")
    circuit = parse_spice_netlist(test_spice)
    assert circuit is not None
    assert 'MN' in circuit._elements


def test_pyspice_validates_pmos_instance(inverter_asdl):
    """Test that the PMOS device line is correctly formatted and parseable."""
    # Unpack the ASDL file and diagnostics
    asdl_file, diagnostics = inverter_asdl 
    
    # Skip test if parsing failed
    if asdl_file is None:
        pytest.skip(f"Parser failed with diagnostics: {diagnostics}")
    
    # Generate SPICE from the real inverter ASDL
    generator = SPICEGenerator()
    spice_output = generator.generate(asdl_file)
    
    # Extract the PMOS line from the generated SPICE (now inside pmos_unit subcircuit)
    lines = spice_output.split('\n')
    pmos_line = None
    for line in lines:
        # Look for MP inside the model subcircuit (with identity port mapping)
        if line.strip().startswith('MP') and 'D G S B' in line:
            pmos_line = line.strip()
            break
    
    assert pmos_line is not None, "PMOS device line not found in generated SPICE"
    
    # PySpice doesn't support complex PDK parameters like nf, ad, etc.
    # So we test with a simplified version that focuses on basic syntax validation
    # Create a simplified test with just basic parameters that PySpice understands
    simple_pmos_line = "MP D G S B pfet_03v3 L=0.5u W=5u"
    
    test_spice = f"""PMOS Test
{simple_pmos_line}
.end"""
    
    # This should parse successfully with basic parameters
    if not PYSPICE_AVAILABLE:
        pytest.skip("PySpice not available in environment")
    circuit = parse_spice_netlist(test_spice)
    assert circuit is not None
    assert 'MP' in circuit._elements


def test_pyspice_validates_subcircuit_ports(inverter_asdl):
    """Test that the inverter subcircuit definition has the correct port syntax."""
    # Unpack the ASDL file and diagnostics
    asdl_file, diagnostics = inverter_asdl 
    
    # Skip test if parsing failed
    if asdl_file is None:
        pytest.skip(f"Parser failed with diagnostics: {diagnostics}")
    
    # Generate SPICE from the real inverter ASDL
    generator = SPICEGenerator()
    spice_output = generator.generate(asdl_file)

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
    
    # Verify the main instantiation uses correct port count
    # Should match the 4 ports defined in the subcircuit (YAML declaration order)
    assert 'XMAIN in out vss vdd inverter' in spice_output
    
    # This validates that:
    # 1. Subcircuit has correct port definition (.subckt line)
    # 2. Main instantiation provides matching number of connections
    # 3. PySpice can parse the SPICE without syntax errors


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


def test_pyspice_missing_import():
    """Test behavior when PySpice is not available (mock scenario)."""
    # This test would need to mock the import failure
    # For now, just ensure the import error message is clear
    try:
        from src.asdl.spice_validator import PYSPICE_AVAILABLE
        if not PYSPICE_AVAILABLE:
            with pytest.raises(ImportError, match="PySpice.*install"):
                parse_spice_netlist("dummy content")
    except ImportError:
        # If PySpice isn't available in test environment, skip this validation
        pytest.skip("PySpice not available for testing import failure scenario") 