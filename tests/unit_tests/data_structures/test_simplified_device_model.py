"""
Test cases for the simplified DeviceModel structure.

This tests the new simplified DeviceModel that removes legacy fields and uses PrimitiveType.
The new DeviceModel focuses on the device_line approach with parameters.
"""

import pytest
from src.asdl.data_structures import PrimitiveType, DeviceModel


class TestSimplifiedDeviceModel:
    """Test cases for the simplified DeviceModel structure."""
    
    def test_minimal_device_model_creation(self):
        """Test creating a minimal DeviceModel with required fields only."""
        model = DeviceModel(
            type=PrimitiveType.PDK_DEVICE,
            ports=['D', 'G', 'S', 'B'],
            device_line="MN {D} {G} {S} {B} nch W={W} L={L}"
        )
        
        assert model.type == PrimitiveType.PDK_DEVICE
        assert model.ports == ['D', 'G', 'S', 'B']
        assert model.device_line == "MN {D} {G} {S} {B} nch W={W} L={L}"
        assert model.doc is None
        assert model.parameters is None
        
    def test_full_device_model_creation(self):
        """Test creating a DeviceModel with all fields populated."""
        model = DeviceModel(
            type=PrimitiveType.SPICE_DEVICE,
            ports=['A', 'K'],
            device_line="D{name} {A} {K} ideal_diode",
            doc="Ideal diode model for circuit simulation",
            parameters={'Is': '1e-14', 'n': '1.0'}
        )
        
        assert model.type == PrimitiveType.SPICE_DEVICE
        assert model.ports == ['A', 'K']
        assert model.device_line == "D{name} {A} {K} ideal_diode"
        assert model.doc == "Ideal diode model for circuit simulation"
        assert model.parameters == {'Is': '1e-14', 'n': '1.0'}
        
    def test_pdk_device_example(self):
        """Test creating a realistic PDK device model."""
        nmos_model = DeviceModel(
            type=PrimitiveType.PDK_DEVICE,
            ports=['D', 'G', 'S', 'B'],
            device_line="MN {D} {G} {S} {B} nfet_03v3 W={W} L={L} M={M}",
            doc="NMOS transistor from GF180MCU PDK",
            parameters={'W': '1u', 'L': '0.18u', 'M': '1'}
        )
        
        assert nmos_model.type == PrimitiveType.PDK_DEVICE
        assert 'nfet_03v3' in nmos_model.device_line
        assert nmos_model.parameters is not None
        assert nmos_model.parameters['W'] == '1u'
        
    def test_spice_device_example(self):
        """Test creating a built-in SPICE device model."""
        vsource_model = DeviceModel(
            type=PrimitiveType.SPICE_DEVICE,
            ports=['P', 'N'],
            device_line="V{name} {P} {N} DC {voltage}",
            doc="DC voltage source",
            parameters={'voltage': '1.8'}
        )
        
        assert vsource_model.type == PrimitiveType.SPICE_DEVICE
        assert 'DC' in vsource_model.device_line
        assert vsource_model.parameters['voltage'] == '1.8'
        
    def test_device_line_placeholder_formats(self):
        """Test various device_line placeholder formats."""
        # Standard parameter placeholders
        model1 = DeviceModel(
            type=PrimitiveType.PDK_DEVICE,
            ports=['D', 'G', 'S'],
            device_line="MN {D} {G} {S} nmos W={W} L={L}"
        )
        assert '{W}' in model1.device_line
        assert '{L}' in model1.device_line
        
        # Port placeholders
        assert '{D}' in model1.device_line
        assert '{G}' in model1.device_line
        assert '{S}' in model1.device_line
        
    def test_ports_ordering_preservation(self):
        """Test that port ordering is preserved in the ports list."""
        model = DeviceModel(
            type=PrimitiveType.PDK_DEVICE,
            ports=['G', 'D', 'S', 'B'],  # Different from typical D,G,S,B order
            device_line="MN {G} {D} {S} {B} nmos"
        )
        
        # Order should be preserved as specified
        assert model.ports == ['G', 'D', 'S', 'B']
        assert model.ports[0] == 'G'
        assert model.ports[1] == 'D'
        
    def test_parameters_string_values(self):
        """Test that parameters use string values for consistency."""
        model = DeviceModel(
            type=PrimitiveType.PDK_DEVICE,
            ports=['D', 'G', 'S'],
            device_line="MN {D} {G} {S} nmos",
            parameters={'W': '1u', 'L': '0.18u', 'M': '1'}  # All string values
        )
        
        # All parameter values should be strings
        for value in model.parameters.values():
            assert isinstance(value, str)
            
    def test_empty_parameters_dict(self):
        """Test DeviceModel with empty parameters dictionary."""
        model = DeviceModel(
            type=PrimitiveType.SPICE_DEVICE,
            ports=['P', 'N'],
            device_line="R{name} {P} {N} {resistance}",
            parameters={}  # Empty but not None
        )
        
        assert model.parameters == {}
        assert model.parameters is not None 