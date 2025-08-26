"""
P0240: Missing Port Direction
"""

from src.asdl.parser import ASDLParser


def test_p0240_missing_port_dir():
    yaml_content = """
file_info:
  top_module: "test"
modules:
  m:
    ports:
      a:
        type: voltage
    spice_template: "X m"
"""
    parser = ASDLParser()
    asdl_file, diagnostics = parser.parse_string(yaml_content)

    assert asdl_file is not None
    assert any(d.code == "P0240" for d in diagnostics)


