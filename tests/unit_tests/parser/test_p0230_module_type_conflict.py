"""
P0230: Module Type Conflict (both spice_template and instances)
"""

from src.asdl.parser import ASDLParser


def test_p0230_module_type_conflict():
    yaml_content = """
file_info:
  top_module: "test"
modules:
  bad:
    spice_template: "X bad"
    instances:
      X1: { model: some }
"""
    parser = ASDLParser()
    asdl_file, diagnostics = parser.parse_string(yaml_content)

    assert any(d.code == "P0230" for d in diagnostics)

