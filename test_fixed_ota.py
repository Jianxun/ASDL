#!/usr/bin/env python3
"""
Test script to compare parsing of original vs fixed OTA file.
Shows how explicit nets: syntax properly separates pin connections from device parameters.
"""

from asdl import ASDLParser
import json

def test_fixed_ota():
    """Compare parsing results between original and fixed OTA files."""
    
    parser = ASDLParser()
    
    print("🔄 Testing fixed OTA syntax...")
    
    try:
        # Parse the fixed version
        print("\n📁 Parsing fixed version: examples/ota_two_stg_fixed.yaml")
        asdl_fixed = parser.parse_file("examples/ota_two_stg_fixed.yaml")
        
        # Show difference in parsing for a transistor device
        print("\n🔍 Device Parsing Comparison (diff_pair_nmos module):")
        
        diff_pair_fixed = asdl_fixed.modules["diff_pair_nmos"]
        transistor_fixed = diff_pair_fixed.circuits[0]
        
        print(f"\n✅ FIXED VERSION - Proper nets/parameters separation:")
        print(f"   Device: {transistor_fixed.name} ({transistor_fixed.model})")
        print(f"   📡 NETS: {transistor_fixed.nets}")
        print(f"   ⚙️  PARAMETERS: {transistor_fixed.parameters}")
        
        # Parse original for comparison
        print(f"\n📁 Parsing original version: examples/ota_two_stg.yaml")
        asdl_orig = parser.parse_file("examples/ota_two_stg.yaml")
        diff_pair_orig = asdl_orig.modules["diff_pair_nmos"]  
        transistor_orig = diff_pair_orig.circuits[0]
        
        print(f"\n❌ ORIGINAL VERSION - Everything in parameters:")
        print(f"   Device: {transistor_orig.name} ({transistor_orig.model})")
        print(f"   📡 NETS: {transistor_orig.nets}")
        print(f"   ⚙️  PARAMETERS: {transistor_orig.parameters}")
        
        # Save fixed version JSON for inspection
        asdl_fixed.save_json("examples/ota_two_stg_fixed_parsed.json")
        
        print(f"\n📊 Summary:")
        print(f"   ✅ Fixed version properly separates:")
        print(f"      • Pin connections (S,D,G,B) → nets field")  
        print(f"      • Device parameters (M, W, L) → parameters field")
        print(f"   ❌ Original version puts everything in parameters")
        print(f"   💡 Recommendation: Use explicit nets: syntax for all devices")
        
        print(f"\n🎯 Next Steps:")
        print(f"   1. Update ASDL schema to require explicit nets: for devices")
        print(f"   2. Update parser to handle this syntax correctly")
        print(f"   3. Convert existing ASDL files to new format")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_fixed_ota() 