"""
P0102: Invalid Root Type
"""

from src.asdl.parser import ASDLParser


def test_p0102_invalid_root_type():
    parser = ASDLParser()
    asdl_file, diagnostics = parser.parse_string("- item1\n- item2")

    assert asdl_file is None
    assert len(diagnostics) == 1
    d = diagnostics[0]
    assert d.code == "P0102"

