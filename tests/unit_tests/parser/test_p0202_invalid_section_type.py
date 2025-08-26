"""
P0202: Invalid Section Type
"""

from src.asdl.parser import ASDLParser
from src.asdl.diagnostics import DiagnosticSeverity


def test_p0202_invalid_modules_section_type():
    yaml_content = """
file_info:
  top_module: "test"
modules:
  - not_a_dict
"""
    parser = ASDLParser()
    asdl_file, diagnostics = parser.parse_string(yaml_content)

    assert asdl_file is not None
    assert len(diagnostics) == 1
    d = diagnostics[0]
    assert d.code == "P0202"
    assert d.severity == DiagnosticSeverity.ERROR

