"""
E0444: Import Alias Not Found (and invalid model alias/qualified ref cases)

Covers diagnostic creation and orchestrator emission for unknown import alias.
"""

import tempfile
from pathlib import Path

from asdl.elaborator.import_.diagnostics import ImportDiagnostics
from asdl.elaborator.import_.import_resolver import ImportResolver
from asdl.diagnostics import DiagnosticSeverity


class TestE0444ImportAliasNotFound:
    def test_diagnostic_generation(self):
        diag_gen = ImportDiagnostics()
        unknown_alias = "unknown_lib"
        qualified_ref = "unknown_lib.some_module"
        available_imports = ["std_lib", "analog_lib", "digital_lib"]

        diagnostic = diag_gen.create_import_alias_not_found_error(
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

    def test_orchestrator_emits_e0444_for_unknown_alias(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
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
      I_OK: {model: lib1.known_mod}
"""
            )

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

            resolver = ImportResolver()
            result, diagnostics = resolver.resolve_imports(
                main_file_path, search_paths=[temp_path]
            )

            assert result is not None
            e0444 = [d for d in diagnostics if d.code == "E0444" and "Import Alias Not Found" in d.title]
            assert len(e0444) >= 1
            assert any("missing_alias" in d.details for d in e0444)


