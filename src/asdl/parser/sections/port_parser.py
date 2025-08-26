"""
Port definitions parser.

Extracts port parsing functionality from the monolithic parser
with exact preservation of validation logic and P104/P105/P201 diagnostic generation.
"""

from typing import Any, Dict, List, Optional, cast
from pathlib import Path

from ...data_structures import Port, PortDirection, SignalType, PortConstraints
from ...diagnostics import Diagnostic, DiagnosticSeverity
from ..core.locatable_builder import LocatableBuilder, YAMLObject
from ..resolvers.field_validator import FieldValidator


class PortParser:
    """Handles port definitions parsing with validation."""
    
    def __init__(self, locatable_builder: LocatableBuilder, field_validator: FieldValidator):
        """Initialize with dependencies."""
        self.locatable_builder = locatable_builder
        self.field_validator = field_validator
    
    def parse(self, data: Any, diagnostics: List[Diagnostic], file_path: Optional[Path]) -> Optional[Dict[str, Port]]:
        """
        Parse ports section.
        
        Exact implementation from _parse_ports() method.
        Preserves P104 required field validation (dir only, type is optional).
        Preserves P105 port parsing error handling.
        Preserves P201 unknown field validation.
        Preserves enum conversion logic.
        
        Args:
            data: Ports section data
            diagnostics: List to append diagnostics to
            file_path: Optional file path for location tracking
            
        Returns:
            Dictionary of port definitions or None if no ports
        """
        if not data:
            return None
        
        ports = {}
        yaml_data = cast(YAMLObject, data)
        for port_name, port_data in yaml_data.items():
            loc = self.locatable_builder.from_yaml_key(yaml_data, port_name, file_path)
            
            # Validate required fields
            dir_val = port_data.get('dir')
            if not dir_val:
                diagnostics.append(Diagnostic(
                    code="P0240",
                    title="Missing Port Direction",
                    details=f"Port '{port_name}' is missing the required 'dir' field.",
                    severity=DiagnosticSeverity.ERROR,
                    location=loc
                ))
                continue
    
            type_val = port_data.get('type')  # Optional field

            # Check for unknown fields in port
            self.field_validator.validate_unknown_fields(
                port_data,
                f"Port '{port_name}'",
                ['dir', 'type', 'constraints', 'metadata'],
                diagnostics,
                loc
            )

            try:
                ports[port_name] = Port(
                    **loc.__dict__,
                    dir=PortDirection(dir_val.lower()),
                    type=SignalType(type_val.lower()) if type_val else None,
                    constraints=self._parse_constraints(port_data.get('constraints')),
                    metadata=port_data.get('metadata')
                )
            except Exception as e:
                diagnostics.append(Diagnostic(
                    code="P0205",
                    title="Port Parsing Error",
                    details=f"An error occurred while parsing port '{port_name}': {e}",
                    severity=DiagnosticSeverity.ERROR,
                    location=loc,
                    suggestion="Review the port definition for correctness and try again later."
                ))
        return ports
    
    def _parse_constraints(self, data: Any) -> Optional[PortConstraints]:
        """
        Parse port constraints.
        
        Exact implementation from _parse_constraints() method.
        Currently a placeholder implementation.
        
        Args:
            data: Constraints data
            
        Returns:
            PortConstraints object or None if no constraints
        """
        if not data:
            return None
        return PortConstraints(constraints=data)