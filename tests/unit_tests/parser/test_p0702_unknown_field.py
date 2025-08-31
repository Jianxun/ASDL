"""
P0702: Unknown Field
"""

from src.asdl.parser import ASDLParser
from src.asdl.diagnostics import DiagnosticSeverity


def test_p0702_unknown_field_in_module():
    yaml_content = """
file_info:
  top_module: "test"
modules:
  m:
    spice_template: "X m"
    unknown: 1
"""
    parser = ASDLParser()
    asdl_file, diagnostics = parser.parse_string(yaml_content)

    assert asdl_file is not None
    assert len(diagnostics) == 1
    d = diagnostics[0]
    assert d.code == "P0702"
    assert d.severity == DiagnosticSeverity.WARNING

