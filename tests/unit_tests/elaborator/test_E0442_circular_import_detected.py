"""
E0442: Circular Import Detected

Covers end-to-end circular dependency detection via orchestrator.
"""

import tempfile
from pathlib import Path

from asdl.elaborator.import_.import_resolver import ImportResolver


class TestE0442CircularImportDetected:
    def test_circular_import_detection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # File A imports B
            file_a_path = temp_path / "module_a.asdl"
            file_a_path.write_text(
                """
file_info:
  top_module: module_a
imports:
  module_b: module_b.asdl
modules:
  circuit_a:
    instances:
      B_INST: {model: module_b.circuit_b}
"""
            )

            # File B imports A (circular)
            file_b_path = temp_path / "module_b.asdl"
            file_b_path.write_text(
                """
file_info:
  top_module: module_b
imports:
  module_a: module_a.asdl
modules:
  circuit_b:
    instances:
      A_INST: {model: module_a.circuit_a}
"""
            )

            resolver = ImportResolver()
            result, diagnostics = resolver.resolve_imports(
                file_a_path, search_paths=[temp_path]
            )

            assert result is not None
            circular_errors = [d for d in diagnostics if d.code == "E0442"]
            assert len(circular_errors) >= 1
            assert any("circular" in d.title.lower() for d in circular_errors)


