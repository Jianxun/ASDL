"""
P0701: Unknown Top-Level Section
"""

import pytest
from src.asdl.parser import ASDLParser
from src.asdl.diagnostics import DiagnosticSeverity


@pytest.mark.parametrize("unknown_key", ["models", "future_feature"])
def test_p0701_unknown_top_level_section(unknown_key: str):
    yaml_content = f"""
file_info:
  top_module: "test"
{unknown_key}:
  option: true
"""
    parser = ASDLParser()
    asdl_file, diagnostics = parser.parse_string(yaml_content)

    assert asdl_file is not None
    assert len(diagnostics) == 1
    d = diagnostics[0]
    assert d.code == "P0701"
    assert d.severity == DiagnosticSeverity.WARNING

