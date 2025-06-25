"""
Tests for instance pattern expansion in ASDL expander.

Tests the expansion of instance names and their synchronized mappings,
ensuring each expanded instance gets separate instantiation blocks.
"""

import pytest
from src.asdl.expander import PatternExpander
from src.asdl.data_structures import Instance


class TestInstanceNameExpansion:
    """Test expansion of instance name patterns."""
    
    def setup_method(self):
        """Set up test instance."""
        self.expander = PatternExpander()
    
    def test_expand_instance_patterns_differential(self):
        """Test expansion of differential instance patterns."""
        instances = {
            "M_<P,N>": Instance(
                model="nmos_unit",
                mappings={"G": "gate", "D": "drain", "S": "source", "B": "bulk"},
                parameters={"W": "1u", "L": "0.1u"}
            ),
            "regular_instance": Instance(
                model="capacitor",
                mappings={"p": "net1", "n": "net2"}
            )
        }
        
        expanded = self.expander.expand_instance_patterns(instances)
        
        # Should have separate instances for P and N
        expected_names = {"M_P", "M_N", "regular_instance"}
        assert set(expanded.keys()) == expected_names
        
        # Verify instance properties are preserved
        assert expanded["M_P"].model == "nmos_unit"
        assert expanded["M_N"].model == "nmos_unit"
        assert expanded["M_P"].parameters == {"W": "1u", "L": "0.1u"}
        assert expanded["M_N"].parameters == {"W": "1u", "L": "0.1u"}
        assert expanded["regular_instance"].model == "capacitor"
    
    def test_expand_instance_patterns_multiple_items(self):
        """Test expansion with more than 2 items in instance names."""
        instances = {
            "amp_<a,b,c>": Instance(
                model="amplifier",
                mappings={"in": "input", "out": "output"},
                parameters={"gain": "10"}
            )
        }
        
        expanded = self.expander.expand_instance_patterns(instances)
        
        expected_names = {"amp_a", "amp_b", "amp_c"}
        assert set(expanded.keys()) == expected_names
        
        # All should have same model and parameters
        for name in expected_names:
            assert expanded[name].model == "amplifier"
            assert expanded[name].parameters == {"gain": "10"}
    
    def test_expand_instance_patterns_empty_suffix(self):
        """Test instance expansion with empty suffix patterns."""
        instances = {
            "clk_gen<,_backup>": Instance(
                model="clock_generator",
                mappings={"out": "clk_signal"}
            )
        }
        
        expanded = self.expander.expand_instance_patterns(instances)
        
        expected_names = {"clk_gen", "clk_gen_backup"}
        assert set(expanded.keys()) == expected_names


class TestSynchronizedInstanceMappingExpansion:
    """Test synchronized expansion of instance names with their mappings."""
    
    def setup_method(self):
        """Set up test instance."""
        self.expander = PatternExpander()
    
    def test_synchronized_instance_and_port_patterns(self):
        """Test synchronized expansion of instance names and port mappings."""
        instances = {
            "M_<P,N>": Instance(
                model="nmos_unit",
                mappings={
                    "G<P,N>": "gate_<p,n>",      # Synchronized patterns
                    "D<P,N>": "drain_<p,n>",     # Synchronized patterns  
                    "S": "source_common",        # No pattern - maps to same net
                    "B<P,N>": "bulk"             # One-sided pattern
                }
            )
        }
        
        expanded = self.expander.expand_instance_patterns(instances)
        
        # Should create separate instances
        assert "M_P" in expanded
        assert "M_N" in expanded
        
        # Check M_P mappings
        expected_p_mappings = {
            "GP": "gate_p",
            "DP": "drain_p", 
            "S": "source_common",
            "BP": "bulk"
        }
        assert expanded["M_P"].mappings == expected_p_mappings
        
        # Check M_N mappings  
        expected_n_mappings = {
            "GN": "gate_n",
            "DN": "drain_n",
            "S": "source_common", 
            "BN": "bulk"
        }
        assert expanded["M_N"].mappings == expected_n_mappings
    
    def test_cross_connected_synchronized_patterns(self):
        """Test cross-connected synchronized pattern expansion."""
        instances = {
            "diff_pair_<p,n>": Instance(
                model="nmos_unit",
                mappings={
                    "G<p,n>": "input_<n,p>",    # Cross-connected
                    "D<p,n>": "output_<p,n>",   # Same order
                    "S": "common_source"
                }
            )
        }
        
        expanded = self.expander.expand_instance_patterns(instances)
        
        # Check cross-connected mappings
        expected_p_mappings = {
            "Gp": "input_n",      # Cross-connected: p maps to n
            "Dp": "output_p",     # Same order: p maps to p  
            "S": "common_source"
        }
        assert expanded["diff_pair_p"].mappings == expected_p_mappings
        
        expected_n_mappings = {
            "Gn": "input_p",      # Cross-connected: n maps to p
            "Dn": "output_n",     # Same order: n maps to n
            "S": "common_source"
        }
        assert expanded["diff_pair_n"].mappings == expected_n_mappings
    
    def test_mismatched_instance_and_port_patterns(self):
        """Test error handling for mismatched instance and port patterns."""
        instances = {
            "M_<P,N>": Instance(   # 2 items
                model="nmos_unit", 
                mappings={
                    "G<a,b,c>": "gate_<x,y,z>"  # 3 items - should error
                }
            )
        }
        
        # This should raise an error because instance pattern doesn't match port pattern
        with pytest.raises(ValueError):
            self.expander.expand_instance_patterns(instances)


