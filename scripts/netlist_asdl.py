#!/usr/bin/env python3
"""
ASDL to SPICE Netlister Script

Usage:
    python scripts/netlist_asdl.py input.yml [output.spice]
    python scripts/netlist_asdl.py @input.yml  # Auto-generate output filename

Integrates the full ASDL pipeline:
1. Parse ASDL YAML file
2. Elaborate patterns (differential, bus, etc.)
3. Generate SPICE netlist
4. Save to output file
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from asdl.parser import ASDLParser
from asdl.elaborator import Elaborator
from asdl.generator import SPICEGenerator


def display_diagnostics(diagnostics, stage_name: str = ""):
    """Display diagnostics with proper formatting."""
    if not diagnostics:
        return
    
    stage_prefix = f"{stage_name}: " if stage_name else ""
    for diag in diagnostics:
        print(f"❌ {stage_prefix}{diag}")


def netlist_asdl_file(input_file: str, output_file: Optional[str] = None, verbose: bool = False):
    """
    Netlist an ASDL file to SPICE format.
    
    Args:
        input_file: Path to ASDL YAML file
        output_file: Output SPICE file path (auto-generated if None)
        verbose: Enable verbose output
    
    Returns:
        Path to generated SPICE file
    """
    input_path = Path(input_file)
    
    # Validate input file
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Auto-generate output filename if not provided
    if output_file is None:
        output_path = input_path.with_suffix('.spice')
    else:
        output_path = Path(output_file)
    
    if verbose:
        print(f"🔄 Processing ASDL file: {input_path}")
        print(f"📝 Output SPICE file: {output_path}")
    
    # Step 1: Parse ASDL file
    if verbose:
        print("📖 Step 1: Parsing ASDL file...")
    
    parser = ASDLParser()
    parse_result = parser.parse_file(str(input_path))
    
    # Handle parser result (could be tuple with diagnostics)
    if isinstance(parse_result, tuple):
        asdl_file, parse_diagnostics = parse_result
        if parse_diagnostics:
            # Check for any errors that would prevent continuation
            error_diagnostics = [d for d in parse_diagnostics if d.severity.name == 'ERROR']
            if error_diagnostics:
                display_diagnostics(error_diagnostics, "Parse Error")
                raise ValueError("Parsing failed due to errors")
            
            # Display warnings/info if verbose
            if verbose:
                warning_diagnostics = [d for d in parse_diagnostics if d.severity.name != 'ERROR']
                if warning_diagnostics:
                    display_diagnostics(warning_diagnostics, "Parse Warning")
    else:
        asdl_file = parse_result
        parse_diagnostics = []
    
    if asdl_file is None:
        raise ValueError("Parsing failed - no ASDL file returned")
    
    if verbose:
        print(f"✅ Parsed successfully:")
        print(f"   - Top module: {asdl_file.file_info.top_module}")
        print(f"   - Models: {len(asdl_file.models)}")
        print(f"   - Modules: {len(asdl_file.modules)}")
    
    # Step 2: Elaborate patterns
    if verbose:
        print("🔀 Step 2: Elaborating patterns...")
    
    elaborator = Elaborator()
    elaborated_file, elab_diagnostics = elaborator.elaborate(asdl_file)
    
    if elab_diagnostics:
        # Check for any errors that would prevent continuation
        error_diagnostics = [d for d in elab_diagnostics if d.severity.name == 'ERROR']
        if error_diagnostics:
            display_diagnostics(error_diagnostics, "Elaboration Error")
            raise ValueError("Elaboration failed due to errors")
        
        # Display warnings/info if verbose
        if verbose:
            warning_diagnostics = [d for d in elab_diagnostics if d.severity.name != 'ERROR']
            if warning_diagnostics:
                display_diagnostics(warning_diagnostics, "Elaboration Warning")
    
    if elaborated_file is None:
        raise ValueError("Elaboration failed - no elaborated file returned")
    
    if verbose:
        # Count elaborated elements
        elaborated_modules = elaborated_file.modules
        total_ports = sum(len(mod.ports or {}) for mod in elaborated_modules.values())
        total_instances = sum(len(mod.instances or {}) for mod in elaborated_modules.values())
        print(f"✅ Pattern elaboration completed:")
        print(f"   - Total ports: {total_ports}")
        print(f"   - Total instances: {total_instances}")
    
    # Step 3: Generate SPICE
    if verbose:
        print("⚡ Step 3: Generating SPICE netlist...")
    
    generator = SPICEGenerator()
    spice_netlist = generator.generate(elaborated_file)
    
    if verbose:
        lines = spice_netlist.split('\n')
        print(f"✅ SPICE generation completed:")
        print(f"   - Total lines: {len(lines)}")
        print(f"   - Subcircuits: {len([l for l in lines if l.strip().startswith('.subckt')])}")
        print(f"   - Devices: {len([l for l in lines if l.strip() and l.strip()[0] in 'MRCLDQXKW'])}")
    
    # Step 4: Save to file
    if verbose:
        print(f"💾 Step 4: Saving to {output_path}...")
    
    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(spice_netlist)
    
    if verbose:
        print(f"✅ Successfully generated SPICE netlist: {output_path}")
        print(f"📊 File size: {output_path.stat().st_size} bytes")
    
    return output_path


def main():
    """Main command-line interface."""
    parser = argparse.ArgumentParser(
        description="Convert ASDL YAML files to SPICE netlists",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/netlist_asdl.py tests/fixtures/inverter.yml
  python scripts/netlist_asdl.py tests/fixtures/diff_pair_nmos.yml output.spice
  python scripts/netlist_asdl.py @tests/fixtures/diff_pair_nmos.yml
        """)
    
    parser.add_argument('input', 
                       help='Input ASDL YAML file (use @filename for auto output naming)')
    parser.add_argument('output', nargs='?', 
                       help='Output SPICE file (optional)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Handle @filename syntax for auto output naming
    input_file = args.input
    if input_file.startswith('@'):
        input_file = input_file[1:]
        output_file = args.output  # Will be auto-generated if None
    else:
        output_file = args.output
    
    try:
        output_path = netlist_asdl_file(input_file, output_file, args.verbose)
        print(f"🎉 Successfully generated: {output_path}")
        return 0
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        return 1
    except ValueError as e:
        # Diagnostic errors are already displayed by netlist_asdl_file
        if "failed due to errors" not in str(e):
            print(f"❌ Processing error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 