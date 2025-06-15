"""
SPICE netlist generation implementation for ASDL.

Generates SPICE netlists from elaborated ASDL designs where patterns
have been expanded and parameters have been resolved.
"""

from typing import Dict, List, Any, Optional
from .data_structures import ASDLFile, Module, Instance, DeviceModel, DeviceType


class SPICEGenerator:
    """
    SPICE netlist generator for ASDL designs.
    
    Generates SPICE netlists from fully elaborated designs:
    - Each Module becomes a .subckt definition
    - Device instances become device lines
    - Module instances become subcircuit calls (X-lines)
    - Hierarchical netlists with proper subcircuit structure
    """
    
    # Device formatting templates with explicit port mapping
    # Templates directly show SPICE format with named port placeholders
    # Two-terminal devices use consistent "plus"/"minus" naming
    DEVICE_FORMATS = {
        DeviceType.RESISTOR: {
            "template": "{name} {plus} {minus} {model} {value}",
            "value_param": "value",
            "param_format": "bare"
        },
        DeviceType.CAPACITOR: {
            "template": "{name} {plus} {minus} {model} {value}",
            "value_param": "value",
            "param_format": "bare"
        },
        DeviceType.INDUCTOR: {
            "template": "{name} {plus} {minus} {model} {value}",
            "value_param": "value", 
            "param_format": "bare"
        },
        DeviceType.NMOS: {
            "template": "{name} {D} {G} {S} {B} {model} {params}",
            "param_format": "named"
        },
        DeviceType.PMOS: {
            "template": "{name} {D} {G} {S} {B} {model} {params}",
            "param_format": "named"
        },
        DeviceType.DIODE: {
            "template": "{name} {a} {c} {model} {params}",
            "param_format": "named"
        },
        # Default format for unknown device types
        "default": {
            "template": "{name} {model} {params}",
            "param_format": "named"
        }
    }
    
    def __init__(self):
        """Initialize SPICE generator with default settings."""
        self.comment_style = "*"  # SPICE comment character
        self.indent = "  "        # Indentation for readability
    
    def generate(self, asdl_file: ASDLFile) -> str:
        """
        Generate complete SPICE netlist from ASDL design.
        
        Args:
            asdl_file: Fully elaborated ASDL design
            
        Returns:
            Complete SPICE netlist as string
        """
        lines = []
        
        # Add header comment
        lines.append(f"* SPICE netlist generated from ASDL")
        lines.append(f"* Design: {asdl_file.file_info.doc}")
        lines.append(f"* Author: {asdl_file.file_info.author}")
        lines.append(f"* Date: {asdl_file.file_info.date}")
        lines.append(f"* Revision: {asdl_file.file_info.revision}")
        lines.append("")
        
        # Generate subcircuit definitions for all modules
        for module_name, module in asdl_file.modules.items():
            subckt_def = self.generate_subckt(module, module_name, asdl_file)
            lines.append(subckt_def)
            lines.append("")
        
        # Add main circuit instantiation if top_module is specified
        if asdl_file.file_info.top_module:
            top_module_name = asdl_file.file_info.top_module
            if top_module_name in asdl_file.modules:
                top_module = asdl_file.modules[top_module_name]
                lines.append(f"* Main circuit instantiation")
                lines.append(f"XMAIN {self._get_top_level_nets(top_module)} {top_module_name}")
                lines.append("")
        
        lines.append(".end")
        
        return "\n".join(lines)
    
    def generate_subckt(self, module: Module, module_name: str, 
                       asdl_file: ASDLFile) -> str:
        """
        Generate .subckt definition for a module.
        
        Args:
            module: Module to generate subcircuit for
            module_name: Name of the module
            asdl_file: Full ASDL design for context
            
        Returns:
            SPICE subcircuit definition as string
        """
        lines = []
        
        # Add module documentation
        if module.doc:
            lines.append(f"* {module.doc}")
        
        # Generate .subckt header
        port_list = self._get_port_list(module)
        lines.append(f".subckt {module_name} {' '.join(port_list)}")
        
        # Generate instances
        if module.instances:
            for instance_id, instance in module.instances.items():
                instance_line = self.generate_instance(
                    instance_id, instance, asdl_file
                )
                lines.append(f"{self.indent}{instance_line}")
        
        # Close subcircuit
        lines.append(".ends")
        
        return "\n".join(lines)
    
    def generate_instance(self, instance_id: str, instance: Instance, 
                         asdl_file: ASDLFile) -> str:
        """
        Generate SPICE line for an instance.
        
        Args:
            instance_id: Instance identifier
            instance: Instance definition
            asdl_file: Full ASDL design for context
            
        Returns:
            SPICE instance line as string
        """
        if instance.is_device_instance(asdl_file):
            return self._generate_device_line(instance_id, instance, asdl_file)
        elif instance.is_module_instance(asdl_file):
            return self._generate_subckt_call(instance_id, instance, asdl_file)
        else:
            raise ValueError(f"Unknown model reference: {instance.model}")
    
    def _generate_device_line(self, instance_id: str, instance: Instance, 
                             asdl_file: ASDLFile) -> str:
        """
        Generate device line for a primitive device instance using templates.
        
        Format: <name> <nodes> <model> <parameters>
        Example: MN1 drain gate source bulk nch_lvt W=1u L=0.1u M=1
        """
        device_model = asdl_file.models[instance.model]
        
        # Get device format specification
        device_format = self.DEVICE_FORMATS.get(device_model.type, self.DEVICE_FORMATS["default"])
        
        # Build template data with direct port mapping
        template_data = {
            "name": instance_id,
            "model": device_model.model,
        }
        
        # Map each port directly to its connected net
        for port in device_model.ports:
            if port in instance.mappings:
                template_data[port] = instance.mappings[port]
            else:
                # Handle unconnected ports
                template_data[port] = "UNCONNECTED"
        
        # Add parameter data based on format type
        all_params = self._merge_parameters(device_model, instance)
        
        if device_format["param_format"] == "bare":
            # Use bare value for simple devices (R, L, C)
            value_param = device_format["value_param"]
            template_data["value"] = str(all_params.get(value_param, ""))
        else:
            # Use named parameters for complex devices (transistors, etc.)
            template_data["params"] = self._format_named_parameters(all_params)
        
        # Apply template
        return device_format["template"].format(**template_data)
    

    
    def _merge_parameters(self, device_model: DeviceModel, instance: Instance) -> Dict[str, Any]:
        """Merge model default parameters with instance parameters."""
        all_params = {}
        
        # Add device model parameters (with defaults)
        if device_model.params:
            all_params.update(device_model.params)
        
        # Override with instance parameters
        if instance.parameters:
            all_params.update(instance.parameters)
            
        return all_params
    
    def _format_named_parameters(self, params: Dict[str, Any]) -> str:
        """Format parameters as param=value pairs."""
        param_parts = [f"{name}={value}" for name, value in params.items()]
        return " ".join(param_parts)
    
    def _generate_subckt_call(self, instance_id: str, instance: Instance, 
                             asdl_file: ASDLFile) -> str:
        """
        Generate subcircuit call for a module instance.
        
        Format: X<name> <nodes> <subckt_name>
        Example: XINV1 in out vdd vss inverter
        """
        module = asdl_file.modules[instance.model]
        
        # Get node connections in port order
        node_list = []
        port_list = self._get_port_list(module)
        
        for port_name in port_list:
            if port_name in instance.mappings:
                node_list.append(instance.mappings[port_name])
            else:
                # TODO: Better error handling
                node_list.append("UNCONNECTED")
        
        # Format: Xname nodes subckt_name
        return f"X{instance_id} {' '.join(node_list)} {instance.model}"
    
    def _get_port_list(self, module: Module) -> List[str]:
        """
        Get ordered list of port names for a module.
        
        TODO: Define port ordering convention (alphabetical? declaration order?)
        """
        if not module.ports:
            return []
        
        # For now, use alphabetical order
        # TODO: Preserve declaration order or use explicit ordering
        return sorted(module.ports.keys())
    
    def _get_top_level_nets(self, module: Module = None) -> str:
        """
        Get net list for top-level instantiation.
        
        For now, return the port list of the module being instantiated.
        TODO: Implement proper top-level net generation with actual connections.
        """
        if module and module.ports:
            # Use the module's port names as top-level nets
            port_list = self._get_port_list(module)
            return " ".join(port_list)
        else:
            return "vdd vss"  # Fallback
    
    def _format_parameter_value(self, value: Any) -> str:
        """
        Format parameter value for SPICE output.
        
        Handles different value types and units.
        """
        if isinstance(value, str):
            return value
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            return str(value) 