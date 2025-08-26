"""
P0250: Missing Instance Model
"""

from src.asdl.parser import ASDLParser


def test_p0250_missing_instance_model():
    yaml_content = """
file_info:
  top_module: "test"
modules:
  m:
    instances:
      M1:
        mappings: {}
"""
    parser = ASDLParser()
    asdl_file, diagnostics = parser.parse_string(yaml_content)

    assert asdl_file is not None
    assert any(d.code == "P0250" for d in diagnostics)


