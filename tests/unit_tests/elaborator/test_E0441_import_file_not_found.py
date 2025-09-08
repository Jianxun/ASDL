"""
E0441: Import File Not Found

Covers diagnostic creation and end-to-end emission via the orchestrator.
"""

import tempfile
from pathlib import Path

from asdl.elaborator.import_.diagnostics import ImportDiagnostics
from asdl.elaborator.import_.import_resolver import ImportResolver
from asdl.diagnostics import DiagnosticSeverity


class TestE0441ImportFileNotFound:
    def setup_method(self):
        self.diagnostics = ImportDiagnostics()

    def test_import_file_not_found_diagnostic(self):
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

    def test_orchestrator_emits_e0441_for_missing_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            main_file_path = temp_path / "main.asdl"
            main_file_path.write_text(
                """
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
"""
            )

            existing_file_path = temp_path / "existing_file.asdl"
            existing_file_path.write_text(
                """
file_info:
  top_module: existing_file
modules:
  existing_module:
    spice_template: "test template"
"""
            )

            resolver = ImportResolver()
            result, diagnostics = resolver.resolve_imports(
                main_file_path, search_paths=[temp_path]
            )

            assert result is not None
            e0441 = [d for d in diagnostics if d.code == "E0441"]
            assert len(e0441) >= 1
            assert any("nonexistent_file.asdl" in d.details for d in e0441)

    def test_orchestrator_e0441_includes_probe_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            dir1 = temp_path / "libs1"
            dir2 = temp_path / "libs2"
            dir1.mkdir()
            dir2.mkdir()

            main_file_path = temp_path / "main.asdl"
            main_file_path.write_text(
                """
file_info:
  top_module: main
imports:
  common_lib: shared/common.asdl
modules:
  top:
    instances: {}
"""
            )

            resolver = ImportResolver()
            result, diagnostics = resolver.resolve_imports(
                main_file_path, search_paths=[dir1, dir2]
            )

            assert result is not None
            e0441 = [d for d in diagnostics if d.code == "E0441"]
            assert len(e0441) >= 1
            assert str(dir1) in e0441[0].details
            assert str(dir2) in e0441[0].details


