from typing import List, Tuple, Dict, Any, Optional
from dataclasses import replace

from asdl.data_structures import ASDLFile, Module, Port, Locatable, Instance
from asdl.diagnostics import Diagnostic, DiagnosticSeverity


class Elaborator:
    """
    The Elaborator is responsible for transforming the abstract, parsed ASDL
    structure into a concrete, fully specified design. It handles pattern
    expansion and parameter resolution.
    """

    def elaborate(self, asdl_file: ASDLFile) -> Tuple[ASDLFile, List[Diagnostic]]:
        """
        Elaborates an ASDL file by performing pattern expansion and parameter
        resolution.

        Args:
            asdl_file: The parsed ASDL file to elaborate.

        Returns:
            A tuple containing the elaborated ASDL file and a list of
            diagnostics generated during elaboration.
        """
        diagnostics: List[Diagnostic] = []
        
        expanded_modules = {}
        for module_name, module in asdl_file.modules.items():
            expanded_module, module_diagnostics = self._expand_module_patterns(module)
            expanded_modules[module_name] = expanded_module
            diagnostics.extend(module_diagnostics)

        elaborated_file = ASDLFile(
            file_info=asdl_file.file_info,
            models=asdl_file.models,
            modules=expanded_modules,
            metadata=asdl_file.metadata,
        )

        return elaborated_file, diagnostics

    def _expand_module_patterns(self, module: Module) -> Tuple[Module, List[Diagnostic]]:
        """
        Expand patterns within a single module.
        """
        expanded_ports, port_diagnostics = self._expand_port_patterns(module.ports or {})
        expanded_instances, instance_diagnostics = self._expand_instance_patterns(module.instances or {})

        diagnostics = port_diagnostics + instance_diagnostics

        new_module = Module(
            doc=module.doc,
            ports=expanded_ports,
            internal_nets=module.internal_nets,
            parameters=module.parameters,
            instances=expanded_instances,
            metadata=module.metadata,
            start_line=module.start_line,
            start_col=module.start_col
        )
        return new_module, diagnostics

    def _expand_port_patterns(self, ports: Dict[str, Port]) -> Tuple[Dict[str, Port], List[Diagnostic]]:
        """
        Expand patterns in port definitions.
        """
        expanded_ports = {}
        diagnostics: List[Diagnostic] = []
        
        for port_name, port in ports.items():
            if self._is_mixed_pattern(port_name):
                diagnostics.append(Diagnostic(
                    code="E103",
                    title="Mixed Pattern Types",
                    details=f"The name '{port_name}' contains both a literal pattern ('<>') and a bus pattern ('[]').",
                    suggestion="Use either a literal pattern or a bus pattern for a single name, not both.",
                    severity=DiagnosticSeverity.ERROR,
                    location=Locatable(start_line=port.start_line, start_col=port.start_col)
                ))
                expanded_ports[port_name] = port # Keep original on error
                continue
            
            if self._has_literal_pattern(port_name):
                expanded_names, validation_diagnostics = self._expand_literal_pattern(port_name, port)
                if validation_diagnostics:
                    diagnostics.extend(validation_diagnostics)
                    expanded_ports[port_name] = port # Keep original on error
                elif expanded_names:
                    for expanded_name in expanded_names:
                        expanded_ports[expanded_name] = port
            elif self._has_bus_pattern(port_name):
                expanded_names, validation_diagnostics = self._expand_bus_pattern(port_name, port)
                if validation_diagnostics:
                    diagnostics.extend(validation_diagnostics)
                    expanded_ports[port_name] = port # Keep original on error
                elif expanded_names:
                    for expanded_name in expanded_names:
                        expanded_ports[expanded_name] = port
            else:
                expanded_ports[port_name] = port
                
        return expanded_ports, diagnostics

    def _expand_instance_patterns(self, instances: Dict[str, Instance]) -> Tuple[Dict[str, Instance], List[Diagnostic]]:
        """
        Expand patterns in instance definitions.
        """
        expanded_instances = {}
        diagnostics: List[Diagnostic] = []

        for instance_id, instance in instances.items():
            if self._is_mixed_pattern(instance_id):
                diagnostics.append(Diagnostic(
                    code="E103",
                    title="Mixed Pattern Types",
                    details=f"The instance name '{instance_id}' contains both a literal pattern ('<>') and a bus pattern ('[]').",
                    suggestion="Use either a literal pattern or a bus pattern for a single name, not both.",
                    severity=DiagnosticSeverity.ERROR,
                    location=Locatable(start_line=instance.start_line, start_col=instance.start_col)
                ))
                expanded_instances[instance_id] = instance
                continue

            if self._has_literal_pattern(instance_id):
                expanded_ids, id_diags = self._expand_literal_pattern(instance_id, instance)
                if id_diags:
                    diagnostics.extend(id_diags)
                    expanded_instances[instance_id] = instance
                    continue

                if expanded_ids:
                    for expanded_id in expanded_ids:
                        expanded_mappings, map_diags = self._expand_mapping_patterns(
                            instance.mappings,
                            instance_id,
                            expanded_id,
                            instance
                        )
                        if map_diags:
                            diagnostics.extend(map_diags)
                            expanded_instances[instance_id] = instance
                            break

                        expanded_instances[expanded_id] = replace(
                            instance,
                            mappings=expanded_mappings
                        )
            else:
                expanded_mappings, map_diags = self._expand_mapping_patterns(
                    instance.mappings,
                    instance_id,
                    instance_id,
                    instance
                )
                if map_diags:
                    diagnostics.extend(map_diags)
                    expanded_instances[instance_id] = instance
                else:
                    expanded_instances[instance_id] = replace(
                        instance,
                        mappings=expanded_mappings
                    )

        return expanded_instances, diagnostics

    def _expand_mapping_patterns(self, mappings: Dict[str, str],
                                original_instance_id: str,
                                expanded_instance_id: str,
                                locatable: Instance) -> Tuple[Dict[str, str], List[Diagnostic]]:
        expanded_mappings = {}
        diagnostics: List[Diagnostic] = []

        instance_items = self._extract_literal_pattern(original_instance_id)

        # Validate pattern counts
        for port_name, net_name in mappings.items():
            net_items = self._extract_literal_pattern(net_name)
            diags = self._validate_pattern_counts(instance_items, net_items, locatable)
            if diags:
                diagnostics.extend(diags)
        
        if diagnostics:
            return mappings, diagnostics


        # Expand patterns
        instance_index = -1
        if instance_items:
            try:
                # The expanded_ids are the same as instance_items, but with prefix/suffix
                expanded_ids, _ = self._expand_literal_pattern(original_instance_id, locatable)
                if expanded_ids:
                    instance_index = expanded_ids.index(expanded_instance_id)
            except (ValueError, IndexError):
                pass
        
        for port_name, net_name in mappings.items():
            net_items = self._extract_literal_pattern(net_name)

            if net_items is None:
                expanded_mappings[port_name] = net_name
                continue
            
            if instance_index != -1 and net_items and instance_items and len(net_items) == len(instance_items):
                expanded_net_names, _ = self._expand_literal_pattern(net_name, locatable)
                if expanded_net_names:
                    expanded_mappings[port_name] = expanded_net_names[instance_index]
            elif net_items and len(net_items) == 1:
                 expanded_mappings[port_name] = net_items[0]
            else:
                expanded_mappings[port_name] = net_name
                
        return expanded_mappings, diagnostics

    def _validate_pattern_counts(self, left_items: Optional[List[str]],
                               right_items: Optional[List[str]],
                               locatable: Instance) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []
        if left_items is None or right_items is None:
            return diagnostics
        
        if len(left_items) != len(right_items):
            diagnostics.append(Diagnostic(
                code="E102",
                title="Pattern Count Mismatch",
                details=f"The number of items in the instance pattern ({len(left_items)}) does not match the number of items in the net pattern ({len(right_items)}).",
                severity=DiagnosticSeverity.ERROR,
                location=Locatable(start_line=locatable.start_line, start_col=locatable.start_col),
                suggestion="Ensure that patterns being mapped to each other have the same number of comma-separated items."
            ))
        return diagnostics

    def _is_mixed_pattern(self, name: str) -> bool:
        """Check if name contains both literal and bus patterns."""
        has_literal_brackets = '<' in name and '>' in name
        has_bus_brackets = '[' in name and ']' in name
        return has_literal_brackets and has_bus_brackets

    def _has_bus_pattern(self, name: str) -> bool:
        """Check if name contains bus pattern [...].""" 
        return '[' in name and ']' in name and ':' in name
    
    def _has_literal_pattern(self, name: str) -> bool:
        """Check if name contains literal pattern <...>."""
        # 1. Must have both < and > to be considered a potential pattern.
        if not ('<' in name and '>' in name):
            return False
        
        # 2. Ensure that the brackets are in the correct order (< comes before >).
        start = name.find('<')
        end = name.find('>')
        if start == -1 or end == -1 or start >= end:
            return False
            
        # 3. Enforce that only one pattern is allowed per name.
        #    This prevents ambiguity from multiple patterns like `sig<p,n><0,1>`.
        remaining = name[end+1:]
        if '<' in remaining and '>' in remaining:
            return False
            
        # 4. Prevent mixing pattern types, e.g., bus syntax `[]` inside a literal pattern `<>`.
        #    This avoids syntactical ambiguity like `in<bus[0],bus[1]>`.
        pattern_content = name[start+1:end]
        if '[' in pattern_content and ']' in pattern_content:
            return False
            
        return True
    
    def _extract_literal_pattern(self, name: str) -> Optional[List[str]]:
        """
        Extract literal pattern items from name.
        """
        if not self._has_literal_pattern(name):
            return None
        
        start = name.find('<')
        end = name.find('>')
        pattern_content = name[start+1:end]
        
        if not pattern_content:
            return []
        
        items = [item.strip() for item in pattern_content.split(',')]
        return items
    
    def _expand_literal_pattern(self, name: str, locatable: Port | Instance) -> Tuple[Optional[List[str]], List[Diagnostic]]:
        """
        Expand literal pattern in name.
        """
        diagnostics: List[Diagnostic] = []
        items = self._extract_literal_pattern(name)
        
        if items is None:
            return [name], []

        location = Locatable(start_line=locatable.start_line, start_col=locatable.start_col)

        if not items:
            diagnostics.append(Diagnostic(
                code="E100",
                title="Empty Pattern",
                details="A literal pattern `<>` cannot be empty. It must contain items to expand.",
                severity=DiagnosticSeverity.ERROR,
                location=location,
                suggestion="Provide at least two comma-separated items inside the pattern brackets, like `in<p,n>`."
            ))
        elif len(items) < 2:
            diagnostics.append(Diagnostic(
                code="E101",
                title="Single-Item Pattern",
                details="A literal pattern must contain at least two items to be meaningful. A pattern with one item provides no expansion benefit.",
                severity=DiagnosticSeverity.ERROR,
                location=location,
                suggestion="Ensure the pattern contains at least two items, like `in<p,n>`, or remove the pattern syntax if only a single port is needed (`in_p`)."
            ))
        elif all(item == "" for item in items):
            diagnostics.append(Diagnostic(
                code="E107",
                title="Empty Pattern Item",
                details="All items in a literal pattern were empty strings.",
                severity=DiagnosticSeverity.ERROR,
                location=location,
                suggestion="Ensure that at least one item inside the pattern is a non-empty string."
            ))

        if diagnostics:
            return None, diagnostics
        
        start = name.find('<')
        end = name.find('>')
        prefix = name[:start]
        suffix = name[end+1:]
        
        expanded_names = [f"{prefix}{item}{suffix}" for item in items]
        return expanded_names, []
    
    def _expand_bus_pattern(self, name: str, locatable: Port | Instance) -> Tuple[Optional[List[str]], List[Diagnostic]]:
        """
        Expand bus pattern in name (placeholder).
        """
        # Future implementation
        return [name], [] 