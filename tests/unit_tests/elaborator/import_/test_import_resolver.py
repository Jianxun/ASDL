"""
Test cases for import_resolver.py - Main import resolution orchestrator.

Tests the complete import resolution workflow including file loading,
dependency resolution, and flattening into a single ASDLFile.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Add src to path for testing
test_dir = Path(__file__).parent
project_root = test_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from asdl.elaborator.import_.import_resolver import ImportResolver
from asdl.data_structures import ASDLFile, FileInfo, Module
from asdl.diagnostics import Diagnostic, DiagnosticSeverity


class TestImportResolver:
    """Test cases for import resolution orchestration (Phase 1.2.4)."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.resolver = ImportResolver()
    
    def test_simple_import_resolution(self):
        """
        T1.8.1: Simple Import Resolution
        TESTS: Basic import resolution with single imported file
        VALIDATES: File loading and module flattening work correctly
        ENSURES: Single flattened ASDLFile output with resolved imports
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create main file with import
            main_file_path = temp_path / "main.asdl"
            main_file_path.write_text("""
file_info:
  top_module: main
imports:
  std_lib: std_devices.asdl
modules:
  inverter:
    ports: {in: {dir: in}, out: {dir: out}}
    instances:
      M1: {model: std_lib.nmos_unit, mappings: {D: out, G: in, S: gnd}}
""")
            
            # Create imported file
            std_file_path = temp_path / "std_devices.asdl"
            std_file_path.write_text("""
file_info:
  top_module: std_devices
modules:
  nmos_unit:
    ports: {D: {dir: out}, G: {dir: in}, S: {dir: out}}
    spice_template: "MN{name} {D} {G} {S} nmos"
""")
            
            # Resolve imports
            result, diagnostics = self.resolver.resolve_imports(
                main_file_path, 
                search_paths=[temp_path]
            )
            
            assert result is not None
            assert len(diagnostics) == 0
            
            # Should have flattened all modules into single file
            assert len(result.modules) == 2  # inverter + nmos_unit
            assert "inverter" in result.modules
            assert "nmos_unit" in result.modules
            
            # Original import/model_alias info should be preserved for reference
            assert result.imports is not None
            assert "std_lib" in result.imports
            
            # Verify module content
            nmos_module = result.modules["nmos_unit"]
            assert nmos_module.spice_template == "MN{name} {D} {G} {S} nmos"
    
    def test_model_alias_resolution(self):
        """
        T1.8.2: Model Alias Resolution
        TESTS: Import resolution with model_alias section
        VALIDATES: Local aliases are resolved to imported modules
        ENSURES: Alias information preserved in flattened output
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create main file with model_alias
            main_file_path = temp_path / "main.asdl"
            main_file_path.write_text("""
file_info:
  top_module: main
imports:
  devices: device_lib.asdl
model_alias:
  nmos: devices.nmos_unit
  pmos: devices.pmos_unit
modules:
  inverter:
    ports: {in: {dir: in}, out: {dir: out}}
    instances:
      MN: {model: nmos, mappings: {D: out, G: in, S: gnd}}
      MP: {model: pmos, mappings: {D: out, G: in, S: vdd}}
""")
            
            # Create device library
            device_file_path = temp_path / "device_lib.asdl"
            device_file_path.write_text("""
file_info:
  top_module: device_lib
modules:
  nmos_unit:
    ports: {D: {dir: out}, G: {dir: in}, S: {dir: out}}
    spice_template: "MN{name} {D} {G} {S} nmos"
  pmos_unit:
    ports: {D: {dir: out}, G: {dir: in}, S: {dir: out}}
    spice_template: "MP{name} {D} {G} {S} pmos"
""")
            
            # Resolve imports
            result, diagnostics = self.resolver.resolve_imports(
                main_file_path,
                search_paths=[temp_path]
            )
            
            assert result is not None
            assert len(diagnostics) == 0
            
            # Should have all modules flattened
            assert len(result.modules) == 3  # inverter + nmos_unit + pmos_unit
            assert "inverter" in result.modules
            assert "nmos_unit" in result.modules
            assert "pmos_unit" in result.modules
            
            # Model alias should be preserved
            assert result.model_alias is not None
            assert "nmos" in result.model_alias
            assert "pmos" in result.model_alias
    
    def test_transitive_imports(self):
        """
        T1.8.3: Transitive Import Resolution
        TESTS: Imports that have their own imports (A imports B imports C)
        VALIDATES: Recursive import loading and resolution
        ENSURES: All transitive dependencies resolved
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create main file (A)
            main_file_path = temp_path / "main.asdl"
            main_file_path.write_text("""
