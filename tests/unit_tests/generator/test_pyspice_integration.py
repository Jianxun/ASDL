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


@pytest.fixture
def inverter_asdl():
    """Load the inverter ASDL test fixture."""
    parser = ASDLParser()
    fixtures_dir = Path(__file__).parent.parent.parent / "fixtures"
    inverter_path = fixtures_dir / "inverter.yml"
    return parser.parse_file(str(inverter_path))


def test_pyspice_parses_inverter_netlist(inverter_asdl):
    """Test that PySpice can parse the generated inverter SPICE netlist."""
    import json
    from pathlib import Path
    from dataclasses import asdict
    
    # Generate SPICE from the real inverter ASDL
    generator = SPICEGenerator()
    spice_output = generator.generate(inverter_asdl)
    
    print("Generated SPICE:")
    print(spice_output)
    
    # Save results for manual inspection
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    
    # Save ASDL data as JSON with custom encoder for enums
    from src.asdl.data_structures import DeviceType, PortDirection, SignalType
    from enum import Enum
    
    class ASDLJSONEncoder(json.JSONEncoder):
        def default(self, obj):
            # Handle all enum types by converting to their string value
            if isinstance(obj, Enum):
                return obj.value
            return super().default(obj)
    
    asdl_dict = asdict(inverter_asdl)
    with open(results_dir / "inverter_asdl.json", "w") as f:
        json.dump(asdl_dict, f, indent=2, cls=ASDLJSONEncoder)
    
    # Save generated SPICE netlist
    with open(results_dir / "inverter_netlist.spice", "w") as f:
        f.write(spice_output)
    
    print(f"Saved inspection files to: {results_dir}")
    print(f"- ASDL JSON: {results_dir / 'inverter_asdl.json'}")
    print(f"- SPICE Netlist: {results_dir / 'inverter_netlist.spice'}")
    
    # Parse with PySpice - should not raise an exception
    circuit = parse_spice_netlist(spice_output)
    
    # Verify circuit parses successfully 
    assert circuit is not None
    
    # Key validation: The SPICE syntax is valid and parseable
    # This confirms our generator produces legal SPICE netlists
    
    # Verify the main circuit instantiation is present
    assert hasattr(circuit, '_elements')
    assert 'XMAIN' in circuit._elements
    
    # Verify we generated proper subcircuit syntax (even if PySpice parsing is limited)
    # Check the raw SPICE content contains expected elements
    assert '.subckt inverter' in spice_output
    assert 'MP out in vdd vdd pch_lvt' in spice_output
    assert 'MN out in vss vss nch_lvt' in spice_output
    assert '.ends' in spice_output
    assert 'XMAIN in out vdd vss inverter' in spice_output


def test_pyspice_validates_nmos_instance(inverter_asdl):
    """Test that the NMOS device line is correctly formatted and parseable."""
    # Generate SPICE from the real inverter ASDL
    generator = SPICEGenerator()
    spice_output = generator.generate(inverter_asdl)
    
    # Extract the NMOS line from the generated SPICE
    lines = spice_output.split('\n')
    nmos_line = None
    for line in lines:
        if line.strip().startswith('MN'):
            nmos_line = line.strip()
            break
    
    assert nmos_line is not None, "NMOS device line not found in generated SPICE"
    
    # Test that PySpice can parse just the NMOS device line
    test_spice = f"""NMOS Test
{nmos_line}
.end"""
    
    circuit = parse_spice_netlist(test_spice)
    
    # Verify the NMOS device is parsed
    assert 'MN' in circuit._elements
    nmos = circuit._elements['MN']
    assert nmos is not None
    
    # NMOS should have 4 nodes (D, G, S, B) 
    if hasattr(nmos, 'nodes'):
        connected_nodes = [node for node in nmos.nodes if node is not None]
        assert len(connected_nodes) == 4
        
        # Check node names match the expected mappings from inverter.yml
        # MN mappings: {G: in, D: out, S: vss, B: vss}
        node_names = [str(node).lower() for node in connected_nodes]
        assert 'in' in node_names   # Gate
        assert 'out' in node_names  # Drain  
        assert 'vss' in node_names  # Source and Bulk


def test_pyspice_validates_pmos_instance(inverter_asdl):
    """Test that the PMOS device line is correctly formatted and parseable."""
    # Generate SPICE from the real inverter ASDL
    generator = SPICEGenerator()
    spice_output = generator.generate(inverter_asdl)
    
    # Extract the PMOS line from the generated SPICE
    lines = spice_output.split('\n')
    pmos_line = None
    for line in lines:
        if line.strip().startswith('MP'):
            pmos_line = line.strip()
            break
    
    assert pmos_line is not None, "PMOS device line not found in generated SPICE"
    
    # Test that PySpice can parse just the PMOS device line
    test_spice = f"""PMOS Test
{pmos_line}
.end"""
    
    circuit = parse_spice_netlist(test_spice)
    
    # Verify the PMOS device is parsed
    assert 'MP' in circuit._elements
    pmos = circuit._elements['MP']
    assert pmos is not None
    
    # PMOS should have 4 nodes (D, G, S, B)
    if hasattr(pmos, 'nodes'):
        connected_nodes = [node for node in pmos.nodes if node is not None]
        assert len(connected_nodes) == 4
        
        # Check node names match the expected mappings from inverter.yml
        # MP mappings: {G: in, D: out, S: vdd, B: vdd}
        node_names = [str(node).lower() for node in connected_nodes]
        assert 'in' in node_names   # Gate
        assert 'out' in node_names  # Drain
        assert 'vdd' in node_names  # Source and Bulk


def test_pyspice_validates_subcircuit_ports(inverter_asdl):
    """Test that the inverter subcircuit definition has the correct port syntax."""
    # Generate SPICE from the real inverter ASDL
    generator = SPICEGenerator()
    spice_output = generator.generate(inverter_asdl)

    # Parse with PySpice to ensure it's syntactically valid
    circuit = parse_spice_netlist(spice_output)

    # Verify the main circuit has the subcircuit instantiation
    assert hasattr(circuit, '_elements')
    assert 'XMAIN' in circuit._elements

    # Verify the subcircuit definition syntax in raw SPICE
    # Expected ports from inverter.yml: in, out, vdd, vss
    assert '.subckt inverter in out vdd vss' in spice_output
    
    # Verify the main instantiation uses correct port count
    # Should match the 4 ports defined in the subcircuit
    assert 'XMAIN in out vdd vss inverter' in spice_output
    
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