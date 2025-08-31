"""
Test cases for bus pattern expansion in the Elaborator.

This suite focuses on expanding bus notations like `data[3:0]` into individual signals
and handling related error conditions as per the diagnostic codes documentation.
"""
import pytest
from asdl.data_structures import (
    ASDLFile,
    FileInfo,
    Module,
    Port,
    Instance,
    PortDirection,
    PortType,
)
from asdl.elaborator import Elaborator
from asdl.parser import ASDLParser


class TestBusExpansion:
    """
    Test bus expansion capabilities of the Elaborator.
    """

    def test_simple_port_bus_expansion_descending(self):
        """
        Tests that a simple bus pattern on a port, like `data[3:0]`,
        is correctly expanded into descending order.
        """
        asdl_string = """
        file_info:
            top_module: "test"
        modules:
            test:
                ports:
                    "data[3:0]":
                        dir: IN
                        type: SIGNAL
                spice_template: "test {data[3:0]}"
        """
        parser = ASDLParser()
        asdl_file, parse_diagnostics = parser.parse_string(asdl_string)
        assert not parse_diagnostics
        assert asdl_file is not None

        elaborator = Elaborator()
        elaborated_file, diagnostics = elaborator.elaborate(asdl_file)

        assert not diagnostics
        assert elaborated_file is not None

        test_module = elaborated_file.modules.get("test")
        assert test_module is not None
        assert test_module.ports is not None
        assert "data[3:0]" not in test_module.ports

        expected_ports = ["data3", "data2", "data1", "data0"]
        assert list(test_module.ports.keys()) == expected_ports

        for port_name in expected_ports:
            assert port_name in test_module.ports
            port = test_module.ports[port_name]
            assert port.dir == PortDirection.IN
            assert port.type == PortType.SIGNAL

    def test_simple_port_bus_expansion_ascending(self):
        """
        Tests that a simple bus pattern on a port, like `data[0:3]`,
        is correctly expanded into ascending order.
        """
        asdl_string = """
        file_info:
            top_module: "test"
        modules:
            test:
                ports:
                    "data[0:3]":
                        dir: IN
                        type: SIGNAL
                spice_template: "test {data[0:3]}"
        """
        parser = ASDLParser()
        asdl_file, parse_diagnostics = parser.parse_string(asdl_string)
        assert not parse_diagnostics
        assert asdl_file is not None

        elaborator = Elaborator()
        elaborated_file, diagnostics = elaborator.elaborate(asdl_file)
        
        assert not diagnostics
        assert elaborated_file is not None

        test_module = elaborated_file.modules.get("test")
        assert test_module is not None
        assert test_module.ports is not None
        assert "data[0:3]" not in test_module.ports
        
        expected_ports = ["data0", "data1", "data2", "data3"]
        assert list(test_module.ports.keys()) == expected_ports

        for port_name in expected_ports:
            assert port_name in test_module.ports
            port = test_module.ports[port_name]
            assert port.dir == PortDirection.IN
            assert port.type == PortType.SIGNAL