"""
SPICE netlist generation implementation for ASDL.

Generates SPICE netlists from elaborated ASDL designs where patterns
have been expanded and parameters have been resolved.
"""

from typing import Dict, List, Any, Optional
from .data_structures import ASDLFile, Module, Instance, DeviceModel, DeviceType


class SPICEGenerator:
    """
    Hierarchical SPICE netlist generator for ASDL designs.
    
    Generates hierarchical SPICE netlists with proper subcircuit structure:
    - Device models become .subckt definitions (primitives inside)
    - Module definitions become .subckt definitions  
    - Device instances become subcircuit calls (X_ prefix)
    - Module instances become subcircuit calls (X prefix)
    - Two-level port resolution: named mappings + model-defined order
    - ngspice compatible output format
    
    Pipeline order:
    1. Model subcircuit definitions (.subckt for each device model)
    2. Module subcircuit definitions (.subckt for each circuit module)
    3. Main circuit instantiation (XMAIN top-level call)
    4. End statement (.end)
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
        
        # Generate model subcircuit definitions first
        if asdl_file.models:
            lines.append("* Model subcircuit definitions")
            for model_name, model in asdl_file.models.items():
                model_subckt = self.generate_model_subcircuit(model_name, model)
                lines.append(model_subckt)
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
        
        # End SPICE netlist (ngspice compatibility)
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
        Generate subcircuit call for a device instance.
        
        Format: X_<name> <nodes> <model_name> <parameters>
        Example: X_MN1 in out vss vss nmos_unit M=2
        """
        device_model = asdl_file.models[instance.model]
        
        # Build subcircuit call with X_ prefix
        subckt_name = f"X_{instance_id}"
        
        # Get node connections in model-defined port order
        node_list = []
        for port_name in device_model.ports:
            if port_name in instance.mappings:
                node_list.append(instance.mappings[port_name])
            else:
                # Handle unconnected ports
                node_list.append("UNCONNECTED")
        
        # Get instance parameters (only instance-specific parameters)
        instance_params = instance.parameters if instance.parameters else {}
        
        # Format subcircuit call: X_name nodes model_name params
        parts = [subckt_name, " ".join(node_list), instance.model]
        
        # Add parameters if any
        if instance_params:
            param_str = self._format_named_parameters(instance_params)
            parts.append(param_str)
        
        return " ".join(parts)
    
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
    
    def _format_named_parameters(self, params: Dict[str, Any], model: DeviceModel = None) -> str:
        """Format parameters as param=value pairs using model-defined order."""
        param_parts = []
        
        if model and model.params:
            # First, add parameters in model-defined order
            for param_name in model.params.keys():
                if param_name in params:
                    param_parts.append(f"{param_name}={params[param_name]}")
            
            # Then add any instance-only parameters (alphabetically for consistency)
            instance_only = set(params.keys()) - set(model.params.keys())
            for param_name in sorted(instance_only):
                param_parts.append(f"{param_name}={params[param_name]}")
        else:
            # Fallback to alphabetical order if no model parameter order available
            for param_name in sorted(params.keys()):
                param_parts.append(f"{param_name}={params[param_name]}")
        
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

    def generate_model_subcircuit(self, model_name: str, model: DeviceModel) -> str:
        """
        Generate .subckt definition for a device model.
        
        Args:
            model_name: Name of the model
            model: DeviceModel definition
            
        Returns:
            SPICE subcircuit definition as string
        """
        lines = []
        
        # Add model documentation
        if model.description:
            lines.append(f"* {model.description}")
        
        # Generate .subckt header with model-defined port order
        port_list = model.ports
        lines.append(f".subckt {model_name} {' '.join(port_list)}")
        
        # Add parameter declarations with default values
        param_defaults = model.get_parameter_defaults()
        if param_defaults:
            for param_name, param_value in param_defaults.items():
                lines.append(f"{self.indent}.param {param_name}={param_value}")
        
        # Generate the internal device instance
        device_instance = self._generate_model_device_instance(model)
        lines.append(f"{self.indent}{device_instance}")
        
        # Close subcircuit
        lines.append(".ends")
        
        return "\n".join(lines)

    def _generate_model_device_instance(self, model: DeviceModel) -> str:
        """
        Generate the internal device instance for a model subcircuit.
        
        This creates the primitive device line that goes inside the model subcircuit.
        Uses either the new device_line approach or legacy template approach.
        
        Args:
            model: DeviceModel definition
            
        Returns:
            SPICE device line as string
        """
        if model.has_device_line():
            # NEW APPROACH: Use raw device_line with parameter substitution
            return self._generate_from_device_line(model)
        else:
            # LEGACY APPROACH: Use templates (backward compatibility)
            return self._generate_from_legacy_template(model)
    
    def _generate_from_device_line(self, model: DeviceModel) -> str:
        """
        Generate device line using the new device_line approach.
        
        Substitutes port names and parameter references in the raw device line.
        """
        device_line = model.device_line
        
        # Build substitution data
        template_data = {}
        
        # Add port mappings (identity mapping within subcircuit)
        for port in model.ports:
            template_data[port] = port
        
        # Add parameter references (will be substituted with {param} syntax)
        param_defaults = model.get_parameter_defaults()
        for param_name in param_defaults.keys():
            template_data[param_name] = f"{{{param_name}}}"
        
        # Apply substitutions
        try:
            return device_line.format(**template_data)
        except KeyError as e:
            raise ValueError(f"Missing template parameter in device_line: {e}")
    
    def _generate_from_legacy_template(self, model: DeviceModel) -> str:
        """
        Generate device line using legacy template approach (backward compatibility).
        """
        # Get device format specification
        device_format = self.DEVICE_FORMATS.get(model.type, self.DEVICE_FORMATS["default"])
        
        # Determine device name prefix based on device type
        device_prefixes = {
            DeviceType.RESISTOR: "R",
            DeviceType.CAPACITOR: "C", 
            DeviceType.INDUCTOR: "L",
            DeviceType.NMOS: "MN",
            DeviceType.PMOS: "MP",
            DeviceType.DIODE: "D"
        }
        device_name = device_prefixes.get(model.type, "X")
        
        # Build template data
        template_data = {
            "name": device_name,
            "model": model.model,
        }
        
        # Map each port to itself (identity mapping within subcircuit)
        for port in model.ports:
            template_data[port] = port
        
        # Add parameter data based on format type
        if device_format["param_format"] == "bare":
            # Use bare value for simple devices (R, L, C)
            value_param = device_format["value_param"]
            template_data["value"] = str(model.params.get(value_param, ""))
        else:
            # Use named parameters for complex devices (transistors, etc.)
            template_data["params"] = self._format_named_parameters(model.params, model)
        
        # Apply template
        return device_format["template"].format(**template_data) 