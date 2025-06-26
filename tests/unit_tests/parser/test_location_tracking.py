"""
Test location tracking for all ASDL data structures during parsing.
"""

import pytest
from pathlib import Path
import sys

# Add src to path for testing
test_dir = Path(__file__).parent
project_root = test_dir.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from asdl.parser import ASDLParser
from asdl.data_structures import (
    DeviceModel,
    Module,
    Port,
    Instance,
    FileInfo,
    ASDLFile,
)

class TestLocationTracking:
    """Test that all data structures have correct location info after parsing."""

    def test_file_info_location(self):
        """Test line/col tracking for the FileInfo object."""
        yaml_content = """
# comment
file_info:
  top_module: "inverter"
  doc: "An example inverter."
"""
        parser = ASDLParser()
        asdl_file, _ = parser.parse_string(yaml_content)
        assert asdl_file is not None
        file_info = asdl_file.file_info
        assert file_info.start_line == 3
        assert file_info.start_col == 1

    def test_device_model_location(self):
        """Test line/col tracking for DeviceModel objects."""
        yaml_content = """
file_info:
  top_module: "test"
models:
  # nmos comment
  nmos_test:
    type: pdk_device
    ports: ["D", "G", "S", "B"]
  # pmos comment
  pmos_test:
    type: spice_device
    device_line: "M D G S B pfet"
"""
        parser = ASDLParser()
        asdl_file, _ = parser.parse_string(yaml_content)
        assert asdl_file is not None

        assert "nmos_test" in asdl_file.models
        nmos = asdl_file.models["nmos_test"]
        assert nmos.start_line == 6
        assert nmos.start_col == 3

        assert "pmos_test" in asdl_file.models
        pmos = asdl_file.models["pmos_test"]
        assert pmos.start_line == 10
        assert pmos.start_col == 3

    def test_module_location(self):
        """Test line/col tracking for Module objects."""
        yaml_content = """
file_info:
  top_module: "test"
modules:
  inverter:
    doc: "A simple inverter."
    ports:
      in:
        dir: in
      out:
        dir: out
  buffer:
    doc: "A simple buffer."
"""
        parser = ASDLParser()
        asdl_file, _ = parser.parse_string(yaml_content)
        assert asdl_file is not None

        assert "inverter" in asdl_file.modules
        inverter = asdl_file.modules["inverter"]
        assert inverter.start_line == 5
        assert inverter.start_col == 3

        assert "buffer" in asdl_file.modules
        buffer = asdl_file.modules["buffer"]
        assert buffer.start_line == 12
        assert buffer.start_col == 3

    def test_port_location(self):
        """Test line/col tracking for Port objects."""
        yaml_content = """
file_info:
  top_module: "test"
modules:
  inverter:
    ports:
      # port comment
      in:
        dir: in
      out:
        dir: out
"""
        parser = ASDLParser()
        asdl_file, _ = parser.parse_string(yaml_content)
        assert asdl_file is not None

        inverter = asdl_file.modules["inverter"]
        assert inverter.ports is not None
        assert "in" in inverter.ports
        port_in = inverter.ports["in"]
        assert port_in.start_line == 8
        assert port_in.start_col == 7

        assert "out" in inverter.ports
        port_out = inverter.ports["out"]
        assert port_out.start_line == 10
        assert port_out.start_col == 7

    def test_instance_location(self):
        """Test line/col tracking for Instance objects."""
        yaml_content = """
file_info:
  top_module: "test"
modules:
  inverter:
    instances:
      # instance comment
      M1:
        model: nmos
      M2:
        model: pmos
"""
        parser = ASDLParser()
        asdl_file, _ = parser.parse_string(yaml_content)
        assert asdl_file is not None

        inverter = asdl_file.modules["inverter"]
        assert inverter.instances is not None

        assert "M1" in inverter.instances
        m1 = inverter.instances["M1"]
        assert m1.start_line == 8
        assert m1.start_col == 7

        assert "M2" in inverter.instances
        m2 = inverter.instances["M2"]
        assert m2.start_line == 10
        assert m2.start_col == 7 