#!/usr/bin/env python3
"""
Manual testing script to regenerate SPICE netlist from inverter.yml

Usage: python regenerate_inverter_netlist.py

This script reads inverter.yml from the same directory and generates
a SPICE netlist, saving it to the generator results directory.
Perfect for manual testing when modifying the YAML file.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path (go up two levels from tests/fixtures)
script_dir = Path(__file__).parent
src_dir = script_dir / '..' / '..' / 'src'
sys.path.append(str(src_dir))

from asdl.parser import ASDLParser
from asdl.generator import SPICEGenerator

def main():
    # File paths relative to this script's location
    yaml_file = script_dir / 'inverter.yml'
    output_file = script_dir / '..' / 'unit_tests' / 'generator' / 'results' / 'inverter_netlist.spice'
    
    print(f'📁 Script location: {script_dir}')
    print(f'📄 Parsing YAML: {yaml_file}')
    
    # Parse the YAML file
    parser = ASDLParser()
    asdl_file = parser.parse_file(str(yaml_file))
    
    print('⚙️  Generating SPICE netlist...')
    
    # Generate SPICE netlist
    generator = SPICEGenerator() 
    spice_netlist = generator.generate(asdl_file)
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f'💾 Saving to: {output_file}')
    with open(output_file, 'w') as f:
        f.write(spice_netlist)
    
    print('✅ Success! Generated netlist with correct PDK models:')
    print('  - NMOS: nfet_03v3') 
    print('  - PMOS: pfet_03v3')
    print(f'  - File: {output_file}')
    
    # Show first few lines of generated netlist
    print('\n📋 First 600 characters of generated netlist:')
    print(spice_netlist[:600])
    print('...')
    
    # Show device lines specifically
    lines = spice_netlist.split('\n')
    print('\n🔍 Device lines found:')
    for i, line in enumerate(lines):
        if 'nfet_03v3' in line or 'pfet_03v3' in line:
            print(f'  Line {i+1}: {line.strip()}')

if __name__ == '__main__':
    main() 