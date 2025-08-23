"""
Test cases for alias_resolver.py - model_alias resolution and validation.

Tests the model_alias processing including qualified reference parsing,
alias target validation, and collision detection.
"""

import pytest
from pathlib import Path
import sys

# Add src to path for testing
test_dir = Path(__file__).parent
project_root = test_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from asdl.elaborator.import_.alias_resolver import AliasResolver
from asdl.data_structures import ASDLFile, FileInfo, Module
from asdl.diagnostics import Diagnostic, DiagnosticSeverity


class TestAliasResolver:
    """Test cases for model_alias resolution and validation (Phase 1.2.3)."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.resolver = AliasResolver()
    
    def test_qualified_reference_parsing(self):
        """
        T1.6.1: Qualified Reference Parsing
        TESTS: Parsing of alias.module_name format references
        VALIDATES: Correct splitting and validation of qualified references
        ENSURES: Valid references are parsed correctly
        """
        test_cases = [
            ("std_lib.nmos_unit", ("std_lib", "nmos_unit")),
            ("amplifiers.two_stage_miller", ("amplifiers", "two_stage_miller")),
            ("pdk_devices.pfet_03v3", ("pdk_devices", "pfet_03v3")),
            ("lib123.mod_456", ("lib123", "mod_456")),
            ("my_lib.my_module", ("my_lib", "my_module"))
        ]
        
        for qualified_ref, expected in test_cases:
            result = self.resolver.parse_qualified_reference(qualified_ref)
            assert result == expected, f"Failed to parse '{qualified_ref}'"
    
    def test_invalid_qualified_reference_formats(self):
        """
        T1.6.2: Invalid Qualified Reference Formats
        TESTS: Detection of malformed qualified references
        VALIDATES: Error handling for invalid alias.module_name formats
        ENSURES: Invalid formats return None
        """
        invalid_refs = [
            "std_lib.",           # Missing module name
            ".nmos_unit",         # Missing import alias
            "std_lib..nmos_unit", # Double dots
            "std_lib.nmos.unit",  # Too many dots
            "std_lib",            # Missing dot
            "",                   # Empty string
            "123_lib.module",     # Invalid alias start
            "lib.123_module",     # Invalid module start
            "lib-name.module",    # Invalid characters
            "lib.mod-name"        # Invalid characters
        ]
        
        for invalid_ref in invalid_refs:
            result = self.resolver.parse_qualified_reference(invalid_ref)
            assert result is None, f"Should return None for invalid reference: {invalid_ref}"
    
    def test_alias_target_validation(self):
        """
        T1.6.3: Alias Target Validation
        TESTS: Validation that alias targets exist in imported files
        VALIDATES: Referenced modules exist in target files
        ENSURES: Broken aliases are detected
        """
        # Create main file with model_alias
        main_file = ASDLFile(
            file_info=FileInfo(top_module="main"),
            modules={},
            imports={"std_lib": "std_library.asdl"},
            model_alias={
                "valid_alias": "std_lib.existing_module",
                "invalid_alias": "std_lib.missing_module"
            }
        )
        
        # Create imported file
        imported_file = ASDLFile(
            file_info=FileInfo(top_module="std_library"),
            modules={"existing_module": Module(ports={}, spice_template="template")}
        )
        loaded_files = {Path("std_library.asdl"): imported_file}
        
        # Validate aliases
        diagnostics = self.resolver.validate_model_aliases(main_file, loaded_files)
        
        # Should find one invalid alias
        assert len(diagnostics) == 1
        diag = diagnostics[0]
        assert diag.code == "E0444"
        assert "invalid_alias" in diag.details
        assert "missing_module" in diag.details
        assert diag.severity == DiagnosticSeverity.ERROR
    
    def test_alias_import_collision_detection(self):
        """
        T1.6.4: Alias-Import Collision Detection  
        TESTS: Detection of collisions between alias names and import names
        VALIDATES: model_alias names don't conflict with import aliases
        ENSURES: Collision diagnostics are generated
        """
        # Create main file with collision between alias and import name
        main_file = ASDLFile(
            file_info=FileInfo(top_module="main"),
            modules={},
            imports={
                "std_lib": "std_library.asdl",
                "other_lib": "other_library.asdl"
            },
            model_alias={
                "std_lib": "other_lib.some_module",  # Collision with import alias
                "valid_alias": "std_lib.valid_module",
                "other_lib": "std_lib.another_module"  # Another collision
            }
        )
        
        # Create mock imported files
        imported_file1 = ASDLFile(
            file_info=FileInfo(top_module="std_library"),
            modules={"valid_module": Module(ports={}, spice_template="template1")}
        )
        imported_file2 = ASDLFile(
            file_info=FileInfo(top_module="other_library"),
            modules={"some_module": Module(ports={}, spice_template="template2")}
        )
        loaded_files = {
            Path("std_library.asdl"): imported_file1,
            Path("other_library.asdl"): imported_file2
        }
        
        # Check for collisions
        diagnostics = self.resolver.validate_model_aliases(main_file, loaded_files)
        
        # Should find collisions for 'std_lib' and 'other_lib' aliases
        collision_diagnostics = [d for d in diagnostics if d.code == "E0445"]
        assert len(collision_diagnostics) == 2
        
        collision_aliases = [d.details for d in collision_diagnostics]
        assert any("std_lib" in details for details in collision_aliases)
        assert any("other_lib" in details for details in collision_aliases)
    
    def test_alias_resolution_with_missing_imports(self):
        """
        T1.6.5: Alias Resolution with Missing Imports
        TESTS: Handling of aliases that reference non-existent import aliases
        VALIDATES: Proper error handling for broken import references
        ENSURES: Clear diagnostics for missing import dependencies
        """
        # Create main file with alias referencing non-existent import
        main_file = ASDLFile(
            file_info=FileInfo(top_module="main"),
            modules={},
            imports={"existing_lib": "existing.asdl"},
            model_alias={
                "valid_alias": "existing_lib.some_module",
                "broken_alias": "nonexistent_lib.some_module"
            }
        )
        
        # Create only the existing imported file
        imported_file = ASDLFile(
            file_info=FileInfo(top_module="existing_library"),
            modules={"some_module": Module(ports={}, spice_template="template")}
        )
        loaded_files = {Path("existing.asdl"): imported_file}
        
        # Validate aliases
        diagnostics = self.resolver.validate_model_aliases(main_file, loaded_files)
        
        # Should find error for broken alias
        import_errors = [d for d in diagnostics if "nonexistent_lib" in d.details]
        assert len(import_errors) == 1
        assert import_errors[0].code == "E0444"  # Import alias not found
        assert "broken_alias" in import_errors[0].details
    
    def test_empty_model_alias_validation(self):
        """
        T1.6.6: Empty model_alias Validation
        TESTS: Handling of files without model_alias section
        VALIDATES: Validation works correctly with empty/missing model_alias
        ENSURES: No errors for files without aliases
        """
        # Test with None model_alias
        main_file_none = ASDLFile(
            file_info=FileInfo(top_module="main"),
            modules={},
            imports={"std_lib": "std_library.asdl"},
            model_alias=None
        )
        
        # Test with empty model_alias
        main_file_empty = ASDLFile(
            file_info=FileInfo(top_module="main"),
            modules={},
            imports={"std_lib": "std_library.asdl"},
            model_alias={}
        )
        
        loaded_files = {}
        
        # Both should validate without errors
        diagnostics_none = self.resolver.validate_model_aliases(main_file_none, loaded_files)
        diagnostics_empty = self.resolver.validate_model_aliases(main_file_empty, loaded_files)
        
        assert len(diagnostics_none) == 0
        assert len(diagnostics_empty) == 0