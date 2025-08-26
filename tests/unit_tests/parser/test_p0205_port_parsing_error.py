"""
P0205: Port Parsing Error
"""

from src.asdl.parser import ASDLParser


def test_p0205_port_parsing_error_from_invalid_enum():
    yaml_content = """
file_info:
  top_module: "test"
modules:
  m:
    ports:
      a:
        dir: invalid_dir_value
        type: voltage
    spice_template: "X m"
"""
    parser = ASDLParser()
    asdl_file, diagnostics = parser.parse_string(yaml_content)

    assert asdl_file is not None
    assert any(d.code == "P0205" for d in diagnostics)

