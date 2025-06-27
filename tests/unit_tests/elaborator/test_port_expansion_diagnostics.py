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
                    "in<,>": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                }
            )
        },
    )

    elaborator = Elaborator()
    elaborated_file, diagnostics = elaborator.elaborate(asdl_file)

    assert len(diagnostics) == 2
    codes = {d.code for d in diagnostics}
    assert "E107" in codes
    assert "E101" in codes

def test_mismatched_pattern_count_diagnostic():
    """
    Test that a diagnostic is generated when instance and mapping patterns
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
    assert diagnostic.code == "E102"
    assert "Mismatched pattern counts" in diagnostic.details 