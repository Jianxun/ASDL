"""
Test cases for the universal metadata field.

This tests the new metadata field that will be added to all major ASDL data structures.
The metadata field provides extensible storage for annotations, tool-specific data, and design intent.
"""

import pytest
from pathlib import Path
from src.asdl.data_structures import (
    ASDLFile, FileInfo, DeviceModel, PrimitiveType, 
    Port, PortDirection, PortType, Module, Instance
)
from asdl.parser import ASDLParser

test_dir = Path(__file__).resolve().parent
project_root = test_dir.parent.parent.parent

class TestMetadataField:
    """Test cases for universal metadata field across all data structures."""
    
    def test_asdl_file_metadata(self):
        """Test metadata field on ASDLFile."""
        file_info = FileInfo(
            top_module="test_module",
            doc="Test documentation",
            revision="1.0",
            author="Test Author",
            date="2024-01-01"
        )
        
        asdl_file = ASDLFile(
            file_info=file_info,
            modules={},
            metadata={
                "design_intent": "test circuit",
                "tool_version": "asdl-compiler-v1.0",
                "simulation_settings": {"temperature": 27, "corners": ["TT", "SS", "FF"]}
            }
        )
        
        assert asdl_file.metadata is not None
        assert asdl_file.metadata["design_intent"] == "test circuit"
        assert asdl_file.metadata["tool_version"] == "asdl-compiler-v1.0"
        assert asdl_file.metadata["simulation_settings"]["temperature"] == 27
        
    def test_file_info_metadata(self):
        """Test metadata field on FileInfo."""
        file_info = FileInfo(
            top_module="test_module",
            doc="Test documentation", 
            revision="1.0",
            author="Test Author",
            date="2024-01-01",
            metadata={
                "project": "analog_designs",
                "technology": "gf180mcu",
                "verification_status": "validated"
            }
        )
        
        assert file_info.metadata is not None
        assert file_info.metadata["project"] == "analog_designs"
        assert file_info.metadata["technology"] == "gf180mcu"
        assert file_info.metadata["verification_status"] == "validated"
        
    def test_device_model_metadata(self):
        """Test metadata field on DeviceModel."""
        device_model = DeviceModel(
            type=PrimitiveType.PDK_DEVICE,
            ports=['D', 'G', 'S', 'B'],
            device_line="MN {D} {G} {S} {B} nfet_03v3 W={W} L={L}",
            doc="NMOS transistor model",
            parameters={'W': '1u', 'L': '0.18u'},
            metadata={
                "pdk_version": "gf180mcu_v1.0.2",
                "model_accuracy": "high",
                "extraction_method": "RCX",
                "layout_constraints": {"min_W": "0.18u", "max_W": "10u"}
            }
        )
        
        assert device_model.metadata is not None
        assert device_model.metadata["pdk_version"] == "gf180mcu_v1.0.2"
        assert device_model.metadata["model_accuracy"] == "high"
        assert device_model.metadata["layout_constraints"]["min_W"] == "0.18u"
        
    def test_port_metadata(self):
        """Test metadata field on Port."""
        port = Port(
            dir=PortDirection.IN,
            type=PortType.SIGNAL,
            metadata={
                "signal_range": {"min": 0.0, "max": 1.8},
                "load_capacitance": "10fF",
                "timing_critical": True,
                "layout_hint": "place_near_center"
            }
        )
        
        assert port.metadata is not None
        assert port.metadata["signal_range"]["max"] == 1.8
        assert port.metadata["load_capacitance"] == "10fF"
        assert port.metadata["timing_critical"] == True
        assert port.metadata["layout_hint"] == "place_near_center"
        
    def test_module_metadata(self):
        """Test metadata field on Module."""
        module = Module(
            doc="Test amplifier module",
            instances={"M1": Instance(model="nmos_unit", mappings={"D": "out"})},  # Make it hierarchical
            metadata={
                "circuit_type": "analog",
                "performance": {
                    "gain": "60dB",
                    "bandwidth": "100MHz", 
                    "power": "1mW"
                },
                "design_constraints": ["low_noise", "high_speed"],
                "verification": {
                    "corners_tested": ["TT", "SS", "FF"],
                    "monte_carlo": True
                }
            }
        )
        
        assert module.metadata is not None
        assert module.metadata["circuit_type"] == "analog"
        assert module.metadata["performance"]["gain"] == "60dB"
        assert module.metadata["design_constraints"] == ["low_noise", "high_speed"]
        assert module.metadata["verification"]["monte_carlo"] == True
        
    def test_instance_metadata_replaces_intent(self):
        """Test that metadata field replaces the old intent field on Instance."""
        instance = Instance(
            model="nmos",
            mappings={'D': 'drain', 'G': 'gate', 'S': 'source'},
            doc="Current mirror input transistor",
            parameters={'W': '2u', 'L': '0.18u'},
            metadata={  # This should replace the old 'intent' field
                "purpose": "current_mirror_input",
                "matching": "critical",
                "layout": {"placement": "symmetric", "routing": "minimize_parasitic"},
                "optimization": {"priority": ["matching", "area"], "constraint": "speed"}
            }
        )
        
        assert instance.metadata is not None
        assert instance.metadata["purpose"] == "current_mirror_input"
        assert instance.metadata["matching"] == "critical"
        assert instance.metadata["layout"]["placement"] == "symmetric"
        assert instance.metadata["optimization"]["priority"] == ["matching", "area"]
        
    def test_metadata_optional_none(self):
        """Test that metadata field is optional and can be None."""
        # Test with minimal required fields only
        device_model = DeviceModel(
            type=PrimitiveType.SPICE_DEVICE,
            ports=['P', 'N'],
            device_line="R{name} {P} {N} {resistance}"
        )
        
        # Metadata should be None when not specified
        assert device_model.metadata is None
        
    def test_metadata_empty_dict(self):
        """Test metadata field with empty dictionary."""
        port = Port(
            dir=PortDirection.OUT,
            type=PortType.SIGNAL,
            metadata={}  # Empty but not None
        )
        
        assert port.metadata == {}
        assert port.metadata is not None
        
    def test_metadata_nested_structures(self):
        """Test metadata with complex nested data structures."""
        complex_metadata = {
            "simulation": {
                "ac_analysis": {
                    "start_freq": "1Hz",
                    "stop_freq": "1GHz",
                    "points_per_decade": 10
                },
                "dc_analysis": {
                    "source": "VDD",
                    "start": "0V",
                    "stop": "1.8V",
                    "step": "0.1V"
                }
            },
            "layout": {
                "placement": ["symmetric", "matched"],
                "routing": {
                    "metal_layers": [1, 2, 3],
                    "via_rules": {"minimize": True, "redundancy": False}
                }
            },
            "validation": {
                "drc_clean": True,
                "lvs_clean": True,
                "extracted": False,
                "corners": ["TT", "SS", "SF", "FS", "FF"]
            }
        }
        
        module = Module(
            doc="Complex analog block",
            instances={"M1": Instance(model="nmos_unit", mappings={"D": "out"})},  # Make it hierarchical
            metadata=complex_metadata
        )
        
        assert module.metadata is not None
        assert module.metadata["simulation"]["ac_analysis"]["start_freq"] == "1Hz"
        assert module.metadata["layout"]["routing"]["metal_layers"] == [1, 2, 3]
        assert module.metadata["validation"]["corners"] == ["TT", "SS", "SF", "FS", "FF"] 