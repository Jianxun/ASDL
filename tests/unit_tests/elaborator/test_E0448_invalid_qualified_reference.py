"""
E0448: Invalid Qualified Reference Format

Covers diagnostic creation and orchestrator/validator emission for malformed
qualified references in both model_alias and instance model references.
"""

import tempfile
from pathlib import Path

from asdl.elaborator.import_.diagnostics import ImportDiagnostics
from asdl.elaborator.import_.import_resolver import ImportResolver
from asdl.elaborator.import_.reference_validator import ReferenceValidator
from asdl.diagnostics import DiagnosticSeverity
from asdl.data_structures import ASDLFile, FileInfo, Module


class TestE0448InvalidQualifiedReference:
    def test_diagnostic_generation_model_alias_invalid(self):
        diag_gen = ImportDiagnostics()
        diagnostic = diag_gen.create_invalid_model_alias_format_error(
            "my_alias", "lib1."
        )
        assert diagnostic.code == "E0448"
        assert diagnostic.title == "Invalid Model Alias Reference"
        assert diagnostic.severity == DiagnosticSeverity.ERROR
        assert "lib1." in diagnostic.details

    def test_diagnostic_generation_instance_invalid(self):
        diag_gen = ImportDiagnostics()
        diagnostic = diag_gen.create_invalid_qualified_reference_error(".bad")
        assert diagnostic.code == "E0448"
        assert diagnostic.title == "Invalid Qualified Reference"
        assert diagnostic.severity == DiagnosticSeverity.ERROR

    def test_parser_emits_p0503_for_invalid_model_alias(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            main_file_path = temp_path / "main.asdl"
            main_file_path.write_text(
                """
file_info:
  top_module: top
imports:
  lib1: devices.asdl
model_alias:
  bad: lib1.
modules:
  top:
    instances: {}
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
            # Parser validates model_alias format and emits P0503; invalid entries are dropped
            p0503 = [d for d in diagnostics if d.code == "P0503"]
            assert len(p0503) >= 1
            assert any("Invalid Model Alias Format" in d.title for d in p0503)

    def test_validator_emits_e0448_for_invalid_instance_reference(self):
        # Build minimal in-memory ASDL file with an invalid qualified instance reference
        main = ASDLFile(
            file_info=FileInfo(),
            modules={
                "top": Module(instances={}),
            },
            imports={"lib1": "devices.asdl"},
            model_alias=None,
        )
        # Inject an invalid qualified reference into the instance list
        # Use a small YAML file to leverage parser semantics
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            main_file_path = temp_path / "main.asdl"
            main_file_path.write_text(
                """
file_info:
  top_module: top
imports:
  lib1: devices.asdl
modules:
  top:
    instances:
      I_BAD: {model: lib1., mappings: {}}
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
            e0448 = [d for d in diagnostics if d.code == "E0448"]
            assert len(e0448) >= 1
            assert any("Invalid Qualified Reference" in d.title for d in e0448)


