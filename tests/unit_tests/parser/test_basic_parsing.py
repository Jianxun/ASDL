"""
Test the refactored ASDL parser.

Focuses on pure parsing logic without validation.
"""

import pytest
from pathlib import Path
import sys
import tempfile
import os
from ruamel.yaml import YAMLError

# Add src to path for testing
test_dir = Path(__file__).parent
project_root = test_dir.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from asdl.parser import ASDLParser
from asdl.data_structures import ASDLFile, FileInfo


class TestBasicParsing:
    """Test basic parsing functionality of the refactored parser."""

    def test_parse_minimal_valid_yaml(self):
        """Test that the parser can create a basic ASDLFile object from a valid YAML string."""
        yaml_content = """file_info:
  top_module: "test_module"
modules: {}
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)

        assert isinstance(asdl_file, ASDLFile)
        assert isinstance(asdl_file.file_info, FileInfo)
        assert asdl_file.file_info.top_module == "test_module"
        assert asdl_file.file_info.doc is None
        assert asdl_file.file_info.revision is None
        assert asdl_file.file_info.author is None
        assert asdl_file.file_info.date is None

        # Check for location data
        assert asdl_file.file_info.start_line == 1
        assert asdl_file.file_info.start_col == 1
        assert asdl_file.file_info.end_line == 1
        assert asdl_file.file_info.end_col == 10
        assert asdl_file.file_info.file_path is None # Should be None when parsing from string

        assert asdl_file.modules == {}

    def test_parse_file_success(self):
        """Test parsing a valid ASDL file from disk."""
        yaml_content = """
file_info:
  top_module: "file_test"
  doc: "Test file parsing"
modules: {}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as tmp_file:
            tmp_file.write(yaml_content)
            tmp_file_path = tmp_file.name
        
        try:
            parser = ASDLParser()
            asdl_file, diagnostics = parser.parse_file(tmp_file_path)
            
            assert not diagnostics
            assert asdl_file is not None
            assert asdl_file.file_info.top_module == "file_test"
            assert asdl_file.file_info.doc == "Test file parsing"
            
            # Check for file path in location data
            assert asdl_file.file_info.file_path == Path(tmp_file_path)
            
        finally:
            os.unlink(tmp_file_path)

    def test_parse_file_not_found(self):
        """Test parsing a non-existent file raises FileNotFoundError."""
        parser = ASDLParser()
        with pytest.raises(FileNotFoundError, match="ASDL file not found"):
            parser.parse_file("non_existent_file.yml")

    def test_parse_invalid_yaml_syntax(self):
        """Test parsing invalid YAML syntax returns a diagnostic."""
        invalid_yaml = "key: [unclosed bracket"
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(invalid_yaml)
        assert asdl_file is None
        assert len(diagnostics) == 1
        assert diagnostics[0].code == "P100"

    def test_parse_non_dictionary_root(self):
        """Test parsing YAML that's not a dictionary returns a diagnostic."""
        non_dict_yaml = "- item1\\n- item2"
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(non_dict_yaml)
        assert asdl_file is None
        assert len(diagnostics) == 1
        assert diagnostics[0].code == "P101"

    def test_parse_empty_yaml(self):
        """Test parsing empty YAML returns no file and no diagnostics."""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string("")
        assert asdl_file is None
        assert not diagnostics 