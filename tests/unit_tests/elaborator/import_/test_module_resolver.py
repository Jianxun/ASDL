"""
Test cases for module_resolver.py - Cross-file module lookup and resolution.

Tests the three-step module resolution: local modules → model_alias → imported modules.
Validates module reference resolution and error handling.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock
import sys

# Add src to path for testing
test_dir = Path(__file__).parent
project_root = test_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from asdl.elaborator.import_.module_resolver import ModuleResolver
from asdl.data_structures import ASDLFile, FileInfo, Module
from asdl.diagnostics import Diagnostic, DiagnosticSeverity


class TestModuleResolver:
    """Test cases for cross-file module lookup and resolution (Phase 1.2.3)."""
    
    def setup_method(self):
        """Set up test dependencies."""
        # Mock file loader for testing
        self.mock_file_loader = Mock()
        self.resolver = ModuleResolver(self.mock_file_loader)
    
    def test_local_module_lookup_priority(self):
        """
        T1.5.1: Local Module Lookup Priority (Step 1)
        TESTS: Local modules have highest priority in resolution
        VALIDATES: Local definitions override imports and aliases
        ENSURES: Step 1 of 3-step lookup works correctly
        """
        # Create main file with local module
        main_file = ASDLFile(
            file_info=FileInfo(top_module="main"),
            modules={
                "local_amp": Module(ports={}, spice_template="local template"),
                "other_mod": Module(ports={}, spice_template="other template")
            },
            imports={"std_lib": "std_library.asdl"},
            model_alias={"local_amp": "std_lib.amplifier"}  # Should be ignored
        )
        
        # Mock imported file (should not be accessed for local lookup)
        imported_file = ASDLFile(
            file_info=FileInfo(top_module="std_library"),
            modules={"amplifier": Module(ports={}, spice_template="imported template")}
        )
        self.mock_file_loader.load_file.return_value = (imported_file, [])
        
        # Resolve local module - should find local definition
        result = self.resolver.resolve_module_reference(
            "local_amp", main_file, {}  # Empty loaded_files cache
        )
        
        assert result is not None
        resolved_module, source_info = result
        assert resolved_module.spice_template == "local template"
        assert source_info["source"] == "local"
        assert source_info["file"] == main_file
        
        # File loader should not be called for local lookup
        self.mock_file_loader.load_file.assert_not_called()
    
    def test_model_alias_lookup_step_2(self):
        """
        T1.5.2: Model Alias Lookup (Step 2)
        TESTS: model_alias resolution when local module not found
        VALIDATES: Qualified references resolve to imported modules
        ENSURES: Step 2 of 3-step lookup works correctly
        """
        # Create main file with model_alias but no local module
        main_file = ASDLFile(
            file_info=FileInfo(top_module="main"),
            modules={"other_mod": Module(ports={}, spice_template="other template")},
            imports={"std_lib": "std_library.asdl"},
            model_alias={"amp_unit": "std_lib.amplifier"}
        )
        
        # Mock imported file
        imported_file = ASDLFile(
            file_info=FileInfo(top_module="std_library"),
            modules={"amplifier": Module(ports={}, spice_template="imported template")}
        )
        loaded_files = {Path("std_library.asdl"): imported_file}
        self.mock_file_loader.load_file.return_value = (imported_file, [])
        
        # Resolve via model_alias - should find imported module
        result = self.resolver.resolve_module_reference(
            "amp_unit", main_file, loaded_files
        )
        
        assert result is not None
        resolved_module, source_info = result
        assert resolved_module.spice_template == "imported template"
        assert source_info["source"] == "model_alias"
        assert source_info["alias"] == "amp_unit"
        assert source_info["qualified_ref"] == "std_lib.amplifier"
        assert source_info["file"] == imported_file
    
    def test_qualified_import_lookup_step_3(self):
        """
        T1.5.3: Qualified Import Lookup (Step 3)
        TESTS: Direct qualified references to imported modules
        VALIDATES: import_alias.module_name resolution works
        ENSURES: Step 3 of 3-step lookup works correctly
        """
        # Create main file with imports but no local module or alias
        main_file = ASDLFile(
            file_info=FileInfo(top_module="main"),
            modules={"other_mod": Module(ports={}, spice_template="other template")},
            imports={"std_lib": "std_library.asdl"}
        )
        
        # Mock imported file
        imported_file = ASDLFile(
            file_info=FileInfo(top_module="std_library"),
            modules={"amplifier": Module(ports={}, spice_template="imported template")}
        )
        loaded_files = {Path("std_library.asdl"): imported_file}
        
        # Resolve qualified reference directly
        result = self.resolver.resolve_module_reference(
            "std_lib.amplifier", main_file, loaded_files
        )
        
        assert result is not None
        resolved_module, source_info = result
        assert resolved_module.spice_template == "imported template"
        assert source_info["source"] == "qualified_import"
        assert source_info["import_alias"] == "std_lib"
        assert source_info["module_name"] == "amplifier"
        assert source_info["file"] == imported_file
    
    def test_resolution_precedence_order(self):
        """
        T1.5.4: Resolution Precedence Order
        TESTS: Local → model_alias → qualified import precedence
        VALIDATES: Higher priority sources override lower priority
        ENSURES: 3-step resolution order is maintained correctly
        """
        # Create main file with all three resolution paths available
        main_file = ASDLFile(
            file_info=FileInfo(top_module="main"),
            modules={"test_mod": Module(ports={}, spice_template="LOCAL template")},  # Highest priority
            imports={"std_lib": "std_library.asdl"},
            model_alias={"test_mod": "std_lib.amplifier"}  # Should be ignored due to local module
        )
        
        # Mock imported file
        imported_file = ASDLFile(
            file_info=FileInfo(top_module="std_library"),
            modules={"amplifier": Module(ports={}, spice_template="imported template")}
        )
        loaded_files = {Path("std_library.asdl"): imported_file}
        
        # Should resolve to local module (highest priority)
        result = self.resolver.resolve_module_reference(
            "test_mod", main_file, loaded_files
        )
        
        assert result is not None
        resolved_module, source_info = result
        assert resolved_module.spice_template == "LOCAL template"
        assert source_info["source"] == "local"
    
    def test_module_not_found_error(self):
        """
        T1.5.5: Module Not Found Error Handling
        TESTS: Behavior when module cannot be found in any step
        VALIDATES: Appropriate error diagnostic generation
        ENSURES: Clear error messages for missing modules
        """
        # Create main file without the requested module
        main_file = ASDLFile(
            file_info=FileInfo(top_module="main"),
            modules={"other_mod": Module(ports={}, spice_template="other template")},
            imports={"std_lib": "std_library.asdl"}
        )
        
        # Mock imported file without the requested module
        imported_file = ASDLFile(
            file_info=FileInfo(top_module="std_library"),
            modules={"different_mod": Module(ports={}, spice_template="different template")}
        )
        loaded_files = {Path("std_library.asdl"): imported_file}
        
        # Try to resolve non-existent module
        result = self.resolver.resolve_module_reference(
            "missing_module", main_file, loaded_files
        )
        
        # Should return None (module not found)
        assert result is None
    
    def test_invalid_qualified_reference_format(self):
        """
        T1.5.6: Invalid Qualified Reference Format
        TESTS: Handling of malformed qualified references
        VALIDATES: Error detection for invalid import_alias.module_name format
        ENSURES: Graceful handling of malformed references
        """
        main_file = ASDLFile(
            file_info=FileInfo(top_module="main"),
            modules={},
            imports={"std_lib": "std_library.asdl"}
        )
        loaded_files = {}
        
        # Test various invalid qualified reference formats
        invalid_refs = [
            "std_lib.",           # Missing module name
            ".amplifier",         # Missing import alias
            "std_lib..amplifier", # Double dots
            "std_lib.amp.extra",  # Too many dots
            ""                    # Empty reference
        ]
        
        for invalid_ref in invalid_refs:
            result = self.resolver.resolve_module_reference(
                invalid_ref, main_file, loaded_files
            )
            # Should return None for invalid format (not crash)
            assert result is None, f"Should return None for invalid reference: {invalid_ref}"
    
    def test_module_reference_validation(self):
        """
        T1.5.7: Module Reference Validation
        TESTS: Validation of module references during resolution
        VALIDATES: Import alias existence and module availability
        ENSURES: Proper error detection for invalid references
        """
        main_file = ASDLFile(
            file_info=FileInfo(top_module="main"),
            modules={},
            imports={"std_lib": "std_library.asdl"},
            model_alias={"broken_alias": "nonexistent_lib.module"}
        )
        
        imported_file = ASDLFile(
            file_info=FileInfo(top_module="std_library"),
            modules={"amplifier": Module(ports={}, spice_template="template")}
        )
        loaded_files = {Path("std_library.asdl"): imported_file}
        
        # Test cases that should return None
        test_cases = [
            "unknown_alias.module",     # Unknown import alias in qualified ref
            "std_lib.missing_module",   # Valid alias but missing module
            "broken_alias"              # model_alias with invalid target
        ]
        
        for test_ref in test_cases:
            result = self.resolver.resolve_module_reference(
                test_ref, main_file, loaded_files
            )
            assert result is None, f"Should return None for invalid reference: {test_ref}"