"""
E0443: Module Not Found in Import

Validates diagnostic and orchestrator emission for unknown module in imported file.
"""

import tempfile
from pathlib import Path

from asdl.elaborator.import_.diagnostics import ImportDiagnostics
from asdl.elaborator.import_.import_resolver import ImportResolver
from asdl.diagnostics import DiagnosticSeverity


class TestE0443ModuleNotFoundInImport:
    def test_diagnostic_generation(self):
        diag_gen = ImportDiagnostics()
        module_name = "missing_amplifier"
        import_alias = "std_lib"
        import_file_path = Path("std_devices.asdl")
        available_modules = ["nmos_unit", "pmos_unit", "voltage_ref"]

        diagnostic = diag_gen.create_module_not_found_error(
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

    def test_orchestrator_emits_e0443_for_missing_module(self):
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
      I_BAD_MODULE: {model: lib1.unknown_mod}
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
            e0443 = [d for d in diagnostics if d.code == "E0443"]
            assert len(e0443) >= 1
            assert any("unknown_mod" in d.details and "lib1" in d.details for d in e0443)


