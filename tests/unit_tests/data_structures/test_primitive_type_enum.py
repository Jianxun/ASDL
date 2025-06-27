"""
Test cases for the new PrimitiveType enum.

This tests the new PrimitiveType enum that replaces DeviceType in the data structure refactor.
PrimitiveType provides a clearer classification based on the origin of the primitive.
"""

import pytest
from src.asdl.data_structures import PrimitiveType


class TestPrimitiveType:
    """Test cases for PrimitiveType enum."""
    
    def test_pdk_device_value(self):
        """Test PDK_DEVICE enum value."""
        assert PrimitiveType.PDK_DEVICE.value == "pdk_device"
        
    def test_spice_device_value(self):
        """Test SPICE_DEVICE enum value."""
        assert PrimitiveType.SPICE_DEVICE.value == "spice_device"
        
    def test_enum_members_count(self):
        """Test that enum has exactly 2 members."""
        assert len(list(PrimitiveType)) == 2
        
    def test_enum_member_names(self):
        """Test enum member names."""
        expected_names = {'PDK_DEVICE', 'SPICE_DEVICE'}
        actual_names = {member.name for member in PrimitiveType}
        assert actual_names == expected_names
        
    def test_enum_member_values(self):
        """Test enum member values."""
        expected_values = {'pdk_device', 'spice_device'}
        actual_values = {member.value for member in PrimitiveType}
        assert actual_values == expected_values
        
    def test_string_representation(self):
        """Test string representation of enum members."""
        assert str(PrimitiveType.PDK_DEVICE) == "PrimitiveType.PDK_DEVICE"
        assert str(PrimitiveType.SPICE_DEVICE) == "PrimitiveType.SPICE_DEVICE"
        
    def test_enum_equality(self):
        """Test enum equality comparison."""
        assert PrimitiveType.PDK_DEVICE == PrimitiveType.PDK_DEVICE
        assert PrimitiveType.SPICE_DEVICE == PrimitiveType.SPICE_DEVICE
        assert PrimitiveType.PDK_DEVICE != PrimitiveType.SPICE_DEVICE
        
    def test_enum_hashing(self):
        """Test that enum members are hashable and can be used in sets/dicts."""
        enum_set = {PrimitiveType.PDK_DEVICE, PrimitiveType.SPICE_DEVICE}
        assert len(enum_set) == 2
        
        enum_dict = {
            PrimitiveType.PDK_DEVICE: "External PDK device",
            PrimitiveType.SPICE_DEVICE: "Built-in SPICE primitive"
        }
        assert len(enum_dict) == 2
        assert enum_dict[PrimitiveType.PDK_DEVICE] == "External PDK device" 