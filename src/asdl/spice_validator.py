"""
SPICE netlist parser using PySpice.

Simple utility to parse SPICE netlists into PySpice.Circuit objects for validation.
"""

import tempfile
import os

try:
    from PySpice.Spice.Netlist import Circuit
    from PySpice.Spice.Parser import SpiceParser
    PYSPICE_AVAILABLE = True
except ImportError:
    PYSPICE_AVAILABLE = False


def parse_spice_netlist(spice_content: str) -> Circuit:
    """
    Parse SPICE netlist content into a PySpice.Circuit object.
    
    Args:
        spice_content: SPICE netlist as string
        
    Returns:
        PySpice.Circuit object
        
    Raises:
        ImportError: If PySpice is not available
        ValueError: If SPICE parsing fails
    """
    if not PYSPICE_AVAILABLE:
        raise ImportError(
            "PySpice is not available. Install with: pip install PySpice>=1.5.0"
        )
    
    try:
        # Create a temporary file for PySpice to parse
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cir', delete=False) as f:
            f.write(spice_content)
            temp_filename = f.name
        
        try:
            # Parse the SPICE file
            parser = SpiceParser(path=temp_filename)
            circuit = parser.build_circuit()
            return circuit
        finally:
            # Clean up temporary file
            os.unlink(temp_filename)
            
    except Exception as e:
        # Provide more specific error messages
        if "syntax error" in str(e).lower():
            raise ValueError(f"SPICE syntax error: {e}")
        elif "unknown" in str(e).lower():
            raise ValueError(f"Unknown SPICE element: {e}")
        else:
            raise ValueError(f"SPICE parsing failed: {e}") 