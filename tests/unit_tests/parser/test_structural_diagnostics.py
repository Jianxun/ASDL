import pytest
from asdl.parser import ASDLParser
from asdl.diagnostics import DiagnosticSeverity

def test_missing_file_info_section():
    """
    Test that P102 is raised if the 'file_info' section is missing.
    """
    asdl_str = """
modules:
    test_module:
        ports:
            in: { direction: input }
"""
    parser = ASDLParser()
    asdl_file, diagnostics = parser.parse_string(asdl_str)
    
    assert asdl_file is None
    assert len(diagnostics) == 1
    diagnostic = diagnostics[0]
    assert diagnostic.code == "P102"
    assert diagnostic.severity == DiagnosticSeverity.ERROR
    assert "'file_info' is a mandatory section" in diagnostic.details

def test_invalid_modules_section_type():
    """
    Test that P103 is raised if the 'modules' section is not a dictionary.
    """
    asdl_str = """
file_info:
    top_module: "test"
modules:
    - name: test_module
      ports:
        in: { direction: input }
"""
    parser = ASDLParser()
    asdl_file, diagnostics = parser.parse_string(asdl_str)
    
    assert asdl_file is not None # The file should parse, but with errors.
    assert len(diagnostics) == 1
    diagnostic = diagnostics[0]
    assert diagnostic.code == "P103"
    assert diagnostic.severity == DiagnosticSeverity.ERROR
    assert "section 'modules' must be a dictionary" in diagnostic.details 