file_info:
  top_module: main
imports:
  analog_lib: analog_blocks.asdl
modules:
  circuit:
    instances:
      AMP: {model: analog_lib.amplifier}
""")
            
            # Create analog blocks file (B) that imports primitives
            analog_file_path = temp_path / "analog_blocks.asdl"
            analog_file_path.write_text("""
file_info:
  top_module: analog_blocks
imports:
  primitives: device_primitives.asdl
modules:
  amplifier:
    instances:
      M1: {model: primitives.nmos}
      M2: {model: primitives.pmos}
""")
            
            # Create primitives file (C)
            primitives_file_path = temp_path / "device_primitives.asdl"
            primitives_file_path.write_text("""
file_info:
  top_module: device_primitives
modules:
  nmos:
    spice_template: "MN{name} {D} {G} {S} nmos"
  pmos:
    spice_template: "MP{name} {D} {G} {S} pmos"
""")
            
            # Resolve imports
            result, diagnostics = self.resolver.resolve_imports(
                main_file_path,
                search_paths=[temp_path]
            )
            
            assert result is not None
            assert len(diagnostics) == 0
            
            # Should have all modules from all files flattened
            assert len(result.modules) == 4  # circuit + amplifier + nmos + pmos
            assert "circuit" in result.modules
            assert "amplifier" in result.modules
            assert "nmos" in result.modules
            assert "pmos" in result.modules
    
    def test_import_error_handling(self):
        """
        T1.8.4: Import Error Handling
        TESTS: Proper error handling for various import failures
        VALIDATES: Diagnostic generation and graceful failure
        ENSURES: Clear error messages for common import issues
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create main file with problematic imports
            main_file_path = temp_path / "main.asdl"
            main_file_path.write_text("""
file_info:
  top_module: main
imports:
  missing_lib: nonexistent_file.asdl
  valid_lib: existing_file.asdl
model_alias:
  broken_alias: missing_lib.some_module
  good_alias: valid_lib.existing_module
modules:
  test_circuit:
    instances:
      INST1: {model: broken_alias}
      INST2: {model: good_alias}
""")
            
            # Create only one of the imported files
            existing_file_path = temp_path / "existing_file.asdl"
            existing_file_path.write_text("""
file_info:
  top_module: existing_file
modules:
  existing_module:
    spice_template: "test template"
""")
            
            # Resolve imports (should handle errors gracefully)
            result, diagnostics = self.resolver.resolve_imports(
                main_file_path,
                search_paths=[temp_path]
            )
            
            # Should still return a result (partial resolution)
            assert result is not None
            
            # Should have diagnostics for the missing file
            assert len(diagnostics) > 0
            
            # Should have E0441 error for missing file
            file_not_found_errors = [d for d in diagnostics if d.code == "E0441"]
            assert len(file_not_found_errors) >= 1
            assert any("nonexistent_file.asdl" in d.details for d in file_not_found_errors)

            # Additional validation-specific errors may be present depending on loaded context
    
    def test_circular_import_detection(self):
        """
        T1.8.5: Circular Import Detection
        TESTS: Detection and handling of circular import dependencies
        VALIDATES: Circular dependency error generation
        ENSURES: Import resolution stops gracefully on cycles
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create file A that imports B
            file_a_path = temp_path / "module_a.asdl"
            file_a_path.write_text("""
