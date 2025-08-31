"""
ASDL Elaborator Package

This package handles the elaboration phase of ASDL compilation, transforming
parsed ASDL structures into fully specified designs through:

- Pattern expansion (literal <> and bus [] patterns)
- Variable resolution (future implementation)
- Diagnostic collection and reporting

The package is organized into focused modules:
- elaborator.py: Main Elaborator class and orchestration
- pattern_expander.py: Pattern expansion logic for literals and buses  
- variable_resolver.py: Variable resolution logic (future implementation)
"""

from .elaborator import Elaborator

__all__ = ['Elaborator']