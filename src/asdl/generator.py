"""
SPICE netlist generation implementation for ASDL.

Generates SPICE netlists from elaborated ASDL designs where patterns
have been expanded and parameters have been resolved.
"""

from typing import Dict, List, Any, Optional
from .data_structures import ASDLFile, Module, Instance


class SPICEGenerator:
    """
    Unified SPICE netlist generator for ASDL designs.
    
    Generates SPICE netlists with unified module architecture:
    - Primitive modules (with spice_template) → inline SPICE generation
    - Hierarchical modules (with instances) → .subckt definitions
    - PDK includes generated automatically for primitive modules
    - ngspice compatible output format
    
    Pipeline order:
    1. PDK include statements (.include for used PDKs)
    2. Hierarchical module subcircuit definitions (.subckt for each circuit module)
    3. Main circuit instantiation (XMAIN top-level call)
    4. End statement (.end)
    """
    

    
    def __init__(self):
        """Initialize SPICE generator with default settings."""
        self.comment_style = "*"  # SPICE comment character
        self.indent = "  "        # Indentation for readability
    
    def generate(self, asdl_file: ASDLFile) -> str:
        """
        Generate complete SPICE netlist from ASDL design with unified architecture.
        
        Args:
            asdl_file: Fully elaborated ASDL design
            
        Returns:
            Complete SPICE netlist as string
        """
        lines = []
        
        # Add header comment
        lines.append(f"* SPICE netlist generated from ASDL")
        lines.append(f"* Design: {asdl_file.file_info.doc}")
        lines.append(f"* Top module: {asdl_file.file_info.top_module}")
        lines.append(f"* Author: {asdl_file.file_info.author}")
        lines.append(f"* Date: {asdl_file.file_info.date}")
        lines.append(f"* Revision: {asdl_file.file_info.revision}")
        lines.append("")
        
        # Generate PDK include statements for primitive modules
        pdk_includes = self._generate_pdk_includes(asdl_file)
        if pdk_includes:
            lines.append("* PDK model includes")
            lines.extend(pdk_includes)
            lines.append("")
        
        # Generate subcircuit definitions for hierarchical modules only
        # (primitive modules are handled inline)
        hierarchical_modules = {name: module for name, module in asdl_file.modules.items() 
                               if module.instances is not None}
        
        if hierarchical_modules:
            lines.append("* Hierarchical module subcircuit definitions")
            for module_name, module in hierarchical_modules.items():
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
    
    def _generate_pdk_includes(self, asdl_file: ASDLFile) -> List[str]:
        """
        Generate .include statements for PDK modules.
        
        Args:
            asdl_file: ASDL design containing modules
            
        Returns:
            List of .include statement strings
        """
        includes = []
        used_pdks = set()
        
        for module in asdl_file.modules.values():
            if module.pdk and module.pdk not in used_pdks:
                includes.append(f'.include "{module.pdk}_fd_pr/models/ngspice/design.ngspice"')
                used_pdks.add(module.pdk)
                
        return includes
    
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
        
        # Add parameter declarations with default values
        if module.parameters:
            for param_name, param_value in module.parameters.items():
                lines.append(f"{self.indent}.param {param_name}={param_value}")
        

        
        # Generate instances
        if module.instances:
            for instance_id, instance in module.instances.items():
                # Add instance documentation as comment if present
                if instance.doc:
                    lines.append(f"{self.indent}* {instance.doc}")
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
        Generate SPICE line for an instance with unified module architecture.
        
        Args:
            instance_id: Instance identifier
            instance: Instance definition
            asdl_file: Full ASDL design for context
            
        Returns:
            SPICE instance line as string
        """
        # Check if instance model exists in modules
        if instance.model not in asdl_file.modules:
            raise ValueError(f"Unknown model reference: {instance.model}")
            
        module = asdl_file.modules[instance.model]
        
        # Determine if this is a primitive or hierarchical module
        if module.spice_template is not None:
            # Primitive module - generate inline SPICE using template
            return self._generate_primitive_instance(instance_id, instance, module)
        elif module.instances is not None:
            # Hierarchical module - generate subcircuit call
            return self._generate_subckt_call(instance_id, instance, asdl_file)
        else:
            raise ValueError(f"Module {instance.model} has neither spice_template nor instances")
    
    def _generate_primitive_instance(self, instance_id: str, instance: Instance, 
                                   module: Module) -> str:
        """
        Generate inline SPICE line for a primitive module instance.
        
        Uses the module's spice_template with parameter and port substitution.
        
        Args:
            instance_id: Instance identifier
            instance: Instance definition
            module: Primitive module with spice_template
            
        Returns:
            SPICE device line as string
        """
        if not module.spice_template:
            raise ValueError(f"Module {instance_id} has no spice_template for primitive generation")
        
        # Build substitution data for template
        template_data = {}
        
        # Add instance name substitution
        template_data['name'] = instance_id
        
        # Add port mappings from instance.mappings
        if instance.mappings:
            for port_name, net_name in instance.mappings.items():
                template_data[port_name] = net_name
        
        # Add parameter substitutions (merge module defaults with instance overrides)
        merged_params = {}
        if module.parameters:
            merged_params.update(module.parameters)
        if instance.parameters:
            merged_params.update(instance.parameters)
            
        for param_name, param_value in merged_params.items():
            template_data[param_name] = param_value
        
        # Add variable substitutions (variables shadow parameters with same names)
        if module.variables:
            for var_name, var_value in module.variables.items():
                template_data[var_name] = var_value  # Variables override parameters
        
        # Apply substitutions to the spice_template
        try:
            final_line = module.spice_template.format(**template_data)
        except KeyError as e:
            raise ValueError(f"Missing placeholder in spice_template for instance {instance_id}: {e}")
        
        return final_line
    
    def _format_named_parameters(self, params: Dict[str, Any]) -> str:
        """Format parameters as param=value pairs in alphabetical order."""
        param_parts = []
        for param_name in sorted(params.keys()):
            param_parts.append(f"{param_name}={params[param_name]}")
        return " ".join(param_parts)
    
    def _generate_subckt_call(self, instance_id: str, instance: Instance, 
                             asdl_file: ASDLFile) -> str:
        """
        Generate subcircuit call for a module instance.
        
        Format: X_<name> <nodes> <subckt_name> <parameters>
        Example: X_INV1 in out vdd vss inverter M=2
        """
        module = asdl_file.modules[instance.model]
        

        
        # Get node connections in port order
        node_list = []
        port_list = self._get_port_list(module)
        
        for port_name in port_list:
            if port_name in instance.mappings:
                node_list.append(instance.mappings[port_name])
            else:
                # Handle unconnected ports (after validation, this should be intentional)
                node_list.append("UNCONNECTED")
        
        # Get instance parameters (only instance-specific parameters)
        instance_params = instance.parameters if instance.parameters else {}
        
        # Format subcircuit call: X_name nodes subckt_name params
        parts = [f"X_{instance_id}", " ".join(node_list), instance.model]
        
        # Add parameters if any
        if instance_params:
            param_str = self._format_named_parameters(instance_params)
            parts.append(param_str)
        
        return " ".join(parts)
    

    
    def _get_port_list(self, module: Module) -> List[str]:
        """
        Get ordered list of port names for a module.
        
        Preserves declaration order from YAML instead of alphabetical sorting.
        This ensures SPICE .subckt port order matches the canonical order 
        defined in the ASDL YAML file.
        """
        if not module.ports:
            return []
        
        # Preserve declaration order (Python 3.7+ dict insertion order)
        return list(module.ports.keys())
    
    def _get_top_level_nets(self, module: Optional[Module] = None) -> str:
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

 