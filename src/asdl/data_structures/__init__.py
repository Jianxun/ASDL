"""
ASDL Data Structures Package

This package contains the core data structures and schema generation for ASDL.
Organizes related functionality:
- structures.py: Core data structures (ASDLFile, Module, Instance, etc.)
- schema_gen.py: JSON Schema and text schema generation from data structures
"""

# Import all data structures for easy access
from .structures import (
    # Core container
    ASDLFile,
    
    # Metadata and location
    FileInfo,
    Locatable,
    Metadata,
    
    
    # Module system  
    Module,
    
    # Port system
    Port,
    PortDirection,
    SignalType,
    PortConstraints,
    
    # Instance system
    Instance,
    
)

# Import schema generation
from .schema_gen import (
    build_json_schema,
    render_text_schema,
)

__all__ = [
    # Core container
    "ASDLFile",
    
    # Metadata and location  
    "FileInfo",
    "Locatable", 
    "Metadata",
    
    
    # Module system
    "Module",
    
    # Port system
    "Port",
    "PortDirection",
    "SignalType", 
    "PortConstraints",
    
    # Instance system
    "Instance",
    
    
    # Schema generation
    "build_json_schema",
    "render_text_schema",
]