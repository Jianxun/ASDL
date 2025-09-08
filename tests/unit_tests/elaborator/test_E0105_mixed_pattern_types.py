from asdl.parser import ASDLParser
from asdl.elaborator import Elaborator
from asdl.diagnostics import DiagnosticSeverity


def test_E0105_mixed_pattern_in_port():
    asdl_str = """
file_info:
    top_module: "test_module"
modules:
    test_module:
        ports:
            "in<p,n>[0]":
                dir: IN
                type: signal
        spice_template: "test_module {in<p,n>[0]}"
"""
    parser = ASDLParser()
    asdl_file, parser_diags = parser.parse_string(asdl_str)
    assert not parser_diags
    elaborator = Elaborator()
    _, diagnostics = elaborator.elaborate(asdl_file)
    assert len(diagnostics) == 1
    d = diagnostics[0]
    assert d.code == "E0105"
    assert d.severity == DiagnosticSeverity.ERROR


def test_E0105_mixed_pattern_in_instance():
    asdl_str = """
file_info:
    top_module: "test_module"
modules:
    test_module:
        instances:
            "M<1,2>[0]":
                model: some_model
"""
    parser = ASDLParser()
    asdl_file, parser_diags = parser.parse_string(asdl_str)
    assert not parser_diags
    elaborator = Elaborator()
    _, diagnostics = elaborator.elaborate(asdl_file)
    assert len(diagnostics) == 1
    d = diagnostics[0]
    assert d.code == "E0105"
    assert d.severity == DiagnosticSeverity.ERROR

