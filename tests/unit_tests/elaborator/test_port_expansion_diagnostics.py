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
    assert "Pattern cannot be empty" in diagnostic.message
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
    assert "Pattern must have at least 2 items" in diagnostic.message

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
    assert "At least one item must be non-empty" in diagnostic.message 