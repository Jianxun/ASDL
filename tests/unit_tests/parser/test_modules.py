"""
Test Module parsing for the refactored ASDL parser.
"""

import pytest
from pathlib import Path
import sys

# Add src to path for testing
test_dir = Path(__file__).parent
project_root = test_dir.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from asdl.parser import ASDLParser
from asdl.data_structures import Module, Port, Instance, PortConstraints

class TestModulesParsing:
    """Test Module section parsing (no validation)."""

    def test_parse_basic_module(self):
        """Test parsing a basic module with ports and one instance."""
        yaml_content = """
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
        asdl_file = parser.parse_string(yaml_content)

        assert "inverter" in asdl_file.modules
        module = asdl_file.modules["inverter"]

        assert isinstance(module, Module)
        assert module.doc == "A simple inverter."
        
        # Check ports
        assert module.ports is not None
        assert "in" in module.ports
        port_in = module.ports["in"]
        assert isinstance(port_in, Port)
        assert port_in.dir == "in"
        assert port_in.type == "voltage"

        # Check instances
        assert module.instances is not None
        assert "MN1" in module.instances
        instance = module.instances["MN1"]
        assert isinstance(instance, Instance)
        assert instance.model == "nmos_test"
        assert instance.mappings == {"G": "in", "D": "out"}

    def test_parse_module_all_fields(self):
        """Test parsing a module with all possible fields populated."""
        yaml_content = """
modules:
  full_module:
    doc: "A complete module."
    ports:
      in: {dir: "in"}
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
        asdl_file = parser.parse_string(yaml_content)

        assert "full_module" in asdl_file.modules
        module = asdl_file.modules["full_module"]

        assert module.doc == "A complete module."
        assert module.ports is not None and "in" in module.ports
        assert module.internal_nets == ["net1", "net2"]
        assert module.parameters == {"param1": "value1"}
        assert module.instances is not None and "I1" in module.instances
        assert module.metadata == {"version": 2} 