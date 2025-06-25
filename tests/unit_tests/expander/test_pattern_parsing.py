"""
Tests for pattern parsing and validation in ASDL expander.

Tests the core pattern detection, extraction, and validation methods
according to the rules documented in doc/pattern_expansion_rules.md.
"""

import pytest
from src.asdl.expander import PatternExpander


class TestPatternDetection:
    """Test pattern detection methods."""
    
    def setup_method(self):
        """Set up test instance."""
        self.expander = PatternExpander()
    
    def test_has_literal_pattern_simple_cases(self):
        """Test detection of basic literal patterns."""
        # Valid patterns
        assert self.expander._has_literal_pattern("in_<p,n>")
        assert self.expander._has_literal_pattern("clk<,b>")
        assert self.expander._has_literal_pattern("<ab,cd>")
        assert self.expander._has_literal_pattern("signal_<pos,neg>")
        
        # No patterns
        assert not self.expander._has_literal_pattern("simple_name")
        assert not self.expander._has_literal_pattern("no_brackets")
        assert not self.expander._has_literal_pattern("data[3:0]")  # Array pattern, not literal
    
    def test_has_literal_pattern_edge_cases(self):
        """Test pattern detection edge cases."""
        # Incomplete patterns
        assert not self.expander._has_literal_pattern("incomplete<")
        assert not self.expander._has_literal_pattern("incomplete>")
        
        # Single item patterns (detected but will error during validation)
        assert self.expander._has_literal_pattern("no_comma<abc>")
        
        # Multiple angle brackets but no commas
        assert not self.expander._has_literal_pattern("<abc><def>")
        
        # Mixed brackets
        assert not self.expander._has_literal_pattern("mixed<[3:0]>")


class TestPatternExtraction:
    """Test pattern extraction methods."""
    
    def setup_method(self):
        """Set up test instance."""
        self.expander = PatternExpander()
    
    def test_extract_literal_pattern_simple(self):
        """Test extraction of simple patterns."""
        # Basic differential pattern
        items = self.expander._extract_literal_pattern("in_<p,n>")
        assert items == ["p", "n"]
        
        # Empty suffix pattern
        items = self.expander._extract_literal_pattern("clk<,b>")
        assert items == ["", "b"]
        
        # No prefix pattern
        items = self.expander._extract_literal_pattern("<ab,cd>")
        assert items == ["ab", "cd"]
    
    def test_extract_literal_pattern_whitespace(self):
        """Test whitespace handling in pattern extraction."""
        # Whitespace should be removed
        items = self.expander._extract_literal_pattern("sig_< p , n >")
        assert items == ["p", "n"]
        
        # Mixed whitespace
        items = self.expander._extract_literal_pattern("data<  a,b  ,  c >")
        assert items == ["a", "b", "c"]
        
        # Tabs and spaces
        items = self.expander._extract_literal_pattern("net<\tp\t,\tn\t>")
        assert items == ["p", "n"]
    
    def test_extract_literal_pattern_multiple_items(self):
        """Test extraction with more than 2 items."""
        items = self.expander._extract_literal_pattern("tri_<a,b,c>")
        assert items == ["a", "b", "c"]
        
        items = self.expander._extract_literal_pattern("<w,x,y,z>")
        assert items == ["w", "x", "y", "z"]
    
    def test_extract_literal_pattern_no_pattern(self):
        """Test extraction when no pattern exists."""
        # Should return None or empty list for no pattern
        result = self.expander._extract_literal_pattern("no_pattern")
        assert result is None or result == []


class TestPatternValidation:
    """Test pattern validation methods."""
    
    def setup_method(self):
        """Set up test instance."""
        self.expander = PatternExpander()
    
    def test_validate_literal_pattern_valid_cases(self):
        """Test validation of valid patterns."""
        # Valid patterns should not raise exceptions
        self.expander._validate_literal_pattern(["p", "n"])
        self.expander._validate_literal_pattern(["", "b"])  # Empty suffix OK
        self.expander._validate_literal_pattern(["a", "b", "c"])  # Multiple items OK
        self.expander._validate_literal_pattern(["pos", "neg"])  # Longer names OK
    
    def test_validate_literal_pattern_error_cases(self):
        """Test validation error conditions."""
        # Empty pattern
        with pytest.raises(ValueError, match="Pattern cannot be empty"):
            self.expander._validate_literal_pattern([])
        
        # Single item
        with pytest.raises(ValueError, match="Pattern must have at least 2 items"):
            self.expander._validate_literal_pattern(["p"])
        
        # All empty items
        with pytest.raises(ValueError, match="At least one item must be non-empty"):
            self.expander._validate_literal_pattern(["", ""])
            
        with pytest.raises(ValueError, match="At least one item must be non-empty"):
            self.expander._validate_literal_pattern(["", "", ""])


