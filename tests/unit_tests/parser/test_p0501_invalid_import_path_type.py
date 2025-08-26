"""
P0501: Invalid Import Path Type
"""

from src.asdl.parser import ASDLParser
from src.asdl.diagnostics import DiagnosticSeverity


def test_p0501_invalid_import_path_type():
    yaml_content = """
file_info:
  top_module: "test"
imports:
  invalid_import: 42
modules: {}
"""
    parser = ASDLParser()
    asdl_file, diagnostics = parser.parse_string(yaml_content)

    assert asdl_file is not None
    p0501 = [d for d in diagnostics if d.code == "P0501"]
    assert len(p0501) == 1
    assert p0501[0].severity == DiagnosticSeverity.ERROR

