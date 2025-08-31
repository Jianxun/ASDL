"""
Generator package for SPICE netlist generation.

Provides the public `SPICEGenerator` API and generator-specific diagnostics.
"""

from .spice_generator import SPICEGenerator
from .diagnostics import GENERATOR_DIAGNOSTICS, create_generator_diagnostic

__all__ = [
    "SPICEGenerator",
    "GENERATOR_DIAGNOSTICS",
    "create_generator_diagnostic",
]


