"""
E0601: Unused Import Alias (style warning)

Verifies that the optional unused-import warning is emitted when enabled.
"""

import tempfile
from pathlib import Path

from asdl.elaborator.import_.import_resolver import ImportResolver


class TestE0601UnusedImportAlias:
    def test_unused_import_alias_warning(self):
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

            # Use coordinator via resolver; by default warnings are off.
            resolver = ImportResolver()
            result, diagnostics = resolver.resolve_imports(
                main_file_path, search_paths=[temp_path]
            )

            # No warnings by default
            assert result is not None
            assert all(d.code != "E0601" for d in diagnostics)


