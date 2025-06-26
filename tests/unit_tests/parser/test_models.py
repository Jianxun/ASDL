"""
Test DeviceModel parsing for the refactored ASDL parser.
"""

import pytest
from pathlib import Path
import sys

# Add src to path for testing
test_dir = Path(__file__).parent
project_root = test_dir.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from asdl.parser import ASDLParser
from asdl.data_structures import DeviceModel
from asdl.data_structures import PrimitiveType

class TestModelsParsing:
    """Test DeviceModel section parsing (no validation)."""

    def test_parse_single_basic_model(self):
        """Test parsing a single, basic device model."""
        yaml_content = """
file_info:
  top_module: "test"
models:
  nmos_test:
    type: pdk_device
    ports: ["D", "G", "S", "B"]
    device_line: "M_nmos_test D G S B nfet_03v3"
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)

        assert asdl_file is not None
        assert not diagnostics
        assert "nmos_test" in asdl_file.models
        model = asdl_file.models["nmos_test"]
        assert model.type == PrimitiveType.PDK_DEVICE
        assert model.ports == ["D", "G", "S", "B"]
        assert model.device_line == "M_nmos_test D G S B nfet_03v3"
        assert model.doc is None
        assert model.parameters is None
        assert model.metadata is None

    def test_parse_multiple_models_with_all_fields(self):
        """Test parsing multiple models with all fields populated."""
        yaml_content = """
file_info:
  top_module: "test"
models:
  nmos_full:
    type: pdk_device
    ports: ["D", "G", "S", "B"]
    device_line: "M_nmos D G S B nfet"
    doc: "An NMOS transistor"
    parameters:
      w: "1u"
      l: "0.1u"
    metadata:
      version: 1
  pmos_full:
    type: spice_device
    ports: ["D", "G", "S", "B"]
    device_line: "M_pmos D G S B pfet"
    doc: "A PMOS transistor"
    parameters:
      w: "2u"
      l: "0.1u"
    metadata:
      author: "tester"
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)

        assert asdl_file is not None
        assert not diagnostics
        assert len(asdl_file.models) == 2

        nmos = asdl_file.models["nmos_full"]
        assert nmos.doc == "An NMOS transistor"
        assert nmos.parameters == {"w": "1u", "l": "0.1u"}
        assert nmos.metadata == {"version": 1}

        pmos = asdl_file.models["pmos_full"]
        assert pmos.type == PrimitiveType.SPICE_DEVICE
        assert pmos.doc == "A PMOS transistor"
        assert pmos.parameters == {"w": "2u", "l": "0.1u"}
        assert pmos.metadata == {"author": "tester"} 