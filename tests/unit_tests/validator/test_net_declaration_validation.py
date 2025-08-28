"""
Test net declaration validation functionality.

Tests validation that all nets used in instance mappings are properly declared.
"""

import pytest
from src.asdl.validator import ASDLValidator
from src.asdl.data_structures import Instance, Module, Port, PortDirection, PortType
from src.asdl.diagnostics import Diagnostic, DiagnosticSeverity


class TestNetDeclarationValidation:
    """Test net declaration validation logic."""
    
    def test_valid_net_declarations_pass(self):
        """Test that valid net declarations pass validation."""
        validator = ASDLValidator()
        
        # Create a module with ports and internal nets
        module = Module(
            ports={
                "in": Port(dir=PortDirection.IN, type=PortType.SIGNAL),
                "out": Port(dir=PortDirection.OUT, type=PortType.SIGNAL)
            },
            internal_nets=["bias", "intermediate"],
            instances={
                "R1": Instance(
                    model="resistor",
                    mappings={"plus": "in", "minus": "bias"}
                ),
                "R2": Instance(
                    model="resistor", 
                    mappings={"plus": "bias", "minus": "out"}
                )
            }
        )
        
        # Validation should pass - no diagnostics returned
        diagnostics = validator.validate_net_declarations(module, "test_module")
        assert len(diagnostics) == 0
    
    def test_undeclared_nets_generate_warnings(self):
        """Test that undeclared nets generate warning diagnostics."""
        validator = ASDLValidator()
        
        # Create a module with only ports (no internal nets)
        module = Module(
            ports={
                "in": Port(dir=PortDirection.IN, type=PortType.SIGNAL),
                "out": Port(dir=PortDirection.OUT, type=PortType.SIGNAL)
            },
            instances={
                "R1": Instance(
                    model="resistor",
                    mappings={"plus": "in", "minus": "undeclared_net"}
                )
            }
        )
        
        # Validation should generate warning for undeclared net
        diagnostics = validator.validate_net_declarations(module, "test_module")
        assert len(diagnostics) == 1
        assert diagnostics[0].severity == DiagnosticSeverity.WARNING
        assert diagnostics[0].code == "V0401"
        assert "undeclared_net" in diagnostics[0].details
        assert "test_module" in diagnostics[0].details 