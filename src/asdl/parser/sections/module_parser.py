"""
Module definitions parser.

Extracts module parsing functionality from the monolithic parser
with exact preservation of unified architecture logic and P107/P108 diagnostic generation.
"""

from typing import Any, Dict, List, Optional, cast
from pathlib import Path

from ...data_structures import Module
from ...diagnostics import Diagnostic, DiagnosticSeverity
from ..core.locatable_builder import LocatableBuilder, YAMLObject
from ..resolvers.field_validator import FieldValidator
from ..resolvers.dual_syntax_resolver import DualSyntaxResolver
from .port_parser import PortParser
from .instance_parser import InstanceParser


class ModuleParser:
    """Handles module parsing orchestration with unified architecture."""
    
    def __init__(self, port_parser: PortParser, instance_parser: InstanceParser,
                 dual_syntax_resolver: DualSyntaxResolver, field_validator: FieldValidator,
                 locatable_builder: LocatableBuilder):
        """Initialize with dependencies."""
        self.port_parser = port_parser
        self.instance_parser = instance_parser
        self.dual_syntax_resolver = dual_syntax_resolver
        self.field_validator = field_validator
        self.locatable_builder = locatable_builder
    
    def parse(self, data: Any, diagnostics: List[Diagnostic], file_path: Optional[Path]) -> Dict[str, Module]:
        """
        Parse modules section.
        
        Exact implementation from _parse_modules() method.
        Preserves P107 module type conflict validation (spice_template XOR instances).
        Preserves P108 incomplete module validation.
        Preserves dual syntax resolution for parameters/variables.
        Preserves unknown field validation.
        Delegates to port_parser and instance_parser.
        Preserves Module construction logic.
        
        Args:
            data: Modules section data
            diagnostics: List to append diagnostics to
            file_path: Optional file path for location tracking
            
        Returns:
            Dictionary of module definitions
        """
        if not self.field_validator.validate_section_is_dict(data, 'modules', diagnostics, file_path):
            return {}

        modules = {}
        yaml_data = cast(YAMLObject, data)
        for module_id, module_data in yaml_data.items():
            loc = self.locatable_builder.from_yaml_key(yaml_data, module_id, file_path)
            
            # Parse all fields
            spice_template = module_data.get('spice_template')
            instances = self.instance_parser.parse(module_data.get('instances'), diagnostics, file_path)
            
            # Validate mutual exclusion: spice_template XOR instances
            has_spice_template = spice_template is not None
            has_instances = instances is not None
            
            if has_spice_template and has_instances:
                diagnostics.append(Diagnostic(
                    code="P107",
                    title="Module Type Conflict",
                    details=f"Module '{module_id}' cannot have both 'spice_template' and 'instances'. Choose one: primitive (spice_template) or hierarchical (instances).",
                    severity=DiagnosticSeverity.ERROR,
                    location=loc,
                    suggestion="Remove either 'spice_template' (to make hierarchical) or 'instances' (to make primitive)."
                ))
                continue
                
            if not has_spice_template and not has_instances:
                diagnostics.append(Diagnostic(
                    code="P108",
                    title="Incomplete Module Definition",
                    details=f"Module '{module_id}' must have either 'spice_template' (primitive) or 'instances' (hierarchical).",
                    severity=DiagnosticSeverity.ERROR,
                    location=loc,
                    suggestion="Add either 'spice_template' for primitive modules or 'instances' for hierarchical modules."
                ))
                continue
            
            # Resolve parameters and variables with dual syntax support
            parameters = self.dual_syntax_resolver.resolve_parameters(
                module_data, f"Module '{module_id}'", diagnostics, loc
            )
            variables = self.dual_syntax_resolver.resolve_variables(
                module_data, f"Module '{module_id}'", diagnostics, loc
            )
            
            # Check for unknown fields in module
            self.field_validator.validate_unknown_fields(
                module_data, 
                f"Module '{module_id}'",
                ['doc', 'ports', 'internal_nets', 'parameters', 'params', 'variables', 'vars', 
                 'spice_template', 'instances', 'pdk', 'metadata'],
                diagnostics, 
                loc
            )
            
            modules[module_id] = Module(
                **loc.__dict__,
                doc=module_data.get('doc'),
                ports=self.port_parser.parse(module_data.get('ports'), diagnostics, file_path),
                internal_nets=module_data.get('internal_nets'),
                parameters=parameters,
                variables=variables,
                spice_template=spice_template,
                instances=instances,
                pdk=module_data.get('pdk'),
                metadata=module_data.get('metadata')
            )
        return modules