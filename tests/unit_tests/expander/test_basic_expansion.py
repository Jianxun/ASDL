"""
Tests for basic literal expansion integration with ASDL structures.

Tests the integration of literal pattern expansion with ports, mappings,
and basic ASDL data structures.
"""

import pytest
from src.asdl.expander import PatternExpander
from src.asdl.data_structures import Port, PortDirection, SignalType, Instance, PortConstraints


class TestPortPatternExpansion:
    """Test pattern expansion in port contexts."""
    
    def setup_method(self):
        """Set up test instance."""
        self.expander = PatternExpander()
    
    def test_expand_port_patterns_differential(self):
        """Test expansion of differential port patterns."""
        # Create test ports with patterns
        ports = {
            "in_<p,n>": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE, constraints=None),
            "out_<pos,neg>": Port(dir=PortDirection.OUT, type=SignalType.VOLTAGE, constraints=None),
            "normal_port": Port(dir=PortDirection.IN, type=SignalType.DIGITAL, constraints=None)
        }
        
        # Expand patterns
        expanded = self.expander.expand_port_patterns(ports)
        
        # Check results
        expected_names = {
            "in_p", "in_n", 
            "out_pos", "out_neg",
            "normal_port"
        }
        assert set(expanded.keys()) == expected_names
        
        # Verify port objects are preserved
        assert expanded["in_p"].dir == PortDirection.IN_OUT
        assert expanded["in_n"].dir == PortDirection.IN_OUT
        assert expanded["out_pos"].dir == PortDirection.OUT
        assert expanded["normal_port"].dir == PortDirection.IN
    
    def test_expand_port_patterns_empty_suffix(self):
        """Test expansion with empty suffix patterns."""
        ports = {
            "clk<,b>": Port(dir=PortDirection.IN, type=SignalType.DIGITAL, constraints=None),
            "reset<,n>": Port(dir=PortDirection.IN, type=SignalType.DIGITAL, constraints=None)
        }
        
        expanded = self.expander.expand_port_patterns(ports)
        
        expected_names = {"clk", "clkb", "reset", "resetn"}
        assert set(expanded.keys()) == expected_names
    
    def test_expand_port_patterns_no_prefix(self):
        """Test expansion with no-prefix patterns."""
        ports = {
            "<vdd,vss>": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE, constraints=None),
            "<power,ground>": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE, constraints=None)
        }
        
        expanded = self.expander.expand_port_patterns(ports)
        
        expected_names = {"vdd", "vss", "power", "ground"}
        assert set(expanded.keys()) == expected_names
    
    def test_expand_port_patterns_multiple_items(self):
        """Test expansion with more than 2 items."""
        ports = {
            "phase_<a,b,c>": Port(dir=PortDirection.OUT, type=SignalType.VOLTAGE, constraints=None),
            "ctrl_<en,sel0,sel1>": Port(dir=PortDirection.IN, type=SignalType.DIGITAL, constraints=None)
        }
        
        expanded = self.expander.expand_port_patterns(ports)
        
        expected_names = {
            "phase_a", "phase_b", "phase_c",
            "ctrl_en", "ctrl_sel0", "ctrl_sel1"
        }
        assert set(expanded.keys()) == expected_names
    
    def test_expand_port_patterns_error_cases(self):
        """Test error handling in port pattern expansion."""
        # Invalid patterns should raise exceptions
        error_cases = [
            {"bad_<>": Port(dir=PortDirection.IN, type=SignalType.DIGITAL, constraints=None)},
            {"invalid_<p>": Port(dir=PortDirection.IN, type=SignalType.DIGITAL, constraints=None)},
            {"empty_<,>": Port(dir=PortDirection.IN, type=SignalType.DIGITAL, constraints=None)}
        ]
        
        for ports in error_cases:
            with pytest.raises(ValueError):
                self.expander.expand_port_patterns(ports)


