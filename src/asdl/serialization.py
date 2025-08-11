"""
Serialization and I/O module for ASDL data structures.

This module handles all conversion and file I/O operations, keeping the core 
data structures pure and focused on representing data.
"""

import json
import yaml
from dataclasses import asdict
from typing import Dict, Any
from enum import Enum
from pathlib import Path

from .data_structures import ASDLFile


def asdl_to_dict(asdl_file: ASDLFile) -> Dict[str, Any]:
    """
    Convert ASDLFile to a dictionary with proper serialization of enums and objects.
    
    Args:
        asdl_file: The ASDLFile instance to serialize
        
    Returns:
        Dictionary representation suitable for YAML/JSON serialization
    """
    def convert_value(obj):
        """Recursively convert objects to serializable format."""
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, Path):
            return str(obj)
        elif hasattr(obj, '__dict__'):
            return {k: convert_value(v) for k, v in obj.__dict__.items()}
        elif isinstance(obj, dict):
            return {k: convert_value(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple, set)):
            return [convert_value(item) for item in obj]
        else:
            return obj
    
    # Convert the dataclass to dict
    data_dict = asdict(asdl_file)
    
    # Apply custom serialization
    result = convert_value(data_dict)
    
    # Use 'file_info' key (v0.4 format) for consistency
    return {
        'file_info': result['file_info'],
        'models': result['models'],
        'modules': result['modules']
    }


def asdl_to_yaml_string(asdl_file: ASDLFile) -> str:
    """
    Convert ASDLFile to YAML string (round-trip).
    
    Note: Round-trip is only guaranteed for original ASDLFile instances
    (before pattern expansion and parameter resolution).
    
    Args:
        asdl_file: The ASDLFile instance to serialize
        
    Returns:
        YAML string representation of the ASDLFile
    """
    data = asdl_to_dict(asdl_file)
    return yaml.dump(data, default_flow_style=False, sort_keys=False)


def asdl_to_json_string(asdl_file: ASDLFile) -> str:
    """
    Convert ASDLFile to JSON string for debugging.
    
    Args:
        asdl_file: The ASDLFile instance to serialize
        
    Returns:
        JSON string representation for debugging purposes
    """
    data = asdl_to_dict(asdl_file)
    return json.dumps(data, indent=2, ensure_ascii=False)


def save_asdl_to_yaml_file(asdl_file: ASDLFile, filepath: str) -> None:
    """
    Save ASDLFile to YAML file (round-trip).
    
    Args:
        asdl_file: The ASDLFile instance to save
        filepath: Path to save the YAML file to
    """
    yaml_content = asdl_to_yaml_string(asdl_file)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(yaml_content)


def save_asdl_to_json_file(asdl_file: ASDLFile, filepath: str) -> None:
    """
    Save ASDLFile as JSON file for debugging.
    
    Args:
        asdl_file: The ASDLFile instance to save
        filepath: Path to save the JSON file to
    """
    json_content = asdl_to_json_string(asdl_file)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(json_content) 