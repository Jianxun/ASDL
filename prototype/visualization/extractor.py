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
from typing import Dict, Any, Optional, List, Tuple

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

def is_power_net(net_name: str) -> bool:
    """Checks if a net name represents a power supply (VDD/VSS/GND)."""
    base_name = strip_pattern(net_name).lower()
    return base_name in ['vdd', 'vss', 'gnd', 'vcc', 'vee', 'avdd', 'avss']

def create_device_node(instance_id: str, instance_obj: Any, x: int, y: int) -> Dict[str, Any]:
    """Creates a device node with coordinates and dimensions."""
    return {
        "id": instance_id,
        "label": strip_pattern(instance_id),
        "model": instance_obj.model,
        "is_patterned": has_pattern(instance_id),
        "x": x,
        "y": y,
        "width": 60,
        "height": 60,
        "node_type": "device"
    }

def create_power_port_node(net_name: str, x: int, y: int) -> Dict[str, Any]:
    """Creates a power supply port node (VDD/VSS as wide horizontal bars)."""
    return {
        "id": net_name.upper(),
        "label": net_name.upper(),
        "model": "power_supply",
        "is_patterned": False,
        "x": x,
        "y": y,
        "width": 400,
        "height": 20,
        "node_type": "port"
    }

def create_port_node(port_name: str, x: int, y: int) -> Dict[str, Any]:
    """Creates a port node (50% size of device nodes)."""
    return {
        "id": f"port_{strip_pattern(port_name)}",
        "label": strip_pattern(port_name),
        "model": "port",
        "is_patterned": has_pattern(port_name),
        "x": x,
        "y": y,
        "width": 30,
        "height": 30,
        "node_type": "port"
    }

def get_node_coordinates(node_id: str, node_type: str) -> Tuple[int, int]:
    """
    Returns hardcoded coordinates for nodes in vertical layout:
    VDD -> R_LOAD<P,N> -> MN_DP<P,N> -> M_TAIL -> VSS
    """
    base_id = strip_pattern(node_id).lower()
    
    # Power supply positioning
    if node_type == "power_supply":
        if base_id == "vdd":
            return (100, 50)   # Top of canvas
        elif base_id in ["vss", "gnd"]:
            return (100, 450)  # Bottom of canvas
    
    # Port positioning  
    if node_type == "port":
        if "in" in base_id:
            return (150, 150)  # Input ports
        elif "out" in base_id:
            return (350, 350)  # Output ports  
        elif "vbn" in base_id:
            return (50, 300)   # Bias voltage
        else:
            return (400, 150)  # Other ports
    
    # Device positioning (vertical layout)
    if "r_load" in base_id:
        return (250, 200)  # Load resistors
    elif "mn_dp" in base_id:
        return (250, 250)  # Differential pair
    elif "m_tail" in base_id:
        return (250, 300)  # Tail current source
    else:
        return (250, 200)  # Default device position

def extract_module_data(module: Module) -> Dict[str, Any]:
    """
    Extracts nodes, nets, and connections from a module with enhanced
    coordinate and dimension information for visualization.
    """
    # 1. Extract Nets (from ports and internal nets)
    nets = {}
    power_nets = set()
    
    for port_name in (module.ports or {}):
        base_name = strip_pattern(port_name)
        net_type = "differential" if has_pattern(port_name) else "single"
        if base_name not in nets or net_type == "differential":
            nets[base_name] = {"type": net_type, "is_internal": False}
        
        if is_power_net(base_name):
            power_nets.add(base_name)

    for net_name in (module.internal_nets or []):
        base_name = strip_pattern(net_name)
        net_type = "differential" if has_pattern(net_name) else "single"
        if base_name not in nets or net_type == "differential":
            nets[base_name] = {"type": net_type, "is_internal": True}
        
        if is_power_net(base_name):
            power_nets.add(base_name)

    # 2. Create Nodes List
    nodes = []
    
    # 2a. Create Power Supply Port Nodes
    for power_net in power_nets:
        x, y = get_node_coordinates(power_net, "power_supply")
        nodes.append(create_power_port_node(power_net, x, y))
    
    # 2b. Create Port Nodes
    for port_name in (module.ports or {}):
        if not is_power_net(strip_pattern(port_name)):  # Skip power supply ports
            x, y = get_node_coordinates(port_name, "port")
            nodes.append(create_port_node(port_name, x, y))
    
    # 2c. Create Device Nodes
    for instance_id, instance_obj in (module.instances or {}).items():
        x, y = get_node_coordinates(instance_id, "device")
        nodes.append(create_device_node(instance_id, instance_obj, x, y))

    # 3. Build net connectivity map (which nodes connect to which nets)
    net_connections = {}  # net_name -> [(node_id, port_name, connection_type), ...]
    
    for instance_id, instance_obj in (module.instances or {}).items():
        for port_name, net_name in (instance_obj.mappings or {}).items():
            # Skip all bulk 'B' connections for MOSFETs
            if strip_pattern(port_name).upper() == "B":
                continue
                
            base_net = strip_pattern(net_name)
            is_differential = has_pattern(port_name) or has_pattern(net_name)
            connection_type = "differential" if is_differential else "single"
            
            if base_net not in net_connections:
                net_connections[base_net] = []
            
            net_connections[base_net].append((instance_id, strip_pattern(port_name), connection_type))

    # 4. Generate connections from net connectivity  
    connections = []
    for net_name, connected_devices in net_connections.items():
        # For each net, create connections between devices and corresponding port (if exists)
        
        # Check if this net corresponds to a port
        port_node_id = None
        if is_power_net(net_name):
            port_node_id = net_name.upper()  # VDD, VSS
        else:
            # Check if net matches any port name
            for port_name in (module.ports or {}):
                if strip_pattern(port_name) == net_name:
                    port_node_id = f"port_{net_name}"
                    break
        
        # Create port-to-device connections (port as source)
        if port_node_id:
            for device_node, device_port, conn_type in connected_devices:
                connections.append({
                    "from_node": port_node_id,
                    "from_port": "terminal",  # Ports have a generic terminal
                    "to_node": device_node,
                    "to_port": device_port,
                    "net": net_name,
                    "type": conn_type
                })
        
        # Also create device-to-device connections for internal nets
        if len(connected_devices) > 1:
            for i, (from_node, from_port, from_type) in enumerate(connected_devices):
                for j, (to_node, to_port, to_type) in enumerate(connected_devices):
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