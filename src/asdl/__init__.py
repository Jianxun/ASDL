"""
ASDL - Analog Structured Description Language

A Python library for parsing ASDL YAML files and generating SPICE netlists.
"""

from .data_structures import (
    ASDLFile,
    FileInfo, 
    DeviceModel,
    DeviceType,
    Module,
    Port,
    PortDirection,
    SignalType,
    PortConstraints,
    Nets,
    Instance
)

from .parser import ASDLParser
from .expander import PatternExpander  
from .resolver import ParameterResolver
from .generator import SPICEGenerator

__version__ = "0.1.0"
__all__ = [
    # Data structures
    "ASDLFile",
    "FileInfo",
    "DeviceModel", 
    "DeviceType",
    "Module",
    "Port",
    "PortDirection", 
    "SignalType",
    "PortConstraints",
    "Nets",
    "Instance",
    # Processing pipeline
    "ASDLParser",
    "PatternExpander",
    "ParameterResolver", 
    "SPICEGenerator"
] 