class TestInstanceExpansionEdgeCases:
    """Test edge cases and error conditions in instance expansion."""
    
    def setup_method(self):
        """Set up test instance."""
        self.expander = PatternExpander()
    
    def test_instance_patterns_with_intent_preservation(self):
        """Test that instance intent metadata is preserved during expansion."""
        instances = {
            "current_mirror_<p,n>": Instance(
                model="nmos_unit",
                mappings={"G": "bias", "D": "out_<p,n>", "S": "gnd"},
                parameters={"W": "2u"},
                intent={"purpose": "current_mirror", "matching": "critical"}
            )
        }
        
        expanded = self.expander.expand_instance_patterns(instances)
        
        # Intent should be preserved for both instances
        assert expanded["current_mirror_p"].intent == {"purpose": "current_mirror", "matching": "critical"}
        assert expanded["current_mirror_n"].intent == {"purpose": "current_mirror", "matching": "critical"}
    
    def test_no_instance_patterns_passthrough(self):
        """Test that instances without patterns pass through unchanged."""
        instances = {
            "simple_instance": Instance(
                model="resistor",
                mappings={"a": "net1", "b": "net2"},
                parameters={"R": "1k"}
            ),
            "another_instance": Instance(
                model="capacitor", 
                mappings={"p": "vdd", "n": "gnd"}
            )
        }
        
        expanded = self.expander.expand_instance_patterns(instances)
        
        # Should be identical to input
        assert expanded == instances
    
    def test_empty_instance_collection(self):
        """Test handling of empty instance collections."""
        instances = {}
        expanded = self.expander.expand_instance_patterns(instances)
        assert expanded == {}
    
    def test_instance_pattern_validation_errors(self):
        """Test that invalid instance patterns raise appropriate errors."""
        error_cases = [
            # Empty pattern
            {
                "bad_<>": Instance(model="test", mappings={})
            },
            # Single item pattern  
            {
                "invalid_<p>": Instance(model="test", mappings={})
            },
            # All empty items
            {
                "empty_<,>": Instance(model="test", mappings={})
            }
        ]
        
        for instances in error_cases:
            with pytest.raises(ValueError):
                self.expander.expand_instance_patterns(instances)


