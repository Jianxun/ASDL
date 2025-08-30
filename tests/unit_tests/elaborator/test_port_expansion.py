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


def test_basic_port_expansion():
    """
    Test that a simple <p,n> pattern in a port name is correctly expanded.
    """
    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="test_module"),
        modules={
            "test_module": Module(
                ports={
                    "in_<p,n>": Port(dir=PortDirection.IN, type=PortType.SIGNAL),
                    "vss": Port(dir=PortDirection.IN, type=PortType.SIGNAL),
                },
                spice_template="test_module {in_<p,n>} {vss}"
            )
        },
    )

    elaborator = Elaborator()
    elaborated_file, diagnostics = elaborator.elaborate(asdl_file)

    assert not diagnostics
    assert elaborated_file.modules is not None
    
    elaborated_module = elaborated_file.modules["test_module"]
    assert elaborated_module.ports is not None

    assert "in_p" in elaborated_module.ports
    assert "in_n" in elaborated_module.ports
    assert "in_<p,n>" not in elaborated_module.ports
    assert "vss" in elaborated_module.ports

    assert elaborated_module.ports["in_p"].dir == PortDirection.IN
    assert elaborated_module.ports["in_n"].dir == PortDirection.IN

def test_port_expansion_with_empty_item():
    """
    Test that a pattern with an empty item like 'clk<,_b>' expands correctly
    to 'clk' and 'clk_b'.
    """
    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="test_module"),
        modules={
            "test_module": Module(
                ports={
                    "clk<,_b>": Port(dir=PortDirection.IN, type=PortType.SIGNAL),
                },
                spice_template="test_module {clk<,_b>}"
            )
        },
    )

    elaborator = Elaborator()
    elaborated_file, diagnostics = elaborator.elaborate(asdl_file)

    assert not diagnostics
    assert elaborated_file.modules is not None
    
    elaborated_module = elaborated_file.modules["test_module"]
    assert elaborated_module.ports is not None

    assert "clk" in elaborated_module.ports
    assert "clk_b" in elaborated_module.ports
    assert "clk<,_b>" not in elaborated_module.ports
    
    assert elaborated_module.ports["clk"].dir == PortDirection.IN
    assert elaborated_module.ports["clk_b"].dir == PortDirection.IN 