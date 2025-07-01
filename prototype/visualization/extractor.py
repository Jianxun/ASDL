#!/usr/bin/env python3
"""
ASDL Hierarchy Extractor for Visualization

Parses a pre-elaborated ASDL file and extracts the hierarchical data
for a single module into a JSON format suitable for web-based
visualization tools like jsPlumb.

This script intentionally operates on pre-elaborated data to preserve
high-level design abstractions like differential pairs.
"""

import sys
import argparse
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from asdl.parser import ASDLParser, Diagnostic
from asdl.data_structures import Module

def has_pattern(name: str) -> bool:
    """Checks if a name contains a <...> pattern."""
    return bool(re.search(r"<.*>", name))

def strip_pattern(name: str) -> str:
    """Removes a <...> pattern from a name to get the base."""
    return re.sub(r"<.*>", "", name)

def extract_module_data(module: Module) -> Dict[str, Any]:
    """
    Extracts nodes, nets, and connections from a module.
    """
    # 1. Extract Nets (from ports and internal nets)
    nets = {}
    for port_name in (module.ports or {}):
        base_name = strip_pattern(port_name)
        net_type = "differential" if has_pattern(port_name) else "single"
        if base_name not in nets or net_type == "differential":
            nets[base_name] = {"type": net_type, "is_internal": False}

    for net_name in (module.internal_nets or []):
        base_name = strip_pattern(net_name)
        net_type = "differential" if has_pattern(net_name) else "single"
        if base_name not in nets or net_type == "differential":
            nets[base_name] = {"type": net_type, "is_internal": True}

    # 2. Extract Nodes (from instances)
    nodes = []
    for instance_id, instance_obj in (module.instances or {}).items():
        nodes.append({
            "id": instance_id,
            "label": strip_pattern(instance_id),
            "model": instance_obj.model,
            "is_patterned": has_pattern(instance_id)
        })

    # 3. Build net connectivity map (which nodes connect to which nets)
    net_connections = {}  # net_name -> [(node_id, port_name, connection_type), ...]
    
    for instance_id, instance_obj in (module.instances or {}).items():
        for port_name, net_name in (instance_obj.mappings or {}).items():
            base_net = strip_pattern(net_name)
            is_differential = has_pattern(port_name) or has_pattern(net_name)
            connection_type = "differential" if is_differential else "single"
            
            if base_net not in net_connections:
                net_connections[base_net] = []
            
            net_connections[base_net].append((instance_id, strip_pattern(port_name), connection_type))

    # 4. Generate node-to-node connections from net connectivity
    connections = []
    for net_name, connected_nodes in net_connections.items():
        # For each net, create connections between all pairs of connected nodes
        for i, (from_node, from_port, from_type) in enumerate(connected_nodes):
            for j, (to_node, to_port, to_type) in enumerate(connected_nodes):
                if i < j:  # Avoid duplicate connections (A->B and B->A)
                    # Connection is differential if either end is differential
                    conn_type = "differential" if from_type == "differential" or to_type == "differential" else "single"
                    connections.append({
                        "from_node": from_node,
                        "from_port": from_port,
                        "to_node": to_node,
                        "to_port": to_port,
                        "net": net_name,
                        "type": conn_type
                    })

    return {
        "module_name": module.doc or "Unnamed Module",
        "nodes": nodes,
        "nets": nets,
        "connections": connections
    }


def main():
    """Main command-line interface."""
    parser = argparse.ArgumentParser(description="Extract ASDL hierarchy to JSON for visualization.")
    parser.add_argument("input_file", type=Path, help="Path to the input ASDL YAML file.")
    parser.add_argument("output_file", type=Path, help="Path to the output JSON file.")
    parser.add_argument("-m", "--module", required=True, help="The name of the module to extract.")
    
    args = parser.parse_args()

    # Validate input file
    if not args.input_file.exists():
        print(f"❌ Error: Input file not found: {args.input_file}")
        sys.exit(1)

    # Step 1: Parse the ASDL file
    print(f"📖 Parsing ASDL file: {args.input_file}...")
    asdl_parser = ASDLParser()
    asdl_file, diagnostics = asdl_parser.parse_file(str(args.input_file))

    if diagnostics:
        for diag in diagnostics:
            if diag.severity == "ERROR":
                print(f"❌ Parser Error: {diag}")
                sys.exit(1)

    if not asdl_file:
        print("❌ Error: Failed to parse ASDL file.")
        sys.exit(1)

    # Step 2: Find the target module
    print(f"🔎 Looking for module: {args.module}...")
    target_module = asdl_file.modules.get(args.module)

    if not target_module:
        print(f"❌ Error: Module '{args.module}' not found in file.")
        print(f"   Available modules: {list(asdl_file.modules.keys())}")
        sys.exit(1)
        
    print("✅ Module found.")

    # Step 3: Extract data
    print("🚀 Extracting hierarchical data...")
    hierarchy_data = extract_module_data(target_module)
    print("✅ Data extraction complete.")

    # Step 4: Write to output file
    print(f"💾 Writing JSON to: {args.output_file}...")
    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_file, 'w') as f:
        json.dump(hierarchy_data, f, indent=2)

    print(f"🎉 Successfully created visualization data at {args.output_file}")


if __name__ == "__main__":
    main() 