file_info:
  top_module: module_a
imports:
  module_b: module_b.asdl
modules:
  circuit_a:
    instances:
      B_INST: {model: module_b.circuit_b}
""")
            
            # Create file B that imports A (circular)
            file_b_path = temp_path / "module_b.asdl"
            file_b_path.write_text("""
file_info:
  top_module: module_b
imports:
  module_a: module_a.asdl
modules:
  circuit_b:
    instances:
      A_INST: {model: module_a.circuit_a}
""")
            
            # Resolve imports (should detect circular dependency)
            result, diagnostics = self.resolver.resolve_imports(
                file_a_path,
                search_paths=[temp_path]
            )
            
            # Should detect circular import
            assert len(diagnostics) > 0
            
            # Should have E0442 error for circular import
            circular_errors = [d for d in diagnostics if d.code == "E0442"]
            assert len(circular_errors) >= 1
            assert any("circular" in d.title.lower() for d in circular_errors)
    
    def test_search_path_resolution(self):
        """
        T1.8.6: Search Path Resolution
        TESTS: File discovery across multiple search paths
        VALIDATES: ASDL_PATH and CLI search path functionality
        ENSURES: Files found in correct search order
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create directory structure
            dir1 = temp_path / "libs1"
            dir2 = temp_path / "libs2"
            dir1.mkdir()
            dir2.mkdir()
            
            # Create main file
            main_file_path = temp_path / "main.asdl"
            main_file_path.write_text("""
file_info:
  top_module: main
imports:
  common_lib: shared/common.asdl
modules:
  test_module:
    instances:
      INST: {model: common_lib.shared_component}
""")
            
            # Create shared file in second search directory only
            shared_dir = dir2 / "shared"
            shared_dir.mkdir()
            shared_file_path = shared_dir / "common.asdl"
            shared_file_path.write_text("""
file_info:
  top_module: common
modules:
  shared_component:
    spice_template: "shared template"
""")
            
            # Resolve with multiple search paths
            result, diagnostics = self.resolver.resolve_imports(
                main_file_path,
                search_paths=[dir1, dir2]  # Should find file in dir2
            )
            
            assert result is not None
            assert len(diagnostics) == 0
            
            # Should have found and loaded the shared component
            assert "shared_component" in result.modules
            assert result.modules["shared_component"].spice_template == "shared template"

    def test_qualified_reference_errors_E0443_E0444(self):
        """
        T1.8.7: Qualified Reference Validation
        TESTS: Emit E0444 when alias unknown, E0443 when module missing in imported file
        VALIDATES: Post-load validation of instance model references
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Main file references two qualified models: one with unknown alias, one with valid alias but missing module
            main_file_path = temp_path / "main.asdl"
            main_file_path.write_text(
                """
file_info:
  top_module: main
imports:
  lib1: devices.asdl
modules:
  top:
    instances:
      I_BAD_ALIAS: {model: missing_alias.some_mod}
      I_BAD_MODULE: {model: lib1.unknown_mod}
"""
            )
            # devices.asdl exists but does not define unknown_mod
            devices_path = temp_path / "devices.asdl"
            devices_path.write_text(
                """
file_info:
  top_module: devices
modules:
  known_mod:
    spice_template: "X{name} {A} {B} known"
"""
            )

            result, diagnostics = self.resolver.resolve_imports(
                main_file_path, search_paths=[temp_path]
            )
            assert result is not None
            # Expect E0444 for unknown alias 'missing_alias'
            e0444_alias = [d for d in diagnostics if d.code == "E0444" and "Import Alias Not Found" in d.title]
            assert len(e0444_alias) >= 1
            assert any("missing_alias" in d.details for d in e0444_alias)
            # Expect E0443 for module not found in import 'lib1'
            e0443 = [d for d in diagnostics if d.code == "E0443"]
            assert len(e0443) >= 1
            assert any("unknown_mod" in d.details and "lib1" in d.details for d in e0443)