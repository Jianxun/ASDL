"""
Test cases for the internal_nets field.

This tests the new internal_nets field that replaces the Nets class in the data structure refactor.
The internal_nets field provides a direct, simple way to declare internal nets on Module.
"""

import pytest
from src.asdl.data_structures import Module, Port, PortDirection, SignalType


class TestInternalNetsField:
    """Test cases for internal_nets field replacing Nets class."""
    
    def test_module_with_internal_nets_list(self):
        """Test Module with internal_nets as a list of strings."""
        module = Module(
            doc="Test module with internal nets",
            internal_nets=["bias_voltage", "internal_node", "temp_signal"]
        )
        
        assert module.internal_nets is not None
        assert isinstance(module.internal_nets, list)
        assert len(module.internal_nets) == 3
        assert "bias_voltage" in module.internal_nets
        assert "internal_node" in module.internal_nets
        assert "temp_signal" in module.internal_nets
        
    def test_module_without_internal_nets(self):
        """Test Module without internal_nets (should be None)."""
        module = Module(
            doc="Simple module without internal nets"
        )
        
        assert module.internal_nets is None
        
    def test_module_with_empty_internal_nets(self):
        """Test Module with empty internal_nets list."""
        module = Module(
            doc="Module with empty internal nets",
            internal_nets=[]
        )
        
        assert module.internal_nets == []
        assert module.internal_nets is not None
        assert len(module.internal_nets) == 0
        
    def test_module_with_ports_and_internal_nets(self):
        """Test Module with both ports and internal_nets."""
        ports = {
            "in_p": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
            "in_n": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
            "out": Port(dir=PortDirection.OUT, type=SignalType.VOLTAGE)
        }
        
        module = Module(
            doc="Differential amplifier",
            ports=ports,
            internal_nets=["bias_current", "intermediate_node", "compensation"]
        )
        
        # Check ports exist
        assert module.ports is not None
        assert len(module.ports) == 3
        assert "in_p" in module.ports
        assert "out" in module.ports
        
        # Check internal nets exist
        assert module.internal_nets is not None
        assert len(module.internal_nets) == 3
        assert "bias_current" in module.internal_nets
        assert "intermediate_node" in module.internal_nets
        assert "compensation" in module.internal_nets
        
    def test_internal_nets_preserves_order(self):
        """Test that internal_nets preserves the order of declaration."""
        ordered_nets = ["first_net", "second_net", "third_net", "fourth_net"]
        
        module = Module(
            doc="Module with ordered internal nets",
            internal_nets=ordered_nets
        )
        
        assert module.internal_nets is not None
        assert module.internal_nets == ordered_nets
        assert module.internal_nets[0] == "first_net"
        assert module.internal_nets[1] == "second_net"
        assert module.internal_nets[2] == "third_net"
        assert module.internal_nets[3] == "fourth_net"
        
    def test_internal_nets_with_descriptive_names(self):
        """Test internal_nets with descriptive, realistic net names."""
        realistic_nets = [
            "vbias_p",
            "vbias_n", 
            "tail_current",
            "diff_out_p",
            "diff_out_n",
            "cmfb_voltage",
            "compensation_node"
        ]
        
        module = Module(
            doc="Operational amplifier with realistic internal nets",
            internal_nets=realistic_nets
        )
        
        assert module.internal_nets is not None
        assert len(module.internal_nets) == 7
        
        # Check some specific nets
        assert "vbias_p" in module.internal_nets
        assert "tail_current" in module.internal_nets
        assert "cmfb_voltage" in module.internal_nets
        assert "compensation_node" in module.internal_nets
        
    def test_internal_nets_string_type_validation(self):
        """Test that internal_nets contains only strings."""
        module = Module(
            doc="Test module",
            internal_nets=["net1", "net2", "net3"]
        )
        assert module.internal_nets is not None
        # All elements should be strings
        assert all(isinstance(net, str) for net in module.internal_nets)
        
    def test_internal_nets_with_pattern_names(self):
        """Test internal_nets with pattern-like names (for future expansion)."""
        pattern_nets = [
            "bias_<p,n>",  # Could be expanded to bias_p, bias_n
            "internal_<0,1,2>",  # Could be expanded to internal_0, internal_1, internal_2
            "temp_node"  # Regular net name
        ]
        
        module = Module(
            doc="Module with pattern-like internal net names",
            internal_nets=pattern_nets
        )
        
        assert module.internal_nets is not None
        assert len(module.internal_nets) == 3
        assert "bias_<p,n>" in module.internal_nets
        assert "internal_<0,1,2>" in module.internal_nets
        assert "temp_node" in module.internal_nets
        
    def test_internal_nets_integration_with_metadata(self):
        """Test internal_nets works together with metadata field."""
        module = Module(
            doc="Complex module with internal nets and metadata",
            internal_nets=["bias_voltage", "internal_node"],
            metadata={
                "circuit_type": "analog",
                "net_count": 2,
                "verification_status": "validated"
            }
        )
        
        # Both internal_nets and metadata should work
        assert module.internal_nets is not None
        assert len(module.internal_nets) == 2
        assert module.metadata is not None
        assert module.metadata["circuit_type"] == "analog"
        assert module.metadata["net_count"] == 2 