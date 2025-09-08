"""
ImportResolver flow tests (simple resolution, aliases, transitive, search path).
Moved from import_/ to top-level elaborator tests.
"""

import tempfile
from pathlib import Path

from asdl.elaborator.import_.import_resolver import ImportResolver
from asdl.diagnostics import DiagnosticSeverity


class TestImportResolverFlow:
    def setup_method(self):
        self.resolver = ImportResolver()

    def test_simple_import_resolution(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            main_file_path = temp_path / "main.asdl"
            main_file_path.write_text(
                """
file_info:
  top_module: main
imports:
  std_lib: std_devices.asdl
modules:
  inverter:
    ports: {in: {dir: in}, out: {dir: out}}
    instances:
      M1: {model: std_lib.nmos_unit, mappings: {D: out, G: in, S: gnd}}
"""
            )

            std_file_path = temp_path / "std_devices.asdl"
            std_file_path.write_text(
                """
file_info:
  top_module: std_devices
modules:
  nmos_unit:
    ports: {D: {dir: out}, G: {dir: in}, S: {dir: out}}
    spice_template: "MN{name} {D} {G} {S} nmos"
"""
            )

            result, diagnostics = self.resolver.resolve_imports(
                main_file_path,
                search_paths=[temp_path]
            )

            assert result is not None
            assert all(d.severity != DiagnosticSeverity.ERROR for d in diagnostics)
            assert len(result.modules) == 2
            assert "inverter" in result.modules
            assert "nmos_unit" in result.modules
            nmos_module = result.modules["nmos_unit"]
            assert nmos_module.spice_template == "MN{name} {D} {G} {S} nmos"

    def test_model_alias_resolution(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            main_file_path = temp_path / "main.asdl"
            main_file_path.write_text(
                """
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
"""
            )

            device_file_path = temp_path / "device_lib.asdl"
            device_file_path.write_text(
                """
file_info:
  top_module: device_lib
modules:
  nmos_unit:
    ports: {D: {dir: out}, G: {dir: in}, S: {dir: out}}
    spice_template: "MN{name} {D} {G} {S} nmos"
  pmos_unit:
    ports: {D: {dir: out}, G: {dir: in}, S: {dir: out}}
    spice_template: "MP{name} {D} {G} {S} pmos"
"""
            )

            result, diagnostics = self.resolver.resolve_imports(
                main_file_path,
                search_paths=[temp_path]
            )

            assert result is not None
            assert all(d.severity != DiagnosticSeverity.ERROR for d in diagnostics)
            assert len(result.modules) == 3
            assert "inverter" in result.modules
            assert "nmos_unit" in result.modules
            assert "pmos_unit" in result.modules
            assert result.model_alias is not None
            assert "nmos" in result.model_alias
            assert "pmos" in result.model_alias

    def test_transitive_imports(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            main_file_path = temp_path / "main.asdl"
            main_file_path.write_text(
                """
file_info:
  top_module: main
imports:
  analog_lib: analog_blocks.asdl
modules:
  circuit:
    instances:
      AMP: {model: analog_lib.amplifier}
"""
            )

            analog_file_path = temp_path / "analog_blocks.asdl"
            analog_file_path.write_text(
                """
file_info:
  top_module: analog_blocks
imports:
  primitives: device_primitives.asdl
modules:
  amplifier:
    instances:
      M1: {model: primitives.nmos}
      M2: {model: primitives.pmos}
"""
            )

            primitives_file_path = temp_path / "device_primitives.asdl"
            primitives_file_path.write_text(
                """
file_info:
  top_module: device_primitives
modules:
  nmos:
    spice_template: "MN{name} {D} {G} {S} nmos"
  pmos:
    spice_template: "MP{name} {D} {G} {S} pmos"
"""
            )

            result, diagnostics = self.resolver.resolve_imports(
                main_file_path,
                search_paths=[temp_path]
            )

            assert result is not None
            assert len(diagnostics) == 0
            assert len(result.modules) == 4
            assert "circuit" in result.modules
            assert "amplifier" in result.modules
            assert "nmos" in result.modules
            assert "pmos" in result.modules

    def test_search_path_resolution(self):
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
  test_module:
    instances:
      INST: {model: common_lib.shared_component}
"""
            )

            shared_dir = dir2 / "shared"
            shared_dir.mkdir()
            shared_file_path = shared_dir / "common.asdl"
            shared_file_path.write_text(
                """
file_info:
  top_module: common
modules:
  shared_component:
    spice_template: "shared template"
"""
            )

            result, diagnostics = self.resolver.resolve_imports(
                main_file_path,
                search_paths=[dir1, dir2]
            )

            assert result is not None
            assert len(diagnostics) == 0
            assert "shared_component" in result.modules
            assert result.modules["shared_component"].spice_template == "shared template"


