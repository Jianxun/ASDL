"""
P0231: Incomplete Module Definition (neither spice_template nor instances)
"""

from src.asdl.parser import ASDLParser


def test_p0231_incomplete_module_definition():
    yaml_content = """
file_info:
  top_module: "test"
modules:
  empty:
    ports:
      in: { dir: in, type: voltage }
"""
    parser = ASDLParser()
    asdl_file, diagnostics = parser.parse_string(yaml_content)

    assert any(d.code == "P0231" for d in diagnostics)

