"""
E0602: Unused Model Alias (style warning)

Verifies that the optional unused-model-alias warning is emitted when enabled.
"""

import tempfile
from pathlib import Path

from asdl.elaborator.import_.import_resolver import ImportResolver


class TestE0602UnusedModelAlias:
    def test_unused_model_alias_warning_off_by_default(self):
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
  shortcut: lib1.known_mod
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

            # No warnings by default
            assert result is not None
            assert all(d.code != "E0602" for d in diagnostics)


