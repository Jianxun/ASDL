"""
P0503: Invalid Model Alias Format
"""

from src.asdl.parser import ASDLParser


def test_p0503_non_string_reference():
    yaml_content = """
file_info:
  top_module: "test"
model_alias:
  local: 123
modules: {}
"""
    parser = ASDLParser()
    asdl_file, diagnostics = parser.parse_string(yaml_content)

    assert asdl_file is not None
    assert any(d.code == "P0503" for d in diagnostics)


def test_p0503_bad_pattern_reference():
    yaml_content = """
file_info:
  top_module: "test"
model_alias:
  local: alias_without_dot
modules: {}
"""
    parser = ASDLParser()
    asdl_file, diagnostics = parser.parse_string(yaml_content)

    assert asdl_file is not None
    assert any(d.code == "P0503" for d in diagnostics)

