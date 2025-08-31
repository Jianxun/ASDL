"""
Port definitions parser.

Extracts port parsing functionality from the monolithic parser
with exact preservation of validation logic and XCCSS diagnostic generation (P0240/P0205/P0702; P0511/P0512).
"""

from typing import Any, Dict, List, Optional, cast
from pathlib import Path

from ...data_structures import Port, PortDirection, PortType
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
        Preserves P0240 required field validation (dir only, type is optional).
        Preserves P0205 generic port parsing error handling (fallback).
        Preserves P0702 unknown field validation.
        Adds explicit enum conversion validation P0511/P0512.
        
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
                ['dir', 'type', 'metadata'],
                diagnostics,
                loc
            )

            # Enum validation with explicit diagnostics
            dir_enum = None
            type_enum = None
            try:
                dir_enum = PortDirection(dir_val.lower())
            except Exception:
                diagnostics.append(Diagnostic(
                    code="P0511",
                    title="Invalid Port Direction Enum",
                    details=f"Port direction must be one of: in, out, in_out. Found '{dir_val}'.",
                    severity=DiagnosticSeverity.ERROR,
                    location=loc,
                    suggestion="Use one of: in, out, in_out."
                ))
                # Skip creating this port due to invalid direction
                continue

            if type_val is not None:
                try:
                    type_enum = PortType(str(type_val).lower())
                except Exception:
                    diagnostics.append(Diagnostic(
                        code="P0512",
                        title="Invalid Port Type Enum",
                        details=f"Port type must be one of: signal, power, ground, bias, control. Found '{type_val}'.",
                        severity=DiagnosticSeverity.ERROR,
                        location=loc,
                        suggestion="Use one of: signal, power, ground, bias, control."
                    ))
                    # Skip creating this port due to invalid type
                    continue

            try:
                ports[port_name] = Port(
                    **loc.__dict__,
                    dir=dir_enum,
                    type=type_enum if type_enum is not None else PortType.SIGNAL,
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
    
    # Port constraints are deprecated; no-op retained intentionally for backward compatibility in callers.