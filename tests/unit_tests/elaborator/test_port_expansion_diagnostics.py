import pytest
from asdl.data_structures import (
    ASDLFile,
    Module,
    Port,
    FileInfo,
    PortDirection,
    PortType,
)
from asdl.elaborator import Elaborator
from asdl.diagnostics import Diagnostic, DiagnosticSeverity

def test_empty_pattern_diagnostic():
    """
    Test that an empty pattern like 'in<>' generates a diagnostic.
    """
    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="test_module"),
        models={},
        modules={
            "test_module": Module(
                ports={
                    "in<>": Port(dir=PortDirection.IN, type=PortType.SIGNAL),
                }
            )
        },
    )

    elaborator = Elaborator()
    elaborated_file, diagnostics = elaborator.elaborate(asdl_file)

    assert len(diagnostics) == 1
    diagnostic = diagnostics[0]
    assert diagnostic.severity == DiagnosticSeverity.ERROR
    assert "is empty" in diagnostic.details
    # TODO: Also assert on the location of the diagnostic 

def test_single_item_pattern_diagnostic():
    """
    Test that a pattern with only one item like 'in<p>' generates a diagnostic.
    """
    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="test_module"),
        models={},
        modules={
            "test_module": Module(
                ports={
                    "in<p>": Port(dir=PortDirection.IN, type=PortType.SIGNAL),
                }
            )
        },
    )

    elaborator = Elaborator()
    elaborated_file, diagnostics = elaborator.elaborate(asdl_file)

    assert len(diagnostics) == 1
    diagnostic = diagnostics[0]
    assert diagnostic.code == "E101"
    assert "contains only a single item" in diagnostic.details

def test_empty_items_pattern_diagnostic():
    """
    Test that a pattern with only empty items like 'in<,>' generates a diagnostic.
    """
    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="test_module"),
        models={},
        modules={
            "test_module": Module(
                ports={
                    "in<,>": Port(dir=PortDirection.IN, type=PortType.SIGNAL),
                }
            )
        },
    )

    elaborator = Elaborator()
    elaborated_file, diagnostics = elaborator.elaborate(asdl_file)

    assert len(diagnostics) >= 1
    # Should have an empty pattern item diagnostic
    empty_item_diagnostics = [d for d in diagnostics if d.code == "E107"]
    assert len(empty_item_diagnostics) >= 1

def test_mismatched_pattern_count_diagnostic():
    """
    Test that a diagnostic is generated when a port has a single item pattern.
    """
    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="test_module"),
        models={},
        modules={
            "test_module": Module(
                ports={
                    "in<p>": Port(dir=PortDirection.IN, type=PortType.SIGNAL),
                }
            )
        },
    )

    elaborator = Elaborator()
    elaborated_file, diagnostics = elaborator.elaborate(asdl_file)

    assert len(diagnostics) == 1
    diagnostic = diagnostics[0]
    assert diagnostic.code == "E101"
    assert "contains only a single item" in diagnostic.details 