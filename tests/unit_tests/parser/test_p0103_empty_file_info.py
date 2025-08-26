"""
P0103: Empty File (INFO)
"""

from src.asdl.parser import ASDLParser
from src.asdl.diagnostics import DiagnosticSeverity


def test_p0103_empty_file_emits_info_and_returns_none():
    yaml_content = """\n"""
    parser = ASDLParser(emit_empty_file_info=True)
    asdl_file, diagnostics = parser.parse_string(yaml_content)

    assert asdl_file is None
    p0103 = [d for d in diagnostics if d.code == "P0103"]
    assert len(p0103) == 1
    assert p0103[0].severity == DiagnosticSeverity.INFO


