from typing import List, Tuple, Dict, Any, Optional
from dataclasses import replace
import re

from asdl.data_structures import ASDLFile, Module, Port, Locatable, Instance
from asdl.diagnostics import Diagnostic, DiagnosticSeverity


class Elaborator:
    """
    The Elaborator is responsible for transforming the raw, parsed ASDL data
    structures into a fully specified, elaborated design. It handles:
    - Pattern Expansion (both literal <> and bus [])
    - Parameter Resolution (future implementation)
    """

    def elaborate(
        self, asdl_file: ASDLFile
    ) -> Tuple[Optional[ASDLFile], List[Diagnostic]]:
        """
        Elaborates an ASDL file by performing pattern expansion.
        """
        diagnostics: List[Diagnostic] = []

        try:
            elaborated_file = replace(asdl_file, modules={})
            for name, module in asdl_file.modules.items():
                elaborated_module, module_diagnostics = self._elaborate_module(module)
                diagnostics.extend(module_diagnostics)
                elaborated_file.modules[name] = elaborated_module

            return elaborated_file, diagnostics

        except Exception as e:
            diagnostics.append(
                self._create_diagnostic(
                    "E999", "Internal Elaboration Error", f"An unexpected error occurred: {e}"
                )
            )
            return None, diagnostics

    def _elaborate_module(self, module: Module) -> Tuple[Module, List[Diagnostic]]:
        """
        Expand patterns within a single module.
        """
        diagnostics: List[Diagnostic] = []
        # Create a deep copy to avoid modifying the original during iteration
        module_copy = replace(
            module,
            ports={name: replace(port) for name, port in (module.ports or {}).items()},
            instances={
                name: replace(inst) for name, inst in (module.instances or {}).items()
            },
        )

        expanded_ports, port_diagnostics = self._expand_ports(module_copy.ports)
        diagnostics.extend(port_diagnostics)
        module_copy.ports = expanded_ports

        expanded_instances, instance_diagnostics = self._expand_instances(module_copy.instances)
        diagnostics.extend(instance_diagnostics)
        module_copy.instances = expanded_instances

        return module_copy, diagnostics

    def _expand_ports(
        self, ports: Optional[Dict[str, Port]]
    ) -> Tuple[Dict[str, Port], List[Diagnostic]]:
        if not ports:
            return {}, []

        new_ports = {}
        diagnostics: List[Diagnostic] = []

        for port_name, port_obj in ports.items():
            has_literal = self._has_literal_pattern(port_name)
            has_bus = self._has_bus_pattern(port_name)

            if has_literal and has_bus:
                diagnostics.append(
                    self._create_diagnostic(
                        "E103",
                        "Mixed Pattern Types",
                        f"Port '{port_name}' contains both a literal ('<>') and bus ('[]') pattern.",
                        port_obj,
                    )
                )
                new_ports[port_name] = port_obj  # Keep original on error
                continue

            if has_literal:
                expanded_names, literal_diagnostics = self._expand_literal_pattern(
                    port_name, port_obj
                )
                diagnostics.extend(literal_diagnostics)
                if not literal_diagnostics:
                    for new_name in expanded_names:
                        new_ports[new_name] = replace(port_obj)
                else:
                    new_ports[port_name] = port_obj
            elif has_bus:
                expanded_names, bus_diagnostics = self._expand_bus_pattern(
                    port_name, port_obj
                )
                diagnostics.extend(bus_diagnostics)
                if not bus_diagnostics:
                    for new_name in expanded_names:
                        new_ports[new_name] = replace(port_obj)
                else:
                    new_ports[port_name] = port_obj
            else:
                new_ports[port_name] = port_obj

        return new_ports, diagnostics

    def _expand_instances(
        self, instances: Optional[Dict[str, Instance]]
    ) -> Tuple[Dict[str, Instance], List[Diagnostic]]:
        if not instances:
            return {}, []

        new_instances = {}
        diagnostics: List[Diagnostic] = []

        for instance_id, instance_obj in instances.items():
            has_literal = self._has_literal_pattern(instance_id)
            has_bus = self._has_bus_pattern(instance_id)

            if has_literal and has_bus:
                diagnostics.append(
                    self._create_diagnostic(
                        "E103",
                        "Mixed Pattern Types",
                        f"Instance '{instance_id}' contains both a literal ('<>') and bus ('[]') pattern.",
                        instance_obj,
                    )
                )
                new_instances[instance_id] = instance_obj  # Keep original on error
                continue

            if has_literal:
                expanded_names, literal_diagnostics = self._expand_literal_pattern(
                    instance_id, instance_obj
                )
                diagnostics.extend(literal_diagnostics)
                if not literal_diagnostics:
                    # Try to expand mappings for all instances first to check for errors
                    mapping_errors = []
                    expanded_instances_data = []
                    
                    for i, new_name in enumerate(expanded_names):
                        # Expand mappings for this instance
                        expanded_mappings, mapping_diagnostics = self._expand_mapping_patterns(
                            instance_obj.mappings or {}, instance_id, new_name, i
                        )
                        mapping_errors.extend(mapping_diagnostics)
                        expanded_instances_data.append((new_name, expanded_mappings))
                    
                    if mapping_errors:
                        # If there are mapping errors, preserve original instance and report diagnostics
                        diagnostics.extend(mapping_errors)
                        new_instances[instance_id] = instance_obj
                    else:
                        # No errors, use expanded instances
                        for new_name, expanded_mappings in expanded_instances_data:
                            new_instances[new_name] = replace(instance_obj, mappings=expanded_mappings)
                else:
                    new_instances[instance_id] = instance_obj
            elif has_bus:
                # Bus patterns for instances (future implementation)
                expanded_names, bus_diagnostics = self._expand_bus_pattern(
                    instance_id, instance_obj
                )
                diagnostics.extend(bus_diagnostics)
                if not bus_diagnostics:
                    for new_name in expanded_names:
                        new_instances[new_name] = replace(instance_obj)
                else:
                    new_instances[instance_id] = instance_obj
            else:
                # No pattern in instance name, but might have patterns in mappings
                expanded_mappings, mapping_diagnostics = self._expand_mapping_patterns(
                    instance_obj.mappings or {}, instance_id, instance_id, 0
                )
                diagnostics.extend(mapping_diagnostics)
                new_instances[instance_id] = replace(instance_obj, mappings=expanded_mappings)

        return new_instances, diagnostics

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

    def _has_bus_pattern(self, name: str) -> bool:
        """Check if name contains bus pattern [...]."""
        return '[' in name and ']' in name

    def _expand_literal_pattern(
        self, name: str, locatable: Locatable
    ) -> Tuple[List[str], List[Diagnostic]]:
        diagnostics: List[Diagnostic] = []
        match = re.search(r"^(.*?)<(.*?)>(.*?)$", name)
        if not match:
            return [name], []

        prefix, content, suffix = match.groups()

        if not content:
            diagnostics.append(
                self._create_diagnostic(
                    "E100",
                    "Empty Literal Pattern",
                    f"Pattern in '{name}' is empty.",
                    locatable,
                )
            )
            return [name], diagnostics

        items = [item.strip() for item in content.split(",")]

        # Check if ALL items are empty (which is invalid)
        if all(item == "" for item in items):
            diagnostics.append(
                self._create_diagnostic(
                    "E107",
                    "Empty Pattern Item",
                    f"Pattern in '{name}' contains only empty items.",
                    locatable,
                )
            )

        if len(items) == 1:
            diagnostics.append(
                self._create_diagnostic(
                    "E101",
                    "Single Item Pattern",
                    f"Pattern in '{name}' contains only a single item.",
                    locatable,
                )
            )

        if diagnostics:
            return [name], diagnostics

        return [f"{prefix}{item}{suffix}" for item in items], []

    def _expand_bus_pattern(
        self, name: str, locatable: Locatable
    ) -> Tuple[List[str], List[Diagnostic]]:
        diagnostics = []
        match = re.search(r"^(.*)\[(\d+):(\d+)\]$", name)
        if not match:
            return [name], diagnostics

        base_name, msb_str, lsb_str = match.groups()
        msb, lsb = int(msb_str), int(lsb_str)

        if msb == lsb:
            diagnostics.append(
                self._create_diagnostic(
                    "E104",
                    "Invalid Bus Range",
                    f"Bus range '{name}' has identical MSB and LSB.",
                    locatable,
                )
            )
            return [], diagnostics

        # Generate in the order specified by the pattern (MSB to LSB)
        if msb < lsb:
            # e.g., [0:3] → ["data0", "data1", "data2", "data3"]
            return [f"{base_name}{i}" for i in range(msb, lsb + 1)], diagnostics
        else:
            # e.g., [3:0] → ["data3", "data2", "data1", "data0"]  
            return [f"{base_name}{i}" for i in range(msb, lsb - 1, -1)], diagnostics

    def _create_diagnostic(
        self,
        code: str,
        title: str,
        details: str,
        locatable: Optional[Locatable] = None,
    ) -> Diagnostic:
        """Helper to create a diagnostic object with location info."""
        return Diagnostic(
            code=code,
            title=title,
            details=details,
            severity=DiagnosticSeverity.ERROR, # Defaulting to ERROR for now
            location=locatable,
        )

    def _expand_mapping_patterns(
        self, 
        mappings: Dict[str, str], 
        original_instance_id: str, 
        expanded_instance_id: str, 
        instance_index: int
    ) -> Tuple[Dict[str, str], List[Diagnostic]]:
        """
        Expand patterns in port-to-net mappings.
        
        For instance expansion, this creates the mappings for a single expanded instance.
        """
        expanded_mappings = {}
        diagnostics: List[Diagnostic] = []
        
        # Check if the instance itself had a pattern
        instance_has_pattern = self._has_literal_pattern(original_instance_id)
        
        for port_name, net_name in mappings.items():
            # Check for patterns in port and net names
            port_has_pattern = self._has_literal_pattern(port_name)
            net_has_pattern = self._has_literal_pattern(net_name)
            
            if port_has_pattern and net_has_pattern:
                # Both sides have patterns - order-sensitive expansion
                port_items = self._extract_literal_pattern(port_name)
                net_items = self._extract_literal_pattern(net_name)
                
                # Validate pattern counts match
                if port_items and net_items and len(port_items) != len(net_items):
                    diagnostics.append(
                        self._create_diagnostic(
                            "E105",
                            "Pattern Count Mismatch",
                            f"Pattern item counts must match: {len(port_items)} vs {len(net_items)}",
                        )
                    )
                    continue
                
                # For instance expansion, select the corresponding port and net
                if instance_has_pattern and port_items and net_items:
                    # Validate that mapping patterns match instance pattern count
                    instance_items = self._extract_literal_pattern(original_instance_id)
                    if instance_items:
                        if len(instance_items) != len(port_items):
                            diagnostics.append(
                                self._create_diagnostic(
                                    "E105",
                                    "Pattern Count Mismatch",
                                    f"Pattern item counts must match: {len(instance_items)} vs {len(port_items)}",
                                )
                            )
                            continue
                        if len(instance_items) != len(net_items):
                            diagnostics.append(
                                self._create_diagnostic(
                                    "E105",
                                    "Pattern Count Mismatch",
                                    f"Pattern item counts must match: {len(instance_items)} vs {len(net_items)}",
                                )
                            )
                            continue
                    
                    # Use the same index for port and net expansion
                    expanded_ports = self._expand_literal_pattern_simple(port_name)
                    expanded_nets = self._expand_literal_pattern_simple(net_name)
                    if instance_index < len(expanded_ports) and instance_index < len(expanded_nets):
                        expanded_mappings[expanded_ports[instance_index]] = expanded_nets[instance_index]
                elif port_items and net_items:
                    # No instance pattern, expand all port-net pairs
                    expanded_ports = self._expand_literal_pattern_simple(port_name)
                    expanded_nets = self._expand_literal_pattern_simple(net_name)
                    for exp_port, exp_net in zip(expanded_ports, expanded_nets):
                        expanded_mappings[exp_port] = exp_net
                    
            elif port_has_pattern and not net_has_pattern:
                # One-sided pattern (port side only)
                if instance_has_pattern:
                    # Validate that port pattern matches instance pattern count
                    instance_items = self._extract_literal_pattern(original_instance_id)
                    port_items = self._extract_literal_pattern(port_name)
                    if instance_items and port_items and len(instance_items) != len(port_items):
                        diagnostics.append(
                            self._create_diagnostic(
                                "E105",
                                "Pattern Count Mismatch", 
                                f"Pattern item counts must match: {len(instance_items)} vs {len(port_items)}",
                            )
                        )
                        continue
                    
                    # Use the corresponding port for this instance
                    expanded_ports = self._expand_literal_pattern_simple(port_name)
                    if instance_index < len(expanded_ports):
                        expanded_mappings[expanded_ports[instance_index]] = net_name
                else:
                    # No instance pattern, expand all ports to same net
                    expanded_ports = self._expand_literal_pattern_simple(port_name)
                    for exp_port in expanded_ports:
                        expanded_mappings[exp_port] = net_name
                    
            elif not port_has_pattern and net_has_pattern:
                # One-sided pattern (net side only)
                if instance_has_pattern:
                    # Validate that net pattern matches instance pattern count
                    instance_items = self._extract_literal_pattern(original_instance_id)
                    net_items = self._extract_literal_pattern(net_name)
                    if instance_items and net_items and len(instance_items) != len(net_items):
                        diagnostics.append(
                            self._create_diagnostic(
                                "E105",
                                "Pattern Count Mismatch",
                                f"Pattern item counts must match: {len(instance_items)} vs {len(net_items)}",
                            )
                        )
                        continue
                    
                    # Use the corresponding net for this instance
                    expanded_nets = self._expand_literal_pattern_simple(net_name)
                    if instance_index < len(expanded_nets):
                        expanded_mappings[port_name] = expanded_nets[instance_index]
                else:
                    # No instance pattern, map to first expanded net
                    expanded_nets = self._expand_literal_pattern_simple(net_name)
                    if expanded_nets:
                        expanded_mappings[port_name] = expanded_nets[0]
                
            else:
                # No patterns - keep as is
                expanded_mappings[port_name] = net_name
                
        return expanded_mappings, diagnostics

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

    def _expand_literal_pattern_simple(self, name: str) -> List[str]:
        """
        Expand literal pattern in name without diagnostics.
        
        Example: "in_<p,n>" -> ["in_p", "in_n"]
        Returns [name] if no pattern.
        """
        items = self._extract_literal_pattern(name)
        if items is None:
            return [name]
        
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