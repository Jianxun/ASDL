#!/usr/bin/env python3
"""
Compile the unified architecture demo ASDL file to SPICE.

This script demonstrates the unified ASDL architecture where:
- Primitive modules (with spice_template) generate inline SPICE
- Hierarchical modules (with instances) generate .subckt definitions
- PDK includes are automatically generated for primitive modules
"""

import sys
import os
from pathlib import Path

# Add the src directory to the path so we can import asdl modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from asdl.parser import ASDLParser
from asdl.generator import SPICEGenerator
from asdl.diagnostics import DiagnosticSeverity

def main():
    """Compile the unified architecture demo to SPICE."""
    
    # File paths
    asdl_file = Path(__file__).parent / "unified_architecture_demo.asdl"
    spice_file = Path(__file__).parent / "unified_architecture_demo.spice"
    
    print(f"📁 Compiling ASDL file: {asdl_file}")
    print(f"📁 Output SPICE file: {spice_file}")
    print()
    
    # Parse the ASDL file
    print("🔍 Parsing ASDL file...")
    parser = ASDLParser()
    
    try:
        asdl_design, diagnostics = parser.parse_file(str(asdl_file))
    except FileNotFoundError:
        print(f"❌ Error: File not found: {asdl_file}")
        return 1
    except Exception as e:
        print(f"❌ Parse error: {e}")
        return 1
    
    # Check for parsing errors
    if diagnostics:
        print("📋 Parser diagnostics:")
        for diag in diagnostics:
            severity = "🔴" if diag.severity == DiagnosticSeverity.ERROR else "🟡"
            print(f"  {severity} {diag.title}: {diag.details}")
            if diag.location:
                print(f"      Location: {diag.location}")
    
    if not asdl_design:
        print("❌ Failed to parse ASDL file")
        return 1
    
    # Show what we parsed
    print(f"✅ Successfully parsed ASDL design")
    print(f"   📄 Top module: {asdl_design.file_info.top_module}")
    print(f"   📄 Description: {asdl_design.file_info.doc}")
    print(f"   📦 Modules: {len(asdl_design.modules)}")
    
    # Categorize modules
    primitive_modules = []
    hierarchical_modules = []
    
    for name, module in asdl_design.modules.items():
        if module.spice_template:
            primitive_modules.append(name)
        elif module.instances:
            hierarchical_modules.append(name)
        else:
            print(f"⚠️  Warning: Module {name} has neither spice_template nor instances")
    
    print(f"   🔧 Primitive modules: {len(primitive_modules)} - {', '.join(primitive_modules)}")
    print(f"   🏗️  Hierarchical modules: {len(hierarchical_modules)} - {', '.join(hierarchical_modules)}")
    print()
    
    # Generate SPICE
    print("🔧 Generating SPICE netlist...")
    generator = SPICEGenerator()
    
    try:
        spice_netlist = generator.generate(asdl_design)
    except Exception as e:
        print(f"❌ Generation error: {e}")
        return 1
    
    # Write SPICE file
    print(f"💾 Writing SPICE netlist to {spice_file}")
    try:
        with open(spice_file, 'w') as f:
            f.write(spice_netlist)
    except Exception as e:
        print(f"❌ Write error: {e}")
        return 1
    
    print("✅ Successfully generated SPICE netlist!")
    print()
    
    # Show some statistics about the generated SPICE
    lines = spice_netlist.split('\n')
    include_lines = [line for line in lines if line.strip().startswith('.include')]
    subckt_lines = [line for line in lines if line.strip().startswith('.subckt')]
    device_lines = [line for line in lines if any(line.strip().startswith(prefix) for prefix in ['MN', 'MP', 'R', 'C', 'X_'])]
    
    print("📊 Generated SPICE statistics:")
    print(f"   📄 Total lines: {len(lines)}")
    print(f"   📦 PDK includes: {len(include_lines)}")
    print(f"   🏗️  Subcircuits: {len(subckt_lines)}")
    print(f"   🔧 Device instances: {len(device_lines)}")
    print()
    
    if include_lines:
        print("📦 PDK includes found:")
        for line in include_lines:
            print(f"   {line.strip()}")
        print()
    
    if subckt_lines:
        print("🏗️  Subcircuits found:")
        for line in subckt_lines:
            print(f"   {line.strip()}")
        print()
    
    print(f"🎉 Compilation complete! Check {spice_file} for the generated netlist.")
    return 0

if __name__ == "__main__":
    exit(main())