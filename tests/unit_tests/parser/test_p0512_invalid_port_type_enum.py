"""
P0512: Invalid Port Type Enum
"""

from src.asdl.parser import ASDLParser
from src.asdl.diagnostics import DiagnosticSeverity


def test_p0512_invalid_port_type_enum():
    yaml_content = """
file_info:
  top_module: "m"
modules:
  m:
    ports:
      a:
        dir: in
        type: volt
    spice_template: "R {a} {a} 1k"
"""
    parser = ASDLParser()
    asdl_file, diagnostics = parser.parse_string(yaml_content)

    assert asdl_file is not None
    p0512 = [d for d in diagnostics if d.code == "P0512"]
    assert len(p0512) == 1
    assert p0512[0].severity == DiagnosticSeverity.ERROR


