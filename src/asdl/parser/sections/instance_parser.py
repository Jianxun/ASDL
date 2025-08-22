"""
Instance definitions parser.

Extracts instance parsing functionality from the monolithic parser
with exact preservation of validation logic and P104/P201 diagnostic generation.
"""

from typing import Any, Dict, List, Optional, cast
from pathlib import Path

from ...data_structures import Instance
from ...diagnostics import Diagnostic, DiagnosticSeverity
from ..core.locatable_builder import LocatableBuilder, YAMLObject
from ..resolvers.field_validator import FieldValidator
from ..resolvers.dual_syntax_resolver import DualSyntaxResolver


class InstanceParser:
    """Handles instance definitions parsing with validation."""
    
    def __init__(self, locatable_builder: LocatableBuilder, field_validator: FieldValidator, 
                 dual_syntax_resolver: DualSyntaxResolver):
        """Initialize with dependencies."""
        self.locatable_builder = locatable_builder
        self.field_validator = field_validator
        self.dual_syntax_resolver = dual_syntax_resolver
    
    def parse(self, data: Any, diagnostics: List[Diagnostic], file_path: Optional[Path]) -> Optional[Dict[str, Instance]]:
        """
        Parse instances section.
        
        Exact implementation from _parse_instances() method.
        Preserves P104 required model field validation.
        Preserves dual syntax parameter resolution.
        Preserves P201 unknown field validation.
        
        Args:
            data: Instances section data
            diagnostics: List to append diagnostics to
            file_path: Optional file path for location tracking
            
        Returns:
            Dictionary of instance definitions or None if no instances
        """
        if not data:
            return None
        
        instances = {}
        yaml_data = cast(YAMLObject, data)
        for instance_name, instance_data in yaml_data.items():
            loc = self.locatable_builder.from_yaml_key(yaml_data, instance_name, file_path)

            model_val = instance_data.get('model')
            if not model_val:
                diagnostics.append(Diagnostic(
                    code="P104", 
                    title="Missing Required Field", 
                    details=f"Instance '{instance_name}' is missing the required 'model' field.",
                    severity=DiagnosticSeverity.ERROR,
                    location=loc
                ))
                continue

            # Resolve parameters with dual syntax support
            parameters = self.dual_syntax_resolver.resolve_parameters(
                instance_data, f"Instance '{instance_name}'", diagnostics, loc
            )
            
            # Check for unknown fields in instance
            self.field_validator.validate_unknown_fields(
                instance_data,
                f"Instance '{instance_name}'",
                ['model', 'mappings', 'doc', 'parameters', 'params', 'metadata'],
                diagnostics,
                loc
            )
            
            instances[instance_name] = Instance(
                **loc.__dict__,
                model=model_val,
                mappings=instance_data.get('mappings'),
                doc=instance_data.get('doc'),
                parameters=parameters,
                metadata=instance_data.get('metadata')
            )
        return instances