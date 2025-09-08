import pytest
from asdl.data_structures import ASDLFile, Module, Port, FileInfo, PortDirection, PortType
from asdl.elaborator import Elaborator
from asdl.diagnostics import DiagnosticSeverity


def test_E0101_empty_literal_pattern_in_port_name():
    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="test_module"),
        modules={
            "test_module": Module(
                ports={
                    "in<>": Port(dir=PortDirection.IN, type=PortType.SIGNAL),
                },
                spice_template="test_module {in<>}",
            )
        },
    )

    elaborator = Elaborator()
    _, diagnostics = elaborator.elaborate(asdl_file)

    assert len(diagnostics) >= 1
    d = diagnostics[0]
    assert d.code == "E0101"
    assert d.severity == DiagnosticSeverity.ERROR
    assert "empty" in d.details.lower()

