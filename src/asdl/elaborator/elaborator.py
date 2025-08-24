from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path
from dataclasses import replace

from ..data_structures import ASDLFile, Module, Port, Locatable, Instance
from ..diagnostics import Diagnostic, DiagnosticSeverity
from .pattern_expander import PatternExpander
from .variable_resolver import VariableResolver
from .import_ import ImportResolver


class Elaborator:
    """
    The Elaborator is responsible for transforming the raw, parsed ASDL data
    structures into a fully specified, elaborated design. It handles:
    - Pattern Expansion (both literal <> and bus [])
    - Parameter Resolution (future implementation)
    """

    def __init__(self):
        self.pattern_expander = PatternExpander()
        self.variable_resolver = VariableResolver()
        self._import_resolver = ImportResolver()

    def elaborate(
        self, asdl_file: ASDLFile
    ) -> Tuple[Optional[ASDLFile], List[Diagnostic]]:
        """
        Elaborates an ASDL file by performing pattern expansion.
        """
        diagnostics: List[Diagnostic] = []

        elaborated_file = replace(asdl_file, modules={})
        for name, module in asdl_file.modules.items():
            try:
                elaborated_module, module_diagnostics = self._elaborate_module(module, name)
                diagnostics.extend(module_diagnostics)
                elaborated_file.modules[name] = elaborated_module
            except Exception as e:
                raise ValueError(f"Error processing module '{name}': {e}") from e

        return elaborated_file, diagnostics

    def elaborate_with_imports(
        self,
        main_file_path: Path,
        search_paths: Optional[List[Path]] = None,
        top: Optional[str] = None,
    ) -> Tuple[Optional[ASDLFile], List[Diagnostic]]:
        """
        Phase 0 skeleton orchestrator: resolve imports, then run pattern and variable phases.

        Args:
            main_file_path: Path to the main .asdl file
            search_paths: Optional list of search roots used for import resolution
            top: Optional override for top module name

        Returns:
            Tuple of (elaborated_file, diagnostics)
        """
        # Phase 0: Import resolution (includes parsing of main file)
        flattened_file, diagnostics = self._import_resolver.resolve_imports(
            main_file_path, search_paths
        )

        if flattened_file is None:
            return None, diagnostics

        # Apply top module override if provided
        if top:
            flattened_file.file_info.top_module = top

        # Phase 1 & 2: Pattern expansion and variable resolution (existing flow)
        elaborated_file, elab_diags = self.elaborate(flattened_file)
        diagnostics.extend(elab_diags)
        return elaborated_file, diagnostics

    def _elaborate_module(self, module: Module, module_name: str) -> Tuple[Module, List[Diagnostic]]:
        """
        Expand patterns and resolve variables within a single module.
        """
        diagnostics: List[Diagnostic] = []
        # Create a deep copy to avoid modifying the original during iteration
        replace_args = {
            'ports': {name: replace(port) for name, port in (module.ports or {}).items()},
        }
        
        # Only set instances if the module actually has instances (preserve None for primitives)
        if module.instances is not None:
            replace_args['instances'] = {
                name: replace(inst) for name, inst in module.instances.items()
            }
        
        module_copy = replace(module, **replace_args)

        expanded_ports, port_diagnostics = self._expand_ports(module_copy.ports)
        diagnostics.extend(port_diagnostics)
        module_copy.ports = expanded_ports

        # Only expand instances if the module actually has instances (preserve None for primitives)
        if module_copy.instances is not None:
            expanded_instances, instance_diagnostics = self._expand_instances(module_copy.instances)
            diagnostics.extend(instance_diagnostics)
            module_copy.instances = expanded_instances
            
            # Resolve variable references in instance parameters using module variables
            if module_copy.variables:
                resolved_instances, variable_diagnostics = self.variable_resolver.resolve_instance_variables(
                    module_copy.instances, module_copy.variables, module_name
                )
                diagnostics.extend(variable_diagnostics)
                module_copy.instances = resolved_instances

        return module_copy, diagnostics

    def _expand_ports(
        self, ports: Optional[Dict[str, Port]]
    ) -> Tuple[Dict[str, Port], List[Diagnostic]]:
        if not ports:
            return {}, []

        new_ports = {}
        diagnostics: List[Diagnostic] = []

        for port_name, port_obj in ports.items():
            has_literal = self.pattern_expander.has_literal_pattern(port_name)
            has_bus = self.pattern_expander.has_bus_pattern(port_name)

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
                expanded_names, literal_diagnostics = self.pattern_expander.expand_literal_pattern(
                    port_name, port_obj
                )
                diagnostics.extend(literal_diagnostics)
                if not literal_diagnostics:
                    for new_name in expanded_names:
                        new_ports[new_name] = replace(port_obj)
                else:
                    new_ports[port_name] = port_obj
            elif has_bus:
                expanded_names, bus_diagnostics = self.pattern_expander.expand_bus_pattern(
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
            has_literal = self.pattern_expander.has_literal_pattern(instance_id)
            has_bus = self.pattern_expander.has_bus_pattern(instance_id)

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
                expanded_names, literal_diagnostics = self.pattern_expander.expand_literal_pattern(
                    instance_id, instance_obj
                )
                diagnostics.extend(literal_diagnostics)
                if not literal_diagnostics:
                    # Try to expand mappings for all instances first to check for errors
                    mapping_errors = []
                    expanded_instances_data = []
                    
                    for i, new_name in enumerate(expanded_names):
                        # Expand mappings for this instance
                        expanded_mappings, mapping_diagnostics = self.pattern_expander.expand_mapping_patterns(
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
                expanded_names, bus_diagnostics = self.pattern_expander.expand_bus_pattern(
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
                expanded_mappings, mapping_diagnostics = self.pattern_expander.expand_mapping_patterns(
                    instance_obj.mappings or {}, instance_id, instance_id, 0
                )
                diagnostics.extend(mapping_diagnostics)
                new_instances[instance_id] = replace(instance_obj, mappings=expanded_mappings)

        return new_instances, diagnostics

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