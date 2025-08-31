"""
P0602: Dual Variables Syntax
"""

from src.asdl.parser import ASDLParser


def test_p0602_dual_variables_syntax():
    yaml_content = """
file_info:
  top_module: "test"
modules:
  m:
    variables: {x: 1}
    vars: {x: 2}
    spice_template: "R{name} {n1} {n2} {R}"
"""
    parser = ASDLParser()
    asdl_file, diagnostics = parser.parse_string(yaml_content)

    assert asdl_file is not None
    assert any(d.code == "P0602" for d in diagnostics)

