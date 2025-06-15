"""
Pattern expansion implementation for ASDL.

Handles expansion of differential patterns (<p,n>) and bus patterns ([3:0])
as an explicit elaboration step, similar to Verilog elaboration.
"""

from typing import Dict, List, Any
from .data_structures import ASDLFile, Module, Port, Instance


class PatternExpander:
    """
    Pattern expansion engine for ASDL designs.
    
    Expands patterns in an explicit step after parsing:
    - Differential patterns: <p,n> -> _p, _n
    - Bus patterns: [3:0] -> [3], [2], [1], [0]
    - Order-matched mapping expansion
    """
    
    def expand_patterns(self, asdl_file: ASDLFile) -> ASDLFile:
        """
        Expand all patterns in the ASDL design.
        
        This is the main entry point for pattern expansion. It processes
        all modules in the design and expands patterns in:
        - Port definitions
        - Instance definitions and mappings
        
        Args:
            asdl_file: Original ASDL design with patterns
            
        Returns:
            New ASDL design with all patterns expanded
        """
        # TODO: Implement pattern expansion
        # For now, return the original file unchanged
        return asdl_file
    
    def expand_module_patterns(self, module: Module) -> Module:
        """
        Expand patterns within a single module.
        
        Args:
            module: Module with potential patterns
            
        Returns:
            Module with patterns expanded
        """
        # TODO: Implement module pattern expansion
        expanded_ports = self.expand_port_patterns(module.ports or {})
        expanded_instances = self.expand_instance_patterns(module.instances or {})
        
        return Module(
            doc=module.doc,
            ports=expanded_ports,
            nets=module.nets,  # TODO: Expand patterns in nets
            parameters=module.parameters,
            instances=expanded_instances
        )
    
    def expand_port_patterns(self, ports: Dict[str, Port]) -> Dict[str, Port]:
        """
        Expand patterns in port definitions.
        
        Examples:
        - "in_<p,n>" -> {"in_p": Port(...), "in_n": Port(...)}
        - "data[3:0]" -> {"data[3]": Port(...), "data[2]": Port(...), ...}
        
        Args:
            ports: Dictionary of port name to Port objects
            
        Returns:
            Dictionary with expanded port names
        """
        # TODO: Implement port pattern expansion
        expanded_ports = {}
        
        for port_name, port in ports.items():
            if self._has_diff_pattern(port_name):
                # Handle differential patterns <p,n>
                expanded_names = self._expand_diff_pattern(port_name)
                for expanded_name in expanded_names:
                    expanded_ports[expanded_name] = port
            elif self._has_bus_pattern(port_name):
                # Handle bus patterns [3:0]
                expanded_names = self._expand_bus_pattern(port_name)
                for expanded_name in expanded_names:
                    expanded_ports[expanded_name] = port
            else:
                # No pattern, keep as is
                expanded_ports[port_name] = port
                
        return expanded_ports
    
    def expand_instance_patterns(self, instances: Dict[str, Instance]) -> Dict[str, Instance]:
        """
        Expand patterns in instance definitions.
        
        Handles both instance name patterns and mapping patterns.
        
        Args:
            instances: Dictionary of instance ID to Instance objects
            
        Returns:
            Dictionary with expanded instance IDs and mappings
        """
        # TODO: Implement instance pattern expansion
        expanded_instances = {}
        
        for instance_id, instance in instances.items():
            if self._has_diff_pattern(instance_id):
                # Expand instance name pattern
                expanded_ids = self._expand_diff_pattern(instance_id)
                for expanded_id in expanded_ids:
                    # Also need to expand mappings for this instance
                    expanded_mappings = self._expand_mapping_patterns(
                        instance.mappings, 
                        instance_id, 
                        expanded_id
                    )
                    expanded_instances[expanded_id] = Instance(
                        model=instance.model,
                        mappings=expanded_mappings,
                        parameters=instance.parameters,
                        intent=instance.intent
                    )
            else:
                # No pattern in instance name, but might have patterns in mappings
                expanded_mappings = self._expand_mapping_patterns(
                    instance.mappings,
                    instance_id,
                    instance_id
                )
                expanded_instances[instance_id] = Instance(
                    model=instance.model,
                    mappings=expanded_mappings,
                    parameters=instance.parameters,
                    intent=instance.intent
                )
                
        return expanded_instances
    
    def _has_diff_pattern(self, name: str) -> bool:
        """Check if name contains differential pattern <...>."""
        return '<' in name and '>' in name
    
    def _has_bus_pattern(self, name: str) -> bool:
        """Check if name contains bus pattern [...].""" 
        return '[' in name and ']' in name and ':' in name
    
    def _expand_diff_pattern(self, name: str) -> List[str]:
        """
        Expand differential pattern in name.
        
        Example: "in_<p,n>" -> ["in_p", "in_n"]
        """
        # TODO: Implement differential pattern expansion
        # Simple placeholder implementation
        if '<p,n>' in name:
            return [name.replace('<p,n>', 'p'), name.replace('<p,n>', 'n')]
        elif '<P,N>' in name:
            return [name.replace('<P,N>', 'P'), name.replace('<P,N>', 'N')]
        return [name]
    
    def _expand_bus_pattern(self, name: str) -> List[str]:
        """
        Expand bus pattern in name.
        
        Example: "data[3:0]" -> ["data[3]", "data[2]", "data[1]", "data[0]"]
        """
        # TODO: Implement bus pattern expansion
        return [name]  # Placeholder
    
    def _expand_mapping_patterns(self, mappings: Dict[str, str], 
                                original_instance_id: str, 
                                expanded_instance_id: str) -> Dict[str, str]:
        """
        Expand patterns in port-to-net mappings.
        
        Handles order-matched expansion where the i-th expanded port
        maps to the i-th expanded net.
        """
        # TODO: Implement mapping pattern expansion
        return mappings  # Placeholder 