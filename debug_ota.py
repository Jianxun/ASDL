#!/usr/bin/env python3
"""
Debug script to identify specific YAML issues in OTA file.
"""

import yaml
from asdl import ASDLParser

def test_problematic_patterns():
    """Test the specific patterns causing issues."""
    
    # Test 1: Pattern in flow mapping keys (PROBLEMATIC)
    print("=== Test 1: Original problematic syntax ===")
    problematic_yaml = """
modules:
  diff_pair_nmos:
    nets: {in_{p,n}: in, out_{p,n}: out, tail: io}
"""
    
    try:
        data = yaml.load(problematic_yaml, Loader=yaml.FullLoader)
        print("✅ Parsed successfully!")
        print(f"Result: {data}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Quoted pattern keys (SHOULD WORK)
    print("\n=== Test 2: Fixed with quoted keys ===")
    fixed_yaml = """
modules:
  diff_pair_nmos:
    nets: {"in_{p,n}": in, "out_{p,n}": out, tail: io}
"""
    
    try:
        data = yaml.load(fixed_yaml, Loader=yaml.FullLoader)
        print("✅ Parsed successfully!")
        print(f"Result: {data}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Parameter substitution (PROBLEMATIC)
    print("\n=== Test 3: Parameter substitution original ===")
    param_yaml = """
modules:
  test:
    circuits:
      - {name: MN1, M: ${M}}
"""
    
    try:
        data = yaml.load(param_yaml, Loader=yaml.FullLoader)
        print("✅ Parsed successfully!")
        print(f"Result: {data}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Quoted parameter substitution (SHOULD WORK)
    print("\n=== Test 4: Quoted parameter substitution ===")
    param_fixed_yaml = """
modules:
  test:
    circuits:
      - {name: MN1, M: "${M}"}
"""
    
    try:
        data = yaml.load(param_fixed_yaml, Loader=yaml.FullLoader)
        print("✅ Parsed successfully!")
        print(f"Result: {data}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_problematic_patterns() 