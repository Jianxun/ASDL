"""
Parser module behavior tests.
"""

import pytest
from pathlib import Path
import sys

from asdl.parser import ASDLParser
from asdl.data_structures import Module, Port, Instance, PortDirection, PortType

class TestModulesParsing:
    """Test Module section parsing (no validation)."""

    def test_parse_basic_module(self):
        """Test parsing a basic module with ports and one instance."""
        yaml_content = """
file_info:
  top_module: "test"
modules:
  inverter:
    doc: "A simple inverter."
    ports:
      in:
        dir: "in"
        type: "voltage"
      out:
        dir: "out"
        type: "voltage"
    instances:
      MN1:
        model: "nmos_test"
        mappings:
          G: "in"
          D: "out"
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)

        assert asdl_file is not None
        assert not diagnostics
        assert "inverter" in asdl_file.modules

        inverter = asdl_file.modules["inverter"]
        assert inverter.doc == "A simple inverter."
        
        assert inverter.ports is not None
        assert "in" in inverter.ports
        assert "out" in inverter.ports
        assert inverter.ports["in"].dir == PortDirection.IN
        assert inverter.ports["in"].type == PortType.SIGNAL

        assert inverter.instances is not None
        assert "MN1" in inverter.instances
        instance = inverter.instances["MN1"]
        assert instance.model == "nmos_test"
        assert instance.mappings == {"G": "in", "D": "out"}

    def test_parse_module_all_fields(self):
        """Test parsing a module with all possible fields populated."""
        yaml_content = """
file_info:
  top_module: "test"
modules:
  full_module:
    doc: "A complete module."
    ports:
      in: {dir: "in", type: "digital"}
    internal_nets: ["net1", "net2"]
    parameters:
      param1: "value1"
    instances:
      I1:
        model: "some_model"
        mappings: {A: "net1"}
    metadata:
      version: 2
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)

        assert asdl_file is not None
        assert not diagnostics
        assert "full_module" in asdl_file.modules

        module = asdl_file.modules["full_module"]
        assert module.doc == "A complete module."
        assert module.ports and "in" in module.ports
        assert module.internal_nets == ["net1", "net2"]
        assert module.parameters == {"param1": "value1"}
        assert module.instances and "I1" in module.instances
        assert module.metadata == {"version": 2} 