class TestPatternCountValidation:
    """Test pattern count matching validation."""
    
    def setup_method(self):
        """Set up test instance."""
        self.expander = PatternExpander()
    
    def test_validate_pattern_counts_matching(self):
        """Test validation when pattern counts match."""
        # Equal counts should not raise exceptions
        self.expander._validate_pattern_counts(["p", "n"], ["a", "b"])
        self.expander._validate_pattern_counts(["a", "b", "c"], ["x", "y", "z"])
        
        # One side no pattern (None) should be OK
        self.expander._validate_pattern_counts(["p", "n"], None)
        self.expander._validate_pattern_counts(None, ["a", "b"])
    
    def test_validate_pattern_counts_mismatched(self):
        """Test validation when pattern counts don't match."""
        # Mismatched counts should raise exception
        with pytest.raises(ValueError, match="Pattern item counts must match"):
            self.expander._validate_pattern_counts(["p", "n"], ["a", "b", "c"])
        
        with pytest.raises(ValueError, match="Pattern item counts must match"):
            self.expander._validate_pattern_counts(["a", "b", "c"], ["x", "y"])


class TestPatternExpansionBasics:
    """Test basic pattern expansion functionality."""
    
    def setup_method(self):
        """Set up test instance."""
        self.expander = PatternExpander()
    
    def test_expand_literal_pattern_simple(self):
        """Test simple literal pattern expansion."""
        # Basic differential pattern
        result = self.expander._expand_literal_pattern("in_<p,n>")
        assert result == ["in_p", "in_n"]
        
        # Empty suffix pattern
        result = self.expander._expand_literal_pattern("clk<,b>")
        assert result == ["clk", "clkb"]
        
        # No prefix pattern
        result = self.expander._expand_literal_pattern("<ab,cd>")
        assert result == ["ab", "cd"]
    
    def test_expand_literal_pattern_multiple_items(self):
        """Test expansion with multiple items."""
        result = self.expander._expand_literal_pattern("data_<a,b,c>")
        assert result == ["data_a", "data_b", "data_c"]
        
        result = self.expander._expand_literal_pattern("<w,x,y,z>")
        assert result == ["w", "x", "y", "z"]
    
    def test_expand_literal_pattern_no_pattern(self):
        """Test expansion when no pattern exists."""
        # Should return original name
        result = self.expander._expand_literal_pattern("no_pattern")
        assert result == ["no_pattern"]


class TestIntegratedPatternParsing:
    """Test integrated pattern parsing workflow."""
    
    def setup_method(self):
        """Set up test instance."""
        self.expander = PatternExpander()
    
    def test_full_pattern_processing_valid(self):
        """Test complete pattern processing workflow for valid patterns."""
        test_cases = [
            ("in_<p,n>", ["in_p", "in_n"]),
            ("clk<,b>", ["clk", "clkb"]),
            ("<ab,cd>", ["ab", "cd"]),
            ("tri_<a,b,c>", ["tri_a", "tri_b", "tri_c"]),
            ("no_pattern", ["no_pattern"]),
        ]
        
        for input_name, expected in test_cases:
            result = self.expander._expand_literal_pattern(input_name)
            assert result == expected, f"Failed for input: {input_name}"
    
    def test_full_pattern_processing_errors(self):
        """Test complete pattern processing workflow for error cases."""
        error_cases = [
            "signal_<>",      # Empty pattern
            "port_<p>",       # Single item
            "net_<,>",        # All empty
            "bad_<,,,>",      # All empty multiple
        ]
        
        for error_case in error_cases:
            with pytest.raises(ValueError):
                self.expander._expand_literal_pattern(error_case) 