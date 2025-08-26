"""
P0502: Invalid Import File Extension
"""

from src.asdl.parser import ASDLParser
from src.asdl.diagnostics import DiagnosticSeverity


def test_p0502_invalid_import_extension():
    yaml_content = """
file_info:
  top_module: "test"
imports:
  bad_ext: lib/invalid.txt
modules: {}
"""
    parser = ASDLParser()
    asdl_file, diagnostics = parser.parse_string(yaml_content)

    assert asdl_file is not None
    p0502 = [d for d in diagnostics if d.code == "P0502"]
    assert len(p0502) == 1
    assert p0502[0].severity == DiagnosticSeverity.ERROR

