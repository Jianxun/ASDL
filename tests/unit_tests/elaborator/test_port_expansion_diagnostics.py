import pytest
from asdl.data_structures import (
    ASDLFile,
    Module,
    Port,
    FileInfo,
    PortDirection,
    SignalType,
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
                    "in<>": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                }
            )
        },
    )

    elaborator = Elaborator()
    elaborated_file, diagnostics = elaborator.elaborate(asdl_file)

    assert len(diagnostics) == 1
    diagnostic = diagnostics[0]
    assert diagnostic.severity == DiagnosticSeverity.ERROR
    assert "A literal pattern `<>` cannot be empty" in diagnostic.details
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
                    "in<p>": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                }
            )
        },
    )

    elaborator = Elaborator()
    elaborated_file, diagnostics = elaborator.elaborate(asdl_file)

    assert len(diagnostics) == 1
    diagnostic = diagnostics[0]
    assert diagnostic.severity == DiagnosticSeverity.ERROR
    assert "A literal pattern must contain at least two items" in diagnostic.details

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
                    "in<,>": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                }
            )
        },
    )

    elaborator = Elaborator()
    elaborated_file, diagnostics = elaborator.elaborate(asdl_file)

    assert len(diagnostics) == 1
    diagnostic = diagnostics[0]
    assert diagnostic.severity == DiagnosticSeverity.ERROR
    assert "All items in a literal pattern were empty strings" in diagnostic.details 