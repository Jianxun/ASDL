"""
P0511: Invalid Port Direction Enum
"""

from src.asdl.parser import ASDLParser
from src.asdl.diagnostics import DiagnosticSeverity


def test_p0511_invalid_port_direction_enum():
    yaml_content = """
file_info:
  top_module: "m"
modules:
  m:
    ports:
      a:
        dir: input
        type: voltage
    spice_template: "R {a} {a} 1k"
"""
    parser = ASDLParser()
    asdl_file, diagnostics = parser.parse_string(yaml_content)

    assert asdl_file is not None
    p0511 = [d for d in diagnostics if d.code == "P0511"]
    assert len(p0511) == 1
    assert p0511[0].severity == DiagnosticSeverity.ERROR


