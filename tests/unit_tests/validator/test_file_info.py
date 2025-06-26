"""
Test FileInfo parsing functionality.

Tests the file_info section parsing including:
- Required and optional field handling
- Backward compatibility with legacy design_info
- Field validation and defaults
- Unknown field handling
"""

import pytest
from pathlib import Path
import sys

# Add src to path for testing
test_dir = Path(__file__).parent
project_root = test_dir.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from asdl.parser import ASDLParser
from asdl.data_structures import ASDLFile, FileInfo


class TestFileInfoParsing:
    """Test FileInfo section parsing."""
    
    def test_parse_complete_file_info(self):
        """Test parsing file_info with all fields present."""
        yaml_content = """
file_info:
  top_module: "complete_test"
  doc: "Complete documentation"
  revision: "v2.1.0"
  author: "Test Developer"
  date: "2024-01-15"

models: {}
modules: {}
"""
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)
        
        file_info = asdl_file.file_info
        assert isinstance(file_info, FileInfo)
        assert file_info.top_module == "complete_test"
        assert file_info.doc == "Complete documentation"
        assert file_info.revision == "v2.1.0"
        assert file_info.author == "Test Developer"
        assert file_info.date == "2024-01-15"
    
    def test_parse_minimal_file_info(self):
        """Test parsing file_info with minimal required fields."""
        yaml_content = """
file_info:
  top_module: "minimal_test"

models: {}
modules: {}
"""
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)
        
        file_info = asdl_file.file_info
        assert file_info.top_module == "minimal_test"
        # Check that optional fields get default empty values
        assert file_info.doc == ""
        assert file_info.revision == ""
        assert file_info.author == ""
        assert file_info.date == ""
    
    def test_parse_legacy_design_info(self):
        """Test backward compatibility with legacy design_info field."""
        yaml_content = """
design_info:
  top_module: "legacy_test"
  doc: "Legacy format"
  revision: "v1.0"
  author: "Legacy Developer"
  date: "2023-12-01"

models: {}
modules: {}
"""
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)
        
        file_info = asdl_file.file_info
        assert file_info.top_module == "legacy_test"
        assert file_info.doc == "Legacy format"
        assert file_info.revision == "v1.0"
        assert file_info.author == "Legacy Developer"
        assert file_info.date == "2023-12-01"
    
    def test_file_info_takes_precedence_over_design_info(self):
        """Test that file_info takes precedence when both are present."""
        yaml_content = """
file_info:
  top_module: "new_format"
  doc: "New format doc"
  revision: "v2.0"
  author: "New Developer"
  date: "2024-01-01"

design_info:
  top_module: "old_format"
  doc: "Old format doc"
  revision: "v1.0"
  author: "Old Developer"
  date: "2023-01-01"

models: {}
modules: {}
"""
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)
        
        file_info = asdl_file.file_info
        # Should use file_info values, not design_info
        assert file_info.top_module == "new_format"
        assert file_info.doc == "New format doc"
        assert file_info.revision == "v2.0"
        assert file_info.author == "New Developer"
        assert file_info.date == "2024-01-01"
    
    def test_missing_file_info_section(self):
        """Test handling when neither file_info nor design_info is present."""
        yaml_content = """
models: {}
modules: {}
"""
        parser = ASDLParser()
        asdl_file = parser.parse_string(yaml_content)
        
        file_info = asdl_file.file_info
        # Should get defaults for all fields
        assert file_info.top_module == ""
        assert file_info.doc == ""
        assert file_info.revision == ""
        assert file_info.author == ""
        assert file_info.date == ""
    
    def test_file_info_not_dictionary(self):
        """Test error handling when file_info is not a dictionary."""
        yaml_content = """
file_info: "not a dictionary"

models: {}
modules: {}
"""
        parser = ASDLParser()
        
        with pytest.raises(ValueError, match="file_info/design_info must be a dictionary"):
            parser.parse_string(yaml_content)
    
    def test_design_info_not_dictionary(self):
        """Test error handling when design_info is not a dictionary."""
        yaml_content = """
design_info: ["not", "a", "dictionary"]

models: {}
modules: {}
"""
        parser = ASDLParser()
        
        with pytest.raises(ValueError, match="file_info/design_info must be a dictionary"):
            parser.parse_string(yaml_content)
    
    def test_file_info_unknown_fields_lenient(self):
        """Test unknown fields handling in lenient mode."""
        yaml_content = """
file_info:
  top_module: "test"
  doc: "Test doc"
  revision: "v1.0"
  author: "Test Author"
  date: "2024-01-01"
  # Unknown fields
  license: "MIT"
  version: "1.0"
  tags: ["analog", "test"]

models: {}
modules: {}
"""
        parser = ASDLParser(strict_mode=False)
        
        with pytest.warns(UserWarning, match="Unknown fields in file_info"):
            asdl_file = parser.parse_string(yaml_content)
        
        # Should still parse successfully
        file_info = asdl_file.file_info
        assert file_info.top_module == "test"
        assert file_info.doc == "Test doc"
    
    def test_file_info_unknown_fields_strict(self):
        """Test unknown fields handling in strict mode."""
        yaml_content = """
file_info:
  top_module: "test"
  doc: "Test doc"
  revision: "v1.0"
  author: "Test Author"
  date: "2024-01-01"
  unknown_field: "should cause error"

models: {}
modules: {}
"""
        parser = ASDLParser(strict_mode=True)
        
        with pytest.raises(ValueError, match="Unknown fields in file_info"):
            parser.parse_string(yaml_content)
    
    def test_partial_field_combinations(self):
        """Test various combinations of partial field presence."""
        test_cases = [
            # Only top_module
            {"top_module": "test1"},
            # top_module + doc
            {"top_module": "test2", "doc": "Test documentation"},
            # top_module + revision + author
            {"top_module": "test3", "revision": "v1.0", "author": "Test Author"},
            # All except date
            {"top_module": "test4", "doc": "Doc", "revision": "v1.0", "author": "Author"},
        ]
        
        parser = ASDLParser()
        
        for i, fields in enumerate(test_cases):
            yaml_content = f"""
file_info:
{chr(10).join(f"  {k}: {repr(v)}" for k, v in fields.items())}

models: {{}}
modules: {{}}
"""
            asdl_file = parser.parse_string(yaml_content)
            file_info = asdl_file.file_info
            
            # Check that specified fields are set
            for field_name, expected_value in fields.items():
                assert getattr(file_info, field_name) == expected_value, f"Case {i}: {field_name}"
            
            # Check that unspecified fields get defaults
            all_fields = {"top_module", "doc", "revision", "author", "date"}
            unspecified_fields = all_fields - set(fields.keys())
            for field_name in unspecified_fields:
                assert getattr(file_info, field_name) == "", f"Case {i}: {field_name} should be empty" 