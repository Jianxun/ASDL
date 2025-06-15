"""
Test basic ASDL parser functionality.

Tests the core parsing capabilities including:
- YAML string parsing
- File parsing
- Basic validation
- ASDLFile structure creation
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys

# Add src to path for testing
test_dir = Path(__file__).parent
project_root = test_dir.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from asdl.parser import ASDLParser
from asdl.data_structures import ASDLFile, FileInfo
import yaml


class TestBasicParsing:
    """Test basic parsing functionality."""
    
    def test_parser_initialization_default(self):
        """Test parser initialization with default settings."""
        parser = ASDLParser()
        assert parser.strict_mode is False
        assert parser.preserve_unknown is True
        assert parser._warnings == []
    
    def test_parser_initialization_custom(self):
        """Test parser initialization with custom settings."""
        parser = ASDLParser(strict_mode=True, preserve_unknown=False)
        assert parser.strict_mode is True
        assert parser.preserve_unknown is False
        assert parser._warnings == []
    
    def test_parse_minimal_valid_yaml_string(self):
        """Test parsing a minimal valid ASDL YAML string."""
        yaml_content = """
file_info:
  top_module: "test_module"
  doc: "Test documentation"
  revision: "v1.0"
  author: "Test Author"
  date: "2024-01-01"

models: {}

modules: {}
"""
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)
        
        # Verify ASDLFile structure
        assert isinstance(asdl_file, ASDLFile)
        assert isinstance(asdl_file.file_info, FileInfo)
        assert asdl_file.file_info.top_module == "test_module"
        assert asdl_file.file_info.doc == "Test documentation"
        assert asdl_file.file_info.revision == "v1.0"
        assert asdl_file.file_info.author == "Test Author"
        assert asdl_file.file_info.date == "2024-01-01"
        assert asdl_file.models == {}
        assert asdl_file.modules == {}
    
    def test_parse_file_success(self):
        """Test parsing a valid ASDL file from disk."""
        yaml_content = """
file_info:
  top_module: "file_test"
  doc: "Test file parsing"
  revision: "v1.0"
  author: "Test Author"
  date: "2024-01-01"

models: {}

modules: {}
"""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as tmp_file:
            tmp_file.write(yaml_content)
            tmp_file_path = tmp_file.name
        
        try:
            parser = ASDLParser()
            asdl_file = parser.parse_file(tmp_file_path)
            
            assert isinstance(asdl_file, ASDLFile)
            assert asdl_file.file_info.top_module == "file_test"
            assert asdl_file.file_info.doc == "Test file parsing"
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
    
    def test_parse_file_not_found(self):
        """Test parsing a non-existent file raises FileNotFoundError."""
        parser = ASDLParser()
        
        with pytest.raises(FileNotFoundError, match="ASDL file not found"):
            parser.parse_file("non_existent_file.yml")
    
    def test_parse_invalid_yaml_syntax(self):
        """Test parsing invalid YAML syntax raises YAMLError."""
        invalid_yaml = """
file_info:
  top_module: "test"
  invalid yaml syntax: [unclosed bracket
"""
        parser = ASDLParser()
        
        with pytest.raises(yaml.YAMLError, match="Failed to parse YAML"):
            parser.parse_string(invalid_yaml)
    
    def test_parse_non_dictionary_root(self):
        """Test parsing YAML that's not a dictionary raises ValueError."""
        non_dict_yaml = """
- item1
- item2
- item3
"""
        parser = ASDLParser()
        
        with pytest.raises(ValueError, match="ASDL file must contain a YAML dictionary"):
            parser.parse_string(non_dict_yaml)
    
    def test_parse_empty_yaml(self):
        """Test parsing empty YAML raises ValueError."""
        parser = ASDLParser()
        
        with pytest.raises(ValueError, match="ASDL file must contain a YAML dictionary"):
            parser.parse_string("")
    
    def test_warnings_collection(self):
        """Test that warnings are collected during parsing."""
        yaml_content = """
file_info:
  top_module: "test"
  doc: "Test"
  revision: "v1.0"
  author: "Test Author"
  date: "2024-01-01"
  unknown_field: "should generate warning"

models: {}

modules: {}
"""
        parser = ASDLParser(strict_mode=False)
        
        # Should capture warnings but not raise errors
        with pytest.warns(UserWarning, match="Unknown fields in file_info"):
            asdl_file = parser.parse_string(yaml_content)
        
        assert isinstance(asdl_file, ASDLFile)
        assert asdl_file.file_info.top_module == "test"
    
    def test_strict_mode_unknown_fields(self):
        """Test that strict mode raises errors for unknown fields."""
        yaml_content = """
file_info:
  top_module: "test"
  doc: "Test"
  revision: "v1.0"
  author: "Test Author"
  date: "2024-01-01"
  unknown_field: "should raise error"

models: {}

modules: {}
"""
        parser = ASDLParser(strict_mode=True)
        
        with pytest.raises(ValueError, match="Unknown fields in file_info"):
            parser.parse_string(yaml_content) 