class TestComplexInstanceExpansion:
    """Test complex scenarios with instance expansion."""
    
    def setup_method(self):
        """Set up test instance."""
        self.expander = PatternExpander()
    
    def test_mixed_instance_patterns_and_normal_instances(self):
        """Test handling of mixed pattern and normal instance names."""
        instances = {
            "diff_<p,n>": Instance(
                model="nmos_unit",
                mappings={"G": "gate_<p,n>", "D": "drain", "S": "source"}
            ),
            "load_resistor": Instance(
                model="resistor", 
                mappings={"a": "vdd", "b": "drain"}
            ),
            "array_<a,b,c>": Instance(
                model="capacitor",
                mappings={"p": "net_<a,b,c>", "n": "gnd"}
            )
        }
        
        expanded = self.expander.expand_instance_patterns(instances)
        
        expected_names = {
            "diff_p", "diff_n", 
            "load_resistor",
            "array_a", "array_b", "array_c"
        }
        assert set(expanded.keys()) == expected_names
        
        # Verify normal instance is unchanged
        assert expanded["load_resistor"] == instances["load_resistor"]
    
    def test_instance_expansion_separate_instantiations(self):
        """Test that expanded instances create truly separate instantiation blocks."""
        instances = {
            "test_<x,y>": Instance(
                model="test_model",
                mappings={"port_<x,y>": "net_<a,b>"},
                parameters={"param": "value"}
            )
        }
        
        expanded = self.expander.expand_instance_patterns(instances)
        
        # Should have separate instances
        assert "test_x" in expanded
        assert "test_y" in expanded
        
        # Instances should be separate objects (not same reference)
        assert expanded["test_x"] is not expanded["test_y"]
        
        # But should have same content structure
        assert expanded["test_x"].model == expanded["test_y"].model == "test_model"
        assert expanded["test_x"].parameters == expanded["test_y"].parameters == {"param": "value"}
        
        # Mappings should be properly expanded and different
        assert expanded["test_x"].mappings == {"port_x": "net_a"}
        assert expanded["test_y"].mappings == {"port_y": "net_b"}
    
    def test_instance_expansion_with_complex_mappings(self):
        """Test instance expansion with various mapping pattern combinations."""
        instances = {
            "complex_<p,n>": Instance(
                model="complex_device",
                mappings={
                    "same_<p,n>": "net_<p,n>",        # Same order
                    "cross_<p,n>": "signal_<n,p>",    # Cross order
                    "one_sided_<p,n>": "common_net",  # One-sided port
                    "other_side": "bus_<a,b>",        # One-sided net
                    "no_pattern": "static_net"        # No patterns
                }
            )
        }
        
        expanded = self.expander.expand_instance_patterns(instances)
        
        # Check complex mapping expansion for _p instance
        expected_p_mappings = {
            "same_p": "net_p",
            "cross_p": "signal_n", 
            "one_sided_p": "common_net",
            "other_side": "bus_a",
            "no_pattern": "static_net"
        }
        assert expanded["complex_p"].mappings == expected_p_mappings
        
                # Check complex mapping expansion for _n instance
        expected_n_mappings = {
            "same_n": "net_n",
            "cross_n": "signal_p",
            "one_sided_n": "common_net",
            "other_side": "bus_b",  # Second instance should map to second element
            "no_pattern": "static_net"
        }
        assert expanded["complex_n"].mappings == expected_n_mappings 


