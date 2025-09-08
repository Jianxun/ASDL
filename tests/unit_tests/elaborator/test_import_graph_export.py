from pathlib import Path
import tempfile

from src.asdl.parser import ASDLParser
from src.asdl.elaborator.import_.coordinator import ImportCoordinator
from src.asdl.elaborator.import_.dependency_graph import export_import_graph


def test_export_import_graph_relative_paths():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        main_text = """
file_info:
  top_module: main
imports:
  lib: lib.asdl
modules:
  top:
    instances:
      X1: {model: lib.prim}
"""
        lib_text = """
file_info:
  top_module: lib
modules:
  prim:
    spice_template: "R{name} {n1} {n2} 1k"
    ports: {n1: {dir: inout}, n2: {dir: inout}}
"""

        main_file = temp_path / "main.asdl"
        lib_file = temp_path / "lib.asdl"
        main_file.write_text(main_text)
        lib_file.write_text(lib_text)

        coord = ImportCoordinator()
        # Build graph via coordinator internals
        parser = ASDLParser()
        main_asdl, _ = parser.parse_file(str(main_file))
        graph, alias_map, loaded_files, _ = coord.graph_builder.build(
            main_asdl, main_file.resolve(), search_paths=[temp_path]
        )

        exported = export_import_graph(graph, alias_map, base_dir=temp_path)

        # Expect two nodes with relative paths
        paths = sorted(n["path"] for n in exported["nodes"])
        assert paths == ["lib.asdl", "main.asdl"]

        # Expect one edge main -> lib in relative form
        edges = exported["edges"]
        assert {e["from"] for e in edges} == {"main.asdl"}
        assert {e["to"] for e in edges} == {"lib.asdl"}

        # Alias map should point 'lib' -> lib.asdl
        assert exported["alias_map"]["main.asdl"]["lib"] == "lib.asdl"


