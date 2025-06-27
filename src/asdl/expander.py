"""
Pattern expansion implementation for ASDL.

Handles expansion of differential patterns (<p,n>) and bus patterns ([3:0])
as an explicit elaboration step, similar to Verilog elaboration.
"""

from typing import Dict, List, Any, Optional
from dataclasses import replace
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
        # Expand patterns in all modules
        expanded_modules = {}
        for module_name, module in asdl_file.modules.items():
            expanded_modules[module_name] = self.expand_module_patterns(module)
        
        # Create new ASDLFile with expanded modules
        # Models don't contain patterns, so they're passed through unchanged
        return ASDLFile(
            file_info=asdl_file.file_info,
            models=asdl_file.models,  # Models unchanged
            modules=expanded_modules,  # Modules with expanded patterns
            metadata=asdl_file.metadata
        )
    
    def expand_module_patterns(self, module: Module) -> Module:
        """
        Expand patterns within a single module.
        
        Args:
            module: Module with potential patterns
            
        Returns:
            Module with patterns expanded
        """
        expanded_ports = self.expand_port_patterns(module.ports or {})
        expanded_instances = self.expand_instance_patterns(module.instances or {})
        
        return Module(
            doc=module.doc,
            ports=expanded_ports,
            internal_nets=module.internal_nets,
            parameters=module.parameters,
            instances=expanded_instances,
            metadata=module.metadata,
            start_line=module.start_line,
            start_col=module.start_col
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
        expanded_ports = {}
        
        for port_name, port in ports.items():
            if self._has_literal_pattern(port_name):
                # Handle literal patterns <p,n>
                expanded_names = self._expand_literal_pattern(port_name)
                for expanded_name in expanded_names:
                    expanded_ports[expanded_name] = port
            elif self._has_bus_pattern(port_name):
                # Handle bus patterns [3:0] (future implementation)
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
        expanded_instances = {}
        
        for instance_id, instance in instances.items():
            if self._has_literal_pattern(instance_id):
                # Expand instance name pattern using literal expansion
                expanded_ids = self._expand_literal_pattern(instance_id)
                for expanded_id in expanded_ids:
                    # Also need to expand mappings for this instance
                    expanded_mappings = self._expand_mapping_patterns(
                        instance.mappings, 
                        instance_id, 
                        expanded_id
                    )
                    # Create new instance inheriting all fields from original, only changing mappings
                    expanded_instances[expanded_id] = replace(
                        instance,
                        mappings=expanded_mappings
                    )
            else:
                # No pattern in instance name, but might have patterns in mappings
                expanded_mappings = self._expand_mapping_patterns(
                    instance.mappings,
                    instance_id,
                    instance_id
                )
                # Create new instance inheriting all fields from original, only changing mappings
                expanded_instances[instance_id] = replace(
                    instance,
                    mappings=expanded_mappings
                )
                
        return expanded_instances
    

    
    def _has_bus_pattern(self, name: str) -> bool:
        """Check if name contains bus pattern [...].""" 
        return '[' in name and ']' in name and ':' in name
    
    def _has_literal_pattern(self, name: str) -> bool:
        """Check if name contains literal pattern <...>."""
        # Must have both < and > 
        if not ('<' in name and '>' in name):
            return False
        
        # Check that there's a complete pattern
        start = name.find('<')
        end = name.find('>')
        if start == -1 or end == -1 or start >= end:
            return False
            
        # Check for multiple bracket pairs (not supported)
        remaining = name[end+1:]
        if '<' in remaining and '>' in remaining:
            return False
            
        # Check for mixed bracket types inside pattern (array syntax inside literal)
        pattern_content = name[start+1:end]
        if '[' in pattern_content and ']' in pattern_content:
            return False
            
        # Any content inside brackets (even empty or single item) is a pattern attempt
        # Validation will enforce comma requirement
        return True
    
    def _extract_literal_pattern(self, name: str) -> Optional[List[str]]:
        """
        Extract literal pattern items from name.
        
        Example: "in_<p,n>" -> ["p", "n"]
        Returns None if no pattern found.
        """
        if not self._has_literal_pattern(name):
            return None
        
        start = name.find('<')
        end = name.find('>')
        pattern_content = name[start+1:end]
        
        # Handle empty pattern
        if not pattern_content:
            return []
        
        # Split by comma and strip whitespace - this handles single items too
        items = [item.strip() for item in pattern_content.split(',')]
        return items
    
    def _validate_literal_pattern(self, items: List[str]) -> None:
        """
        Validate literal pattern items according to expansion rules.
        
        Raises ValueError for invalid patterns.
        """
        if not items:
            raise ValueError("Pattern cannot be empty")
        
        if len(items) < 2:
            raise ValueError("Pattern must have at least 2 items")
        
        # Check that at least one item is non-empty
        if all(item == "" for item in items):
            raise ValueError("At least one item must be non-empty")
    
    def _validate_pattern_counts(self, left_items: Optional[List[str]], 
                               right_items: Optional[List[str]]) -> None:
        """
        Validate that pattern counts match for mappings.
        
        Raises ValueError if both sides have patterns but different counts.
        """
        # If one side is None (no pattern), that's OK
        if left_items is None or right_items is None:
            return
        
        # Both sides have patterns - counts must match
        if len(left_items) != len(right_items):
            raise ValueError(f"Pattern item counts must match: {len(left_items)} vs {len(right_items)}")
    
    def _expand_literal_pattern(self, name: str) -> List[str]:
        """
        Expand literal pattern in name.
        
        Example: "in_<p,n>" -> ["in_p", "in_n"]
        Returns [name] if no pattern.
        """
        items = self._extract_literal_pattern(name)
        if items is None:
            return [name]
        
        # Validate pattern
        self._validate_literal_pattern(items)
        
        # Find pattern location
        start = name.find('<')
        end = name.find('>')
        prefix = name[:start]
        suffix = name[end+1:]
        
        # Generate expanded names
        expanded = []
        for item in items:
            expanded_name = prefix + item + suffix
            expanded.append(expanded_name)
        
        return expanded
    

    
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
        
        For instance expansion, this creates the mappings for a single expanded instance.
        """
        expanded_mappings = {}
        
        # Get the index of this expanded instance if the instance itself had a pattern
        instance_has_pattern = self._has_literal_pattern(original_instance_id)
        if instance_has_pattern:
            # Get the index of this particular expansion
            instance_items = self._extract_literal_pattern(original_instance_id)
            instance_expansions = self._expand_literal_pattern(original_instance_id)
            try:
                instance_index = instance_expansions.index(expanded_instance_id)
            except ValueError:
                # If we can't find the index, something is wrong
                instance_index = 0
        else:
            instance_index = 0
        
        for port_name, net_name in mappings.items():
            # Check for patterns in port and net names
            port_has_pattern = self._has_literal_pattern(port_name)
            net_has_pattern = self._has_literal_pattern(net_name)
            
            if port_has_pattern and net_has_pattern:
                # Both sides have patterns - order-sensitive expansion
                port_items = self._extract_literal_pattern(port_name)
                net_items = self._extract_literal_pattern(net_name)
                
                # Validate pattern counts match
                self._validate_pattern_counts(port_items, net_items)
                
                # For instance expansion, select the corresponding port and net
                if instance_has_pattern:
                    # Ensure the mapping patterns match the instance pattern count
                    self._validate_pattern_counts(instance_items, port_items)
                    self._validate_pattern_counts(instance_items, net_items)
                    
                    # Use the same index for port and net expansion
                    expanded_ports = self._expand_literal_pattern(port_name)
                    expanded_nets = self._expand_literal_pattern(net_name)
                    expanded_mappings[expanded_ports[instance_index]] = expanded_nets[instance_index]
                else:
                    # No instance pattern, expand all port-net pairs
                    expanded_ports = self._expand_literal_pattern(port_name)
                    expanded_nets = self._expand_literal_pattern(net_name)
                    for exp_port, exp_net in zip(expanded_ports, expanded_nets):
                        expanded_mappings[exp_port] = exp_net
                    
            elif port_has_pattern and not net_has_pattern:
                # One-sided pattern (port side only)
                if instance_has_pattern:
                    # Ensure the port pattern matches the instance pattern count
                    port_items = self._extract_literal_pattern(port_name)
                    self._validate_pattern_counts(instance_items, port_items)
                    
                    # Use the corresponding port for this instance
                    expanded_ports = self._expand_literal_pattern(port_name)
                    expanded_mappings[expanded_ports[instance_index]] = net_name
                else:
                    # No instance pattern, expand all ports to same net
                    expanded_ports = self._expand_literal_pattern(port_name)
                    for exp_port in expanded_ports:
                        expanded_mappings[exp_port] = net_name
                    
            elif not port_has_pattern and net_has_pattern:
                # One-sided pattern (net side only)
                if instance_has_pattern:
                    # Ensure the net pattern matches the instance pattern count
                    net_items = self._extract_literal_pattern(net_name)
                    self._validate_pattern_counts(instance_items, net_items)
                    
                    # Use the corresponding net for this instance
                    expanded_nets = self._expand_literal_pattern(net_name)
                    expanded_mappings[port_name] = expanded_nets[instance_index]
                else:
                    # No instance pattern, map to first expanded net
                    expanded_nets = self._expand_literal_pattern(net_name)
                    expanded_mappings[port_name] = expanded_nets[0]
                
            else:
                # No patterns - keep as is
                expanded_mappings[port_name] = net_name
                
        return expanded_mappings 