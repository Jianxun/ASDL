"""
P0101: Invalid YAML Syntax
"""

from src.asdl.parser import ASDLParser


def test_p0101_invalid_yaml_syntax():
    parser = ASDLParser()
    asdl_file, diagnostics = parser.parse_string("key: [unclosed bracket")

    assert asdl_file is None
    assert len(diagnostics) == 1
    d = diagnostics[0]
    assert d.code == "P0101"

