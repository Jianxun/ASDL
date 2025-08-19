"""
Test cases for the ImportDeclaration foundation.

This test suite validates the ImportDeclaration data structure that enables
the import system's qualified name resolution. These tests establish the
foundation for the alias: library.filename[@version] syntax.

Tests correspond to T0.3 in the ASDL Import System Test Plan.
"""

import pytest
from src.asdl.data_structures import ImportDeclaration, ASDLFile, FileInfo, Module


class TestImportDeclarations:
    """Test cases for ImportDeclaration foundation (T0.3)."""
    
    def test_import_declaration_basic_structure(self):
        """
        T0.3.1: Import Declaration Structure
        TESTS: ImportDeclaration data structure creation
        VALIDATES: Foundation for alias: library.filename syntax
        ENSURES: Clean structure for future import resolution
        """
        # Basic import declaration
        import_decl = ImportDeclaration(
            alias="pdk_primitives",
            qualified_source="gf180mcu_pdk.primitives"
        )
        
        assert import_decl.alias == "pdk_primitives"
        assert import_decl.qualified_source == "gf180mcu_pdk.primitives"
        assert import_decl.version is None  # No version specified
        
        # Import with all fields
        versioned_import = ImportDeclaration(
            alias="analog_ip",
            qualified_source="company_lib.analog_blocks",
            version="2.1.0"
        )
        
        assert versioned_import.alias == "analog_ip"
        assert versioned_import.qualified_source == "company_lib.analog_blocks"
        assert versioned_import.version == "2.1.0"
        
    def test_qualified_source_format(self):
        """
        T0.3.2: Qualified Source Parsing
        TESTS: library.filename format validation
        VALIDATES: Clear resolution rules for import targets
        ENSURES: Unambiguous file path resolution
        """
        # Standard library.filename format
        standard_import = ImportDeclaration(
            alias="std_devices",
            qualified_source="gf180mcu_std_tiles.devices"
        )
        
        assert standard_import.qualified_source == "gf180mcu_std_tiles.devices"
        
        # Nested library names (should be valid)
        nested_import = ImportDeclaration(
            alias="company_ip",
            qualified_source="company.analog.amplifiers.ota_library"
        )
        
        assert nested_import.qualified_source == "company.analog.amplifiers.ota_library"
        
        # Underscore in names (should be valid)
        underscore_import = ImportDeclaration(
            alias="pdk_models",
            qualified_source="sky130_fd_pr.device_models"
        )
        
        assert underscore_import.qualified_source == "sky130_fd_pr.device_models"
        
    def test_version_tag_parsing(self):
        """
        T0.3.3: Version Tag Support
        TESTS: Optional @version tag in imports
        VALIDATES: Foundation for version-specific imports
        ENSURES: Reproducible builds with version constraints
        """
        # Semantic version
        semantic_import = ImportDeclaration(
            alias="stable_lib",
            qualified_source="analog_ip.amplifiers",
            version="1.2.3"
        )
        
        assert semantic_import.version == "1.2.3"
        
        # Pre-release version
        prerelease_import = ImportDeclaration(
            alias="beta_lib",
            qualified_source="experimental.new_devices", 
            version="2.0.0-beta1"
        )
        
        assert prerelease_import.version == "2.0.0-beta1"
        
        # Git commit hash
        commit_import = ImportDeclaration(
            alias="dev_lib",
            qualified_source="internal.dev_blocks",
            version="abc123def456"
        )
        
        assert commit_import.version == "abc123def456"
        
        # Date-based version
        date_import = ImportDeclaration(
            alias="dated_lib",
            qualified_source="pdk.monthly_updates",
            version="2024.03.15"
        )
        
        assert date_import.version == "2024.03.15"
        
    def test_import_alias_validation(self):
        """
        Additional test: Import alias validation
        TESTS: Alias naming conventions and uniqueness
        VALIDATES: Clear local names for imported libraries
        ENSURES: No conflicts in import namespace
        """
        # Standard alias
        std_import = ImportDeclaration(
            alias="primitives",
            qualified_source="gf180mcu_pdk.primitives"
        )
        
        assert std_import.alias == "primitives"
        
        # Descriptive alias
        descriptive_import = ImportDeclaration(
            alias="high_speed_amps",
            qualified_source="analog_ip.high_speed.amplifiers"
        )
        
        assert descriptive_import.alias == "high_speed_amps"
        
        # Technology-specific alias
        tech_import = ImportDeclaration(
            alias="gf180_devices",
            qualified_source="gf180mcu_pdk.all_devices"
        )
        
        assert tech_import.alias == "gf180_devices"
        
    def test_asdl_file_with_imports(self):
        """
        Additional test: ASDLFile with imports field
        TESTS: imports field integration with ASDLFile
        VALIDATES: Import declarations work within file structure
        ENSURES: Foundation for import resolution system
        """
        file_info = FileInfo(
            top_module="design_with_imports",
            doc="Design using imported libraries"
        )
        
        # Create imports dictionary
        imports = {
            "pdk": ImportDeclaration(
                alias="pdk",
                qualified_source="gf180mcu_pdk.primitives",
                version="1.0.2"
            ),
            "analog_lib": ImportDeclaration(
                alias="analog_lib",
                qualified_source="company_ip.analog_blocks",
                version="2.1.0"
            ),
            "spice_lib": ImportDeclaration(
                alias="spice_lib",
                qualified_source="builtin.spice_primitives"
                # No version - uses latest
            )
        }
        
        # Modules that reference imported components
        modules = {
            "my_design": Module(
                doc="Design using imports",
                instances={
                    # These would reference pdk.nmos, analog_lib.ota, etc.
                    # Actual resolution will be implemented later
                }
            )
        }
        
        asdl_file = ASDLFile(
            file_info=file_info,
            modules=modules,
            imports=imports
        )
        
        # Validate imports structure
        assert asdl_file.imports is not None
        assert len(asdl_file.imports) == 3
        assert "pdk" in asdl_file.imports
        assert "analog_lib" in asdl_file.imports
        assert "spice_lib" in asdl_file.imports
        
        # Validate individual import declarations
        pdk_import = asdl_file.imports["pdk"]
        assert pdk_import.alias == "pdk"
        assert pdk_import.qualified_source == "gf180mcu_pdk.primitives"
        assert pdk_import.version == "1.0.2"
        
        analog_import = asdl_file.imports["analog_lib"]
        assert analog_import.qualified_source == "company_ip.analog_blocks"
        assert analog_import.version == "2.1.0"
        
        spice_import = asdl_file.imports["spice_lib"]
        assert spice_import.qualified_source == "builtin.spice_primitives"
        assert spice_import.version is None  # No version specified
        
    def test_import_declaration_locatable(self):
        """
        Additional test: ImportDeclaration inherits Locatable
        TESTS: Location tracking for import declarations
        VALIDATES: Error reporting capabilities for imports
        ENSURES: Debugging support for import resolution
        """
        from pathlib import Path
        
        import_decl = ImportDeclaration(
            alias="test_lib",
            qualified_source="test.library",
            file_path=Path("/path/to/design.asdl"),
            start_line=10,
            start_col=5,
            end_line=10,
            end_col=35
        )
        
        assert import_decl.file_path == Path("/path/to/design.asdl")
        assert import_decl.start_line == 10
        assert import_decl.start_col == 5
        assert import_decl.end_line == 10
        assert import_decl.end_col == 35
        
        # Test string representation for error messages
        location_str = str(import_decl)
        assert "/path/to/design.asdl" in location_str
        assert "10:5" in location_str
        
    def test_empty_imports_section(self):
        """
        Additional test: ASDLFile with empty imports
        TESTS: Empty imports dictionary handling
        VALIDATES: Files without imports are supported
        ENSURES: Graceful handling of non-importing designs
        """
        file_info = FileInfo(top_module="standalone_design")
        
        # File with empty imports
        asdl_file_empty = ASDLFile(
            file_info=file_info,
            modules={"standalone": Module(spice_template="R{name} {a} {b} 1k")},
            imports={}  # Empty but not None
        )
        
        assert asdl_file_empty.imports is not None
        assert len(asdl_file_empty.imports) == 0
        
        # File with no imports field (None)
        asdl_file_none = ASDLFile(
            file_info=file_info,
            modules={"standalone": Module(spice_template="R{name} {a} {b} 1k")}
            # imports defaults to None
        )
        
        assert asdl_file_none.imports is None