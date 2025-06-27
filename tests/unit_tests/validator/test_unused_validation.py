"""
Test unused components validation functionality.

Tests validation that identifies unused models and modules.
"""

import pytest
from src.asdl.validator import ASDLValidator
from src.asdl.data_structures import (
    ASDLFile, FileInfo, Instance, Module, DeviceModel, 
    Port, PortDirection, SignalType, PrimitiveType
)
from src.asdl.diagnostics import Diagnostic, DiagnosticSeverity


class TestUnusedValidation:
    """Test unused components validation logic."""
    
    def test_all_components_used_no_warnings(self):
        """Test that when all components are used, no warnings are generated."""
        validator = ASDLValidator()
        
        # Create ASDL file with all components used
        asdl_file = ASDLFile(
            file_info=FileInfo(top_module="test_circuit"),
            models={
                "resistor": DeviceModel(
                    type=PrimitiveType.SPICE_DEVICE,
                    ports=["plus", "minus"],
                    device_line="R{name} {plus} {minus} {value}"
                )
            },
            modules={
                "test_circuit": Module(
                    ports={
                        "in": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                        "out": Port(dir=PortDirection.OUT, type=SignalType.VOLTAGE)
                    },
                    instances={
                        "R1": Instance(
                            model="resistor",
                            mappings={"plus": "in", "minus": "out"}
                        )
                    }
                )
            }
        )
        
        # Validation should pass - no diagnostics returned
        diagnostics = validator.validate_unused_components(asdl_file)
        assert len(diagnostics) == 0
    
    def test_unused_model_generates_warning(self):
        """Test that unused models generate warning diagnostics."""
        validator = ASDLValidator()
        
        # Create ASDL file with unused model
        asdl_file = ASDLFile(
            file_info=FileInfo(top_module="test_circuit"),
            models={
                "resistor": DeviceModel(
                    type=PrimitiveType.SPICE_DEVICE,
                    ports=["plus", "minus"],
                    device_line="R{name} {plus} {minus} {value}"
                ),
                "unused_capacitor": DeviceModel(  # This one is unused
                    type=PrimitiveType.SPICE_DEVICE,
                    ports=["plus", "minus"],
                    device_line="C{name} {plus} {minus} {value}"
                )
            },
            modules={
                "test_circuit": Module(
                    instances={
                        "R1": Instance(
                            model="resistor",
                            mappings={"plus": "in", "minus": "out"}
                        )
                    }
                )
            }
        )
        
        # Validation should generate warning for unused model
        diagnostics = validator.validate_unused_components(asdl_file)
        assert len(diagnostics) == 1
        assert diagnostics[0].severity == DiagnosticSeverity.WARNING
        assert "unused_capacitor" in diagnostics[0].details
        assert "unused models" in diagnostics[0].details.lower() 