class TestRealWorldDifferentialPair:
    """Test real-world differential pair patterns using the diff_pair_nmos fixture."""
    
    def setup_method(self):
        """Set up test environment."""
        self.expander = PatternExpander()
        
    def test_differential_pair_fixture_pattern_expansion(self):
        """Test pattern expansion using the real diff_pair_nmos.yml fixture."""
        from pathlib import Path
        from src.asdl.parser import ASDLParser
        
        # Load the real differential pair fixture
        fixtures_dir = Path(__file__).parent.parent.parent / "fixtures"
        diff_pair_path = fixtures_dir / "diff_pair_nmos.yml"
        
        parser = ASDLParser()
        asdl_file = parser.parse_file(str(diff_pair_path))
        
        # Expand patterns
        expanded_file = self.expander.expand_patterns(asdl_file)
        
        # Get the expanded differential pair module
        diff_pair_module = expanded_file.modules['diff_pair_nmos']
        
        # Verify port expansion: in_<p,n> → in_p, in_n
        expected_ports = ['in_p', 'in_n', 'out_p', 'out_n', 'vdd', 'vss', 'iref', 'tail']
        assert diff_pair_module.ports is not None
        actual_ports = list(diff_pair_module.ports.keys())
        assert set(actual_ports) == set(expected_ports)
        
        # Critical test: Verify MN_<P,N> instance expansion
        # This is the exact pattern that was broken!
        assert diff_pair_module.instances is not None
        assert 'MN_P' in diff_pair_module.instances
        assert 'MN_N' in diff_pair_module.instances
        
        # Verify correct differential pair mappings
        mn_p_mappings = diff_pair_module.instances['MN_P'].mappings
        mn_n_mappings = diff_pair_module.instances['MN_N'].mappings
        
        # The bug: both instances were getting same gate connection
        # Correct behavior: MN_P → in_p, MN_N → in_n
        assert mn_p_mappings['G'] == 'in_p', f"MN_P gate should connect to in_p, got {mn_p_mappings['G']}"
        assert mn_n_mappings['G'] == 'in_n', f"MN_N gate should connect to in_n, got {mn_n_mappings['G']}"
        
        # Verify drain connections: MN_P → out_p, MN_N → out_n  
        assert mn_p_mappings['D'] == 'out_p', f"MN_P drain should connect to out_p, got {mn_p_mappings['D']}"
        assert mn_n_mappings['D'] == 'out_n', f"MN_N drain should connect to out_n, got {mn_n_mappings['D']}"
        
        # Verify shared connections (no patterns)
        assert mn_p_mappings['S'] == 'tail'
        assert mn_n_mappings['S'] == 'tail'
        assert mn_p_mappings['B'] == 'vss'
        assert mn_n_mappings['B'] == 'vss'
        
    def test_differential_pair_resistor_loads(self):
        """Test resistor load pattern expansion in differential pair."""
        from pathlib import Path
        from src.asdl.parser import ASDLParser
        
        # Load the real differential pair fixture
        fixtures_dir = Path(__file__).parent.parent.parent / "fixtures"
        diff_pair_path = fixtures_dir / "diff_pair_nmos.yml"
        
        parser = ASDLParser()
        asdl_file = parser.parse_file(str(diff_pair_path))
        
        # Expand patterns
        expanded_file = self.expander.expand_patterns(asdl_file)
        diff_pair_module = expanded_file.modules['diff_pair_nmos']
        
        # Verify resistor load instances: RL_<P,N> → RL_P, RL_N
        assert diff_pair_module.instances is not None
        assert 'RL_P' in diff_pair_module.instances
        assert 'RL_N' in diff_pair_module.instances
        
        # Verify resistor load mappings
        rl_p_mappings = diff_pair_module.instances['RL_P'].mappings
        rl_n_mappings = diff_pair_module.instances['RL_N'].mappings
        
        # Test one-sided net pattern: minus: out_<p,n>
        assert rl_p_mappings['minus'] == 'out_p'
        assert rl_n_mappings['minus'] == 'out_n'
        
        # Shared connection (no pattern)
        assert rl_p_mappings['plus'] == 'vdd'
        assert rl_n_mappings['plus'] == 'vdd'
        
    def test_differential_pair_full_netlist_generation(self):
        """End-to-end test: Parse → Expand → Generate SPICE for differential pair."""
        from pathlib import Path
        from src.asdl.parser import ASDLParser
        from src.asdl.generator import SPICEGenerator
        
        # Load the real differential pair fixture
        fixtures_dir = Path(__file__).parent.parent.parent / "fixtures"
        diff_pair_path = fixtures_dir / "diff_pair_nmos.yml"
        
        parser = ASDLParser()
        asdl_file = parser.parse_file(str(diff_pair_path))
        
        # Expand patterns
        expanded_file = self.expander.expand_patterns(asdl_file)
        
        # Generate SPICE
        generator = SPICEGenerator()
        spice_output = generator.generate(expanded_file)
        
        # Verify critical differential pair connections in SPICE
        # Should have separate gate connections for P and N transistors
        assert 'X_MN_P in_p out_p tail vss nmos_unit' in spice_output
        assert 'X_MN_N in_n out_n tail vss nmos_unit' in spice_output
        
        # Verify we don't have the bug (both connected to same input)
        assert 'X_MN_N in_p out_p tail vss nmos_unit' not in spice_output
        
        # Verify resistor loads
        assert 'X_RL_P vdd out_p resistor_unit' in spice_output
        assert 'X_RL_N vdd out_n resistor_unit' in spice_output 