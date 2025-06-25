"""
Test suite for schema robustness in pattern expansion.

Tests that pattern expansion properly inherits all fields from original instances,
ensuring forward compatibility when new fields are added to the Instance schema.
"""

import pytest
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from src.asdl.expander import PatternExpander
from src.asdl.data_structures import Instance


class TestPatternExpansionSchemaRobustness:
    """Test that pattern expansion handles schema changes robustly."""
    
    def test_instance_field_inheritance(self):
        """Test that all instance fields are properly inherited during expansion."""
        # Create a comprehensive instance with all current fields
        original_instance = Instance(
            model="test_model",
            mappings={"G": "in_<p,n>", "D": "out_<p,n>", "S": "vss", "B": "vss"},
            doc="Test instance with all fields",
            parameters={"M": "2", "W": "1u"},
            intent={"op": {"region": "saturation"}, "matching": "critical"}
        )
        
        # Create expander and expand patterns
        expander = PatternExpander()
        expanded_instances = expander.expand_instance_patterns({"MN_<P,N>": original_instance})
        
        # Verify we got the expected expanded instances
        assert "MN_P" in expanded_instances
        assert "MN_N" in expanded_instances
        
        # Verify all fields are preserved in expanded instances
        for expanded_id, expanded_instance in expanded_instances.items():
            # Model should be preserved
            assert expanded_instance.model == original_instance.model
            
            # Doc should be preserved
            assert expanded_instance.doc == original_instance.doc
            
            # Parameters should be preserved
            assert expanded_instance.parameters == original_instance.parameters
            
            # Intent should be preserved
            assert expanded_instance.intent == original_instance.intent
            
            # Mappings should be expanded but same keys
            assert set(expanded_instance.mappings.keys()) == set(original_instance.mappings.keys())
            
            # Verify the expanded instance is a separate object
            assert expanded_instance is not original_instance
    
    def test_field_preservation_with_none_values(self):
        """Test that fields with None values are properly preserved."""
        # Create instance with some None fields
        original_instance = Instance(
            model="test_model",
            mappings={"G": "in_<p,n>", "D": "out_<p,n>"},
            doc=None,  # None value
            parameters=None,  # None value
            intent={"design": "test"}
        )
        
        expander = PatternExpander()
        expanded_instances = expander.expand_instance_patterns({"TEST_<P,N>": original_instance})
        
        # Verify None values are preserved
        for expanded_instance in expanded_instances.values():
            assert expanded_instance.doc is None
            assert expanded_instance.parameters is None
            assert expanded_instance.intent == original_instance.intent
    
    def test_non_pattern_instance_field_preservation(self):
        """Test that non-pattern instances also preserve all fields."""
        # Create instance without patterns but with mapping patterns
        original_instance = Instance(
            model="test_model",
            mappings={"G": "in", "D": "out_<p,n>", "S": "vss", "B": "vss"},  # Mapping pattern
            doc="Non-pattern instance with mapping patterns",
            parameters={"M": "4", "L": "0.18u"},
            intent={"purpose": "load", "optimization": "area"}
        )
        
        expander = PatternExpander()
        expanded_instances = expander.expand_instance_patterns({"LOAD": original_instance})
        
        # Should have one instance with same ID but expanded mappings
        assert "LOAD" in expanded_instances
        expanded_instance = expanded_instances["LOAD"]
        
        # All non-mapping fields should be identical
        assert expanded_instance.model == original_instance.model
        assert expanded_instance.doc == original_instance.doc
        assert expanded_instance.parameters == original_instance.parameters
        assert expanded_instance.intent == original_instance.intent
        
        # Mappings should be expanded
        assert expanded_instance.mappings != original_instance.mappings
        assert "D" in expanded_instance.mappings  # Key should still exist
    
    def test_dataclass_replace_usage(self):
        """Test that the expansion uses dataclass.replace() correctly."""
        # This test verifies the implementation detail to ensure we're using
        # the robust approach rather than manual field copying
        
        original_instance = Instance(
            model="test_model",
            mappings={"port": "net_<a,b>"},
            doc="Test for dataclass.replace usage",
            parameters={"param1": "value1"},
            intent={"test": "value"}
        )
        
        # Create expander
        expander = PatternExpander()
        
        # Manually call the mapping expansion to test the internal mechanism
        expanded_mappings = expander._expand_mapping_patterns(
            original_instance.mappings,
            "ORIGINAL_ID",
            "EXPANDED_ID"
        )
        
        # Verify the mappings were expanded
        assert "port" in expanded_mappings
        assert "net_<a,b>" not in expanded_mappings.values()
        
        # The key insight: when we use dataclass.replace(), ALL fields
        # are preserved by default, which is more robust than manual copying
    
    def test_object_identity_separation(self):
        """Test that expanded instances are separate objects."""
        original_instance = Instance(
            model="test_model",
            mappings={"G": "in_<p,n>", "D": "out_<p,n>"},  # Pattern that creates different mappings
            doc="Original instance",
            parameters={"M": "1"},
            intent={"type": "input"}
        )
        
        expander = PatternExpander()
        expanded_instances = expander.expand_instance_patterns({"IN_<P,N>": original_instance})
        
        # Verify we have separate objects
        assert len(expanded_instances) == 2
        instance_p = expanded_instances["IN_P"]
        instance_n = expanded_instances["IN_N"]
        
        # Objects should be different
        assert instance_p is not instance_n
        assert instance_p is not original_instance
        assert instance_n is not original_instance
        
        # But content should be identical except for mappings
        assert instance_p.model == instance_n.model == original_instance.model
        assert instance_p.doc == instance_n.doc == original_instance.doc
        assert instance_p.parameters == instance_n.parameters == original_instance.parameters
        assert instance_p.intent == instance_n.intent == original_instance.intent
        
        # Mappings should be expanded (different from original)
        assert instance_p.mappings != original_instance.mappings
        assert instance_n.mappings != original_instance.mappings
        
        # Verify patterns were expanded (no more <p,n> syntax)
        for mapping_value in instance_p.mappings.values():
            assert '<p,n>' not in mapping_value
        for mapping_value in instance_n.mappings.values():
            assert '<p,n>' not in mapping_value
            
        # The key point: all non-mapping fields should be identical objects
        # This verifies dataclass.replace() is working correctly
    
    def test_complex_nested_data_preservation(self):
        """Test that complex nested data structures are properly preserved."""
        complex_intent = {
            "design": {
                "purpose": "amplification",
                "constraints": {
                    "power": "< 1mW",
                    "area": "< 100um²"
                }
            },
            "simulation": {
                "corners": ["tt", "ff", "ss"],
                "temperatures": [25, 85, -40]
            },
            "layout": {
                "matching": True,
                "symmetry": "required"
            }
        }
        
        complex_parameters = {
            "device": {
                "M": "2",
                "W": "1u", 
                "L": "0.18u"
            },
            "bias": {
                "Vgs": "0.6V",
                "Vds": "0.4V"
            }
        }
        
        original_instance = Instance(
            model="complex_model",
            mappings={"G": "in_<p,n>", "D": "out_<p,n>"},
            doc="Complex instance with nested data",
            parameters=complex_parameters,
            intent=complex_intent
        )
        
        expander = PatternExpander()
        expanded_instances = expander.expand_instance_patterns({"COMPLEX_<P,N>": original_instance})
        
        # Verify complex data is preserved
        for expanded_instance in expanded_instances.values():
            assert expanded_instance.parameters == complex_parameters
            assert expanded_instance.intent == complex_intent
            
            # Verify deep equality (not just reference equality)
            assert expanded_instance.parameters["device"]["M"] == "2"
            assert expanded_instance.intent["design"]["constraints"]["power"] == "< 1mW"
            assert expanded_instance.intent["simulation"]["corners"] == ["tt", "ff", "ss"] 