#!/usr/bin/env python3
"""
Manual test script for ASDL parser.
"""

from asdl import ASDLParser

def test_simple_circuit():
    """Test with a simple circuit that should work."""
    yaml_content = """
.version: "ASDL v1.0"
.top_module: simple_amp

.defaults: &DEF
  NMOS: &NMOS {model: nmos_unit, B: VSS}
  PMOS: &PMOS {model: pmos_unit, B: VDD}

modules:
  simple_amp:
    nets: 
      in: in
      out: out
      vdd: io
      vss: io
    parameters: 
      M: 4
    circuits:
      - name: MP_DRV
        model: pmos_unit
        S: vdd
        D: out
        G: in
        M: 2
      - name: MN_LOAD
        model: nmos_unit
        S: vss
        D: out
        G: vdd
        M: 1
"""
    
    parser = ASDLParser()
    
    try:
        asdl_file = parser.parse_string(yaml_content)
        print("✅ Successfully parsed ASDL file!")
        print(f"Version: {asdl_file.version}")
        print(f"Top module: {asdl_file.top_module}")
        print(f"Modules: {list(asdl_file.modules.keys())}")
        
        # Check the simple_amp module
        simple_amp = asdl_file.modules["simple_amp"]
        print(f"\nSimple amp module:")
        print(f"  Nets: {simple_amp.nets}")
        print(f"  Parameters: {simple_amp.parameters}")
        print(f"  Circuits count: {len(simple_amp.circuits)}")
        
        for i, circuit in enumerate(simple_amp.circuits):
            print(f"  Circuit {i}: {circuit.name} ({circuit.model})")
            print(f"    Parameters: {circuit.parameters}")
    
    except Exception as e:
        print(f"❌ Error parsing: {e}")


if __name__ == "__main__":
    test_simple_circuit() 