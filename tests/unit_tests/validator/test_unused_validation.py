"""
Test unused components validation functionality.

Tests validation that identifies unused models and modules.
"""

import pytest
from src.asdl.validator import ASDLValidator
from src.asdl.data_structures import (
    ASDLFile, FileInfo, Instance, Module
)
from src.asdl.diagnostics import Diagnostic, DiagnosticSeverity


class TestUnusedValidation:
    """Test unused components validation logic."""
    
    def test_all_modules_used_no_warnings(self):
        """No warnings when all modules are used (top and its children)."""
        validator = ASDLValidator()
        
        # Create ASDL file with all modules used
        asdl_file = ASDLFile(
            file_info=FileInfo(top_module="top"),
            modules={
                "child": Module(instances={}),
                "top": Module(
                    instances={
                        "U1": Instance(model="child", mappings={})
                    }
                )
            }
        )
        
        # Validation should pass - no diagnostics returned
        diagnostics = validator.validate_unused_components(asdl_file)
        assert len(diagnostics) == 0
    
    def test_unused_module_generates_warning(self):
        """Warn when a defined module is never instantiated (excluding top)."""
        validator = ASDLValidator()
        
        # Create ASDL file with an unused module
        asdl_file = ASDLFile(
            file_info=FileInfo(top_module="top"),
            modules={
                "used_child": Module(instances={}),
                "unused_child": Module(instances={}),
                "top": Module(
                    instances={
                        "U1": Instance(model="used_child", mappings={})
                    }
                )
            }
        )
        
        # Validation should generate warning for unused model
        diagnostics = validator.validate_unused_components(asdl_file)
        assert len(diagnostics) == 1
        assert diagnostics[0].severity == DiagnosticSeverity.WARNING
        assert diagnostics[0].code == "V0601"
        assert "unused_child" in diagnostics[0].details
        assert "unused modules" in diagnostics[0].details.lower()