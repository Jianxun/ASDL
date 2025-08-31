"""
P0201: Missing Required Section ('file_info')
"""

from src.asdl.parser import ASDLParser
from src.asdl.diagnostics import DiagnosticSeverity


def test_p0201_missing_file_info_section():
    yaml_content = """
modules: {}
"""
    parser = ASDLParser()
    asdl_file, diagnostics = parser.parse_string(yaml_content)

    assert asdl_file is None
    assert len(diagnostics) == 1
    d = diagnostics[0]
    assert d.code == "P0201"
    assert d.severity == DiagnosticSeverity.ERROR

