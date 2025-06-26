"""
Tests for parser error handling and diagnostic generation.
"""

import pytest
from pathlib import Path
import sys

# Add src to path for testing
test_dir = Path(__file__).parent
project_root = test_dir.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from asdl.parser import ASDLParser
from asdl.diagnostics import DiagnosticSeverity

class TestParserErrorHandling:
    """Test that the parser generates diagnostics for syntax/structure errors."""

    def test_toplevel_is_not_a_dictionary(self):
        """
        Test that a diagnostic is generated if the top-level YAML
        is not a dictionary.
        """
        yaml_content = "- a list, not a dictionary"
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)

        assert asdl_file is None
        assert len(parser.diagnostics) == 1
        diagnostic = parser.diagnostics[0]
        assert diagnostic.severity == DiagnosticSeverity.ERROR
        assert "Top-level content must be a YAML dictionary" in diagnostic.message
        assert diagnostic.location.start_line == 1
        assert diagnostic.location.start_col == 1

    def test_yaml_syntax_error(self):
        """Test that a diagnostic is generated for malformed YAML."""
        # This YAML has an invalid indentation for a mapping
        yaml_content = """
file_info:
  top_module: test
 bad_indent: here
"""
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)

        assert asdl_file is None
        assert len(parser.diagnostics) == 1
        diagnostic = parser.diagnostics[0]
        assert diagnostic.severity == DiagnosticSeverity.ERROR
        assert "YAML syntax error" in diagnostic.message
        assert diagnostic.location.start_line == 4
        assert diagnostic.location.start_col == 2 