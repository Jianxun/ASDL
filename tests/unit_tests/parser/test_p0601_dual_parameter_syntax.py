"""
P0601: Dual Parameter Syntax
"""

from src.asdl.parser import ASDLParser


def test_p0601_dual_parameter_syntax():
    yaml_content = """
file_info:
  top_module: "test"
modules:
  m:
    parameters: {R: 1k}
    params: {R: 2k}
    spice_template: "R{name} {n1} {n2} {R}"
"""
    parser = ASDLParser()
    asdl_file, diagnostics = parser.parse_string(yaml_content)

    assert asdl_file is not None
    assert any(d.code == "P0601" for d in diagnostics)

