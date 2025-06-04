#!/usr/bin/env python3
"""
Script to demonstrate JSON dump functionality for ASDL parsing.
This shows how the parsed structure can be exported to JSON for manual inspection.
"""

from asdl import ASDLParser
from pathlib import Path

def main():
    """Parse the OTA file and dump it to JSON for inspection."""
    
    parser = ASDLParser()
    
    print("🔄 Parsing and dumping OTA file to JSON...")
    
    try:
        # Parse and dump in one step
        asdl_file = parser.parse_and_dump(
            filepath=Path("examples/ota_two_stg.yaml"),
            output_json="examples/ota_two_stg_parsed.json"
        )
        
        print(f"\n📊 JSON dump complete!")
        print(f"   📁 Original: examples/ota_two_stg.yaml")
        print(f"   📄 JSON output: examples/ota_two_stg_parsed.json")
        
        # Show a specific module structure
        print(f"\n🔍 Sample Module Structure (diff_pair_nmos):")
        diff_pair = asdl_file.modules["diff_pair_nmos"]
        
        # Print as pretty JSON
        import json
        print(json.dumps(diff_pair.to_dict() if hasattr(diff_pair, 'to_dict') else {
            'name': diff_pair.name,
            'nets': diff_pair.nets,
            'parameters': diff_pair.parameters,
            'circuits': [c.__dict__ for c in diff_pair.circuits],
            'notes': diff_pair.notes
        }, indent=2))
        
        print(f"\n✅ JSON dump functionality working correctly!")
        print(f"💡 Use the JSON file to:")
        print(f"   • Inspect parsed structure manually")
        print(f"   • Debug pattern expansion issues")
        print(f"   • Validate parameter resolution")
        print(f"   • Compare before/after transformations")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 