class TestMappingPatternExpansion:
    """Test pattern expansion in mapping contexts."""
    
    def setup_method(self):
        """Set up test instance."""
        self.expander = PatternExpander()
    
    def test_expand_mapping_patterns_order_sensitive(self):
        """Test order-sensitive mapping pattern expansion."""
        mappings = {
            "port_<p,n>": "net_<n,p>",  # Cross-connected
            "data_<a,b,c>": "bus_<c,b,a>",  # Reversed order
            "normal": "regular_net"
        }
        
        expanded = self.expander._expand_mapping_patterns(
            mappings, "test_instance", "test_instance"
        )
        
        expected = {
            "port_p": "net_n",
            "port_n": "net_p", 
            "data_a": "bus_c",
            "data_b": "bus_b",
            "data_c": "bus_a",
            "normal": "regular_net"
        }
        assert expanded == expected
    
    def test_expand_mapping_patterns_one_sided_port(self):
        """Test one-sided pattern expansion (port side only)."""
        mappings = {
            "data_<p,n>": "single_net",
            "ctrl_<en,sel>": "control_line"
        }
        
        expanded = self.expander._expand_mapping_patterns(
            mappings, "test_instance", "test_instance"
        )
        
        expected = {
            "data_p": "single_net",
            "data_n": "single_net",
            "ctrl_en": "control_line", 
            "ctrl_sel": "control_line"
        }
        assert expanded == expected
    
    def test_expand_mapping_patterns_one_sided_net(self):
        """Test one-sided pattern expansion (net side only)."""
        mappings = {
            "single_port": "net_<a,b>",
            "another_port": "bus_<x,y,z>"
        }
        
        # This should be treated as connecting one port to the first net
        # (This might be changed based on requirements - could be an error)
        expanded = self.expander._expand_mapping_patterns(
            mappings, "test_instance", "test_instance"
        )
        
        # For now, map to first expanded net
        expected = {
            "single_port": "net_a",
            "another_port": "bus_x"
        }
        assert expanded == expected
    
    def test_expand_mapping_patterns_mismatched_counts(self):
        """Test error handling for mismatched pattern counts."""
        mappings = {
            "port_<p,n>": "net_<a,b,c>"  # 2 vs 3 items
        }
        
        with pytest.raises(ValueError, match="Pattern item counts must match"):
            self.expander._expand_mapping_patterns(
                mappings, "test_instance", "test_instance"
            )


class TestBasicExpansionIntegration:
    """Test integration of basic expansion with ASDL structures."""
    
    def setup_method(self):
        """Set up test instance."""
        self.expander = PatternExpander()
    
    def test_mixed_patterns_and_normal_names(self):
        """Test handling mixed pattern and normal names."""
        ports = {
            "diff_<p,n>": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE, constraints=None),
            "normal_in": Port(dir=PortDirection.IN, type=SignalType.DIGITAL, constraints=None),
            "clk<,b>": Port(dir=PortDirection.IN, type=SignalType.DIGITAL, constraints=None),
            "normal_out": Port(dir=PortDirection.OUT, type=SignalType.VOLTAGE, constraints=None)
        }
        
        expanded = self.expander.expand_port_patterns(ports)
        
        expected_names = {
            "diff_p", "diff_n", 
            "normal_in", 
            "clk", "clkb",
            "normal_out"
        }
        assert set(expanded.keys()) == expected_names
    
    def test_whitespace_handling_in_patterns(self):
        """Test that whitespace is properly handled in real contexts."""
        ports = {
            "signal_< p , n >": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE, constraints=None),
            "data_<  a,  b,  c  >": Port(dir=PortDirection.OUT, type=SignalType.DIGITAL, constraints=None)
        }
        
        expanded = self.expander.expand_port_patterns(ports)
        
        expected_names = {
            "signal_p", "signal_n",
            "data_a", "data_b", "data_c"
        }
        assert set(expanded.keys()) == expected_names
    
    def test_preserve_port_properties(self):
        """Test that port properties are preserved during expansion."""
        original_port = Port(
            dir=PortDirection.IN_OUT, 
            type=SignalType.VOLTAGE,
            constraints=PortConstraints({"voltage": "1.8V", "drive": "high"})
        )
        
        ports = {"test_<p,n>": original_port}
        expanded = self.expander.expand_port_patterns(ports)
        
        # Both expanded ports should have same properties
        assert expanded["test_p"].dir == PortDirection.IN_OUT
        assert expanded["test_n"].dir == PortDirection.IN_OUT
        assert expanded["test_p"].constraints.constraints == {"voltage": "1.8V", "drive": "high"}
        assert expanded["test_n"].constraints.constraints == {"voltage": "1.8V", "drive": "high"}
    
    def test_empty_port_collection(self):
        """Test handling of empty port collections."""
        ports = {}
        expanded = self.expander.expand_port_patterns(ports)
        assert expanded == {}
    
    def test_no_patterns_passthrough(self):
        """Test that ports without patterns pass through unchanged."""
        ports = {
            "input_a": Port(dir=PortDirection.IN, type=SignalType.DIGITAL, constraints=None),
            "output_b": Port(dir=PortDirection.OUT, type=SignalType.VOLTAGE, constraints=None),
            "inout_c": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE, constraints=None)
        }
        
        expanded = self.expander.expand_port_patterns(ports)
        
        # Should be identical to input
        assert expanded == ports
        assert set(expanded.keys()) == {"input_a", "output_b", "inout_c"} 