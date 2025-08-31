"""
ASDL - Analog Structured Description Language

A Python library for parsing ASDL YAML files and generating SPICE netlists.
"""

from .data_structures import (
    ASDLFile,
    FileInfo, 
    Module,
    Port,
    PortDirection,
    PortType,
    Instance
)

from .parser import ASDLParser
from .elaborator import Elaborator
from .generator import SPICEGenerator
from .validator import ASDLValidator

__version__ = "0.1.0"
__all__ = [
    # Data structures
    "ASDLFile",
    "FileInfo",
    "Module",
    "Port",
    "PortDirection", 
    "PortType",
    "Instance",
    # Processing pipeline
    "ASDLParser",
    "Elaborator",
    "SPICEGenerator",
    "ASDLValidator"
] 