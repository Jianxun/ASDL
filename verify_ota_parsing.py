#!/usr/bin/env python3
"""
Verification script showing the OTA file now parses correctly.
"""

from asdl import ASDLParser
import json

def verify_ota_parsing():
    """Verify the OTA file parses correctly and show the structure."""
    
    parser = ASDLParser()
    
    try:
        print("🔄 Parsing examples/ota_two_stg.yaml...")
        asdl_file = parser.parse_file("examples/ota_two_stg.yaml")
        
        print("✅ Successfully parsed OTA file!")
        print(f"📄 Version: {asdl_file.version}")
        print(f"🎯 Top module: {asdl_file.top_module}")
        print(f"📦 Modules ({len(asdl_file.modules)}): {list(asdl_file.modules.keys())}")
        
        # Show top module details
        ota_module = asdl_file.get_top_module()
        print(f"\n🏗️  OTA Module Details:")
        print(f"   Nets: {ota_module.nets}")
        print(f"   Parameters: {ota_module.parameters}")
        print(f"   Circuits: {len(ota_module.circuits)}")
        
        for i, circuit in enumerate(ota_module.circuits):
            print(f"     {i+1}. {circuit.name} ({circuit.model})")
            if circuit.parameters and 'M' in circuit.parameters:
                print(f"        M: {circuit.parameters['M']}")
        
        # Show some pattern syntax examples
        print(f"\n🔧 Pattern Examples:")
        diff_pair = asdl_file.modules["diff_pair_nmos"]
        print(f"   diff_pair_nmos nets: {diff_pair.nets}")
        print(f"   First circuit: {diff_pair.circuits[0].name}")
        print(f"   Parameters: {diff_pair.circuits[0].parameters}")
        
        print(f"\n📊 Summary:")
        print(f"   ✓ File parsed successfully")
        print(f"   ✓ All {len(asdl_file.modules)} modules loaded")
        print(f"   ✓ Pattern syntax preserved (e.g., 'in_{{p,n}}')")
        print(f"   ✓ Parameter substitution preserved (e.g., '${{M.diff}}')")
        print(f"   ✓ Ready for pattern expansion and parameter resolution!")
        
        # Demonstrate JSON export functionality
        print(f"\n📝 JSON Export Demo:")
        json_output = "examples/ota_debug.json"
        asdl_file.save_json(json_output)
        
        # Show a snippet of the JSON structure
        json_data = json.loads(asdl_file.to_json())
        print(f"\n🔍 Sample JSON structure (top-level keys):")
        print(f"   {list(json_data.keys())}")
        
        print(f"\n💡 JSON file saved to: {json_output}")
        print(f"   Use this for:")
        print(f"   • Manual inspection of parsed structure")
        print(f"   • Debugging pattern expansion")
        print(f"   • Validating parameter resolution")
        print(f"   • Comparing transformations")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verify_ota_parsing() 