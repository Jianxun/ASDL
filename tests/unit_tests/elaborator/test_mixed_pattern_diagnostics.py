import pytest
from asdl.data_structures import ASDLFile, Locatable
from asdl.diagnostics import Diagnostic, DiagnosticSeverity
from asdl.parser import ASDLParser
from asdl.elaborator import Elaborator

def test_mixed_pattern_in_port():
    """
    Test that E103 is raised for a port with mixed patterns.
    """
    asdl_str = """
file_info:
    top_module: "test_module"
modules:
    test_module:
        ports:
            "in<p,n>[0]":
                dir: in
                type: digital
"""
    parser = ASDLParser()
    asdl_file, parser_diags = parser.parse_string(asdl_str)
    assert not parser_diags, "Parser should not produce diagnostics on valid input."
    assert asdl_file is not None, "Parser should successfully parse the string."
    
    elaborator = Elaborator()
    _, diagnostics = elaborator.elaborate(asdl_file)
    
    assert len(diagnostics) == 1
    diagnostic = diagnostics[0]
    assert diagnostic.code == "E103"
    assert diagnostic.severity == DiagnosticSeverity.ERROR
    assert "contains both a literal ('<>') and bus ('[]') pattern" in diagnostic.details
    assert diagnostic.location is not None
    assert diagnostic.location.start_line == 7

def test_mixed_pattern_in_instance():
    """
    Test that E103 is raised for an instance with mixed patterns.
    """
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
    assert not parser_diags, "Parser should not produce diagnostics on valid input."
    assert asdl_file is not None, "Parser should successfully parse the string."

    elaborator = Elaborator()
    _, diagnostics = elaborator.elaborate(asdl_file)
    
    assert len(diagnostics) == 1
    diagnostic = diagnostics[0]
    assert diagnostic.code == "E103"
    assert diagnostic.severity == DiagnosticSeverity.ERROR
    assert "contains both a literal ('<>') and bus ('[]') pattern" in diagnostic.details
    assert diagnostic.location is not None
    assert diagnostic.location.start_line == 7

def test_no_mixed_pattern_diagnostics():
    """
    Test that no diagnostics are raised for valid port/instance names.
    """
    asdl_str = """
file_info:
    top_module: "test_module"
modules:
    test_module:
        ports:
            in<p,n>:
                dir: in
                type: digital
        instances:
            M<1,2>:
                model: some_model
"""
    parser = ASDLParser()
    asdl_file, parser_diags = parser.parse_string(asdl_str)
    assert not parser_diags, "Parser should not produce diagnostics on valid input."
    assert asdl_file is not None, "Parser should successfully parse the string."

    elaborator = Elaborator()
    _, diagnostics = elaborator.elaborate(asdl_file)
    
    assert len(diagnostics) == 0 