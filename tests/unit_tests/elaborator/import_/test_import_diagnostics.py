"""
Test cases for import diagnostics - E044x error code generation.

Tests the diagnostic generation for import resolution errors including
file not found, circular imports, module resolution failures, and alias issues.
"""

import pytest
from pathlib import Path

from asdl.elaborator.import_.diagnostics import ImportDiagnostics
from asdl.diagnostics import DiagnosticSeverity


class TestImportDiagnostics:
    """Test cases for import diagnostic generation (Phase 1.2.4)."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.diagnostics = ImportDiagnostics()
    
    def test_import_file_not_found_e0441(self):
        """
        T1.7.1: Import File Not Found (E0441)
        TESTS: E0441 diagnostic generation for missing import files
        VALIDATES: Proper error message and suggestion for missing files
        ENSURES: File path and search information included
        """
        import_alias = "std_lib"
        import_path = "gf180mcu/std_devices.asdl"
        search_paths = [Path("/pdks"), Path("/workspace/libs")]
        
        diagnostic = self.diagnostics.create_file_not_found_error(
            import_alias, import_path, search_paths
        )
        
        assert diagnostic.code == "E0441"
        assert diagnostic.title == "Import File Not Found"
        assert diagnostic.severity == DiagnosticSeverity.ERROR
        assert import_alias in diagnostic.details
        assert import_path in diagnostic.details
        assert "searched in the following locations" in diagnostic.details.lower()
        assert str(search_paths[0]) in diagnostic.details
        assert str(search_paths[1]) in diagnostic.details
        assert "check that the file path is correct" in diagnostic.suggestion.lower()
    
    def test_circular_import_detected_e0442(self):
        """
        T1.7.2: Circular Import Detected (E0442)
        TESTS: E0442 diagnostic generation for circular import detection
        VALIDATES: Circular dependency chain description
        ENSURES: Import cycle clearly shown in error message
        """
        import_cycle = [
            Path("module_a.asdl"),
            Path("module_b.asdl"), 
            Path("module_c.asdl"),
            Path("module_a.asdl")  # Back to start
        ]
        
        diagnostic = self.diagnostics.create_circular_import_error(import_cycle)
        
        assert diagnostic.code == "E0442"
        assert diagnostic.title == "Circular Import Detected"
        assert diagnostic.severity == DiagnosticSeverity.ERROR
        assert "circular import dependency" in diagnostic.details.lower()
        assert "module_a.asdl" in diagnostic.details
        assert "module_b.asdl" in diagnostic.details
        assert "module_c.asdl" in diagnostic.details
        assert "→" in diagnostic.details  # Shows dependency chain
        assert "restructur" in diagnostic.suggestion.lower()  # Restructuring suggestion
    
    def test_module_not_found_in_import_e0443(self):
        """
        T1.7.3: Module Not Found in Import (E0443)
        TESTS: E0443 diagnostic generation for missing modules in imported files
        VALIDATES: Module name and file context in error message
        ENSURES: Available modules listed as suggestions
        """
        module_name = "missing_amplifier"
        import_alias = "std_lib"
        import_file_path = Path("std_devices.asdl")
        available_modules = ["nmos_unit", "pmos_unit", "voltage_ref"]
        
        diagnostic = self.diagnostics.create_module_not_found_error(
            module_name, import_alias, import_file_path, available_modules
        )
        
        assert diagnostic.code == "E0443"
        assert diagnostic.title == "Module Not Found in Import"
        assert diagnostic.severity == DiagnosticSeverity.ERROR
        assert module_name in diagnostic.details
        assert import_alias in diagnostic.details
        assert str(import_file_path) in diagnostic.details
        assert "available modules" in diagnostic.suggestion.lower()
        assert all(mod in diagnostic.suggestion for mod in available_modules)
    
    def test_import_alias_not_found_e0444(self):
        """
        T1.7.4: Import Alias Not Found (E0444)
        TESTS: E0444 diagnostic generation for unknown import aliases
        VALIDATES: Import alias and context in error message
        ENSURES: Available import aliases listed as suggestions
        """
        unknown_alias = "unknown_lib"
        qualified_ref = "unknown_lib.some_module"
        available_imports = ["std_lib", "analog_lib", "digital_lib"]
        
        diagnostic = self.diagnostics.create_import_alias_not_found_error(
            unknown_alias, qualified_ref, available_imports
        )
        
        assert diagnostic.code == "E0444"
        assert diagnostic.title == "Import Alias Not Found"  
        assert diagnostic.severity == DiagnosticSeverity.ERROR
        assert unknown_alias in diagnostic.details
        assert qualified_ref in diagnostic.details
        assert "is not declared in the imports section" in diagnostic.details
        assert "available import aliases" in diagnostic.suggestion.lower()
        assert all(alias in diagnostic.suggestion for alias in available_imports)
    
    def test_model_alias_collision_e0445(self):
        """
        T1.7.5: Model Alias Collision (E0445)
        TESTS: E0445 diagnostic generation for alias name collisions
        VALIDATES: Collision description and conflicting names
        ENSURES: Renaming suggestion provided
        """
        conflicting_alias = "std_lib"
        import_alias = "std_lib" 
        alias_target = "other_lib.some_module"
        
        diagnostic = self.diagnostics.create_model_alias_collision_error(
            conflicting_alias, import_alias, alias_target
        )
        
        assert diagnostic.code == "E0445"
        assert diagnostic.title == "Model Alias Collision"
        assert diagnostic.severity == DiagnosticSeverity.ERROR
        assert conflicting_alias in diagnostic.details
        assert "collides with import alias" in diagnostic.details
        assert alias_target in diagnostic.details
        assert "rename the model alias" in diagnostic.suggestion.lower()
        assert "avoid collision" in diagnostic.suggestion.lower()
    
    def test_diagnostic_message_formatting(self):
        """
        T1.7.6: Diagnostic Message Formatting
        TESTS: Consistent formatting across all diagnostic types
        VALIDATES: Message structure and information completeness
        ENSURES: Diagnostics follow standard format patterns
        """
        # Test various diagnostic creation methods for consistent formatting
        file_diag = self.diagnostics.create_file_not_found_error(
            "test_alias", "test/path.asdl", [Path("/test")]
        )
        
        circular_diag = self.diagnostics.create_circular_import_error([
            Path("a.asdl"), Path("b.asdl"), Path("a.asdl")
        ])
        
        module_diag = self.diagnostics.create_module_not_found_error(
            "test_mod", "test_alias", Path("test.asdl"), ["other_mod"]
        )
        
        alias_diag = self.diagnostics.create_import_alias_not_found_error(
            "test_alias", "test_alias.mod", ["other_alias"]
        )
        
        collision_diag = self.diagnostics.create_model_alias_collision_error(
            "test_alias", "test_alias", "other.mod"
        )
        
        all_diagnostics = [file_diag, circular_diag, module_diag, alias_diag, collision_diag]
        
        # All should have required fields
        for diag in all_diagnostics:
            assert diag.code is not None and diag.code.startswith("E044")
            assert diag.title is not None and len(diag.title) > 0
            assert diag.details is not None and len(diag.details) > 0
            assert diag.suggestion is not None and len(diag.suggestion) > 0
            assert diag.severity == DiagnosticSeverity.ERROR
        
        # All should have unique error codes
        codes = [diag.code for diag in all_diagnostics]
        assert len(set(codes)) == len(codes), "All diagnostics should have unique codes"
    
    def test_empty_search_paths_handling(self):
        """
        T1.7.7: Empty Search Paths Handling
        TESTS: Diagnostic generation with empty search paths list
        VALIDATES: Graceful handling of missing search path information
        ENSURES: Error message still informative without search paths
        """
        diagnostic = self.diagnostics.create_file_not_found_error(
            "test_alias", "test/path.asdl", []
        )
        
        assert diagnostic.code == "E0441"
        assert "test_alias" in diagnostic.details
        assert "test/path.asdl" in diagnostic.details
        # Should still be informative even without search paths
        assert len(diagnostic.details) > 20  # Reasonable detail length