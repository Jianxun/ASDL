"""
Test port mapping validation functionality.

Tests the validation of instance port mappings against module port definitions.
"""

import pytest
from src.asdl.validator import ASDLValidator
from src.asdl.data_structures import Instance, Module, Port, PortDirection, PortType
from src.asdl.diagnostics import Diagnostic, DiagnosticSeverity


class TestPortMappingValidation:
    """Test port mapping validation logic."""
    
    def test_valid_port_mapping_passes(self):
        """Test that valid port mappings pass validation."""
        validator = ASDLValidator()
        
        # Create a module with two ports
        module = Module(
            ports={
                "in": Port(dir=PortDirection.IN, type=PortType.SIGNAL),
                "out": Port(dir=PortDirection.OUT, type=PortType.SIGNAL)
            }
        )
        
        # Create an instance that maps to these ports
        instance = Instance(
            model="test_module",
            mappings={"in": "signal_in", "out": "signal_out"}
        )
        
        # Validation should pass - no diagnostics returned
        diagnostics = validator.validate_port_mappings("inst1", instance, module)
        assert len(diagnostics) == 0
    
    def test_invalid_port_mapping_fails(self):
        """Test that invalid port mappings generate error diagnostics."""
        validator = ASDLValidator()
        
        # Create a module with only one port
        module = Module(
            ports={
                "in": Port(dir=PortDirection.IN, type=PortType.SIGNAL)
            }
        )
        
        # Create an instance that maps to non-existent port
        instance = Instance(
            model="test_module",
            mappings={"in": "signal_in", "invalid_port": "signal_out"}
        )
        
        # Validation should fail - return error diagnostic
        diagnostics = validator.validate_port_mappings("inst1", instance, module)
        assert len(diagnostics) == 1
        assert diagnostics[0].severity == DiagnosticSeverity.ERROR
        assert "invalid_port" in diagnostics[0].details
        assert "inst1" in diagnostics[0].details 