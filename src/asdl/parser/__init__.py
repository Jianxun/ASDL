"""
ASDL Parser package - modular architecture with preserved API.

Maintains exact same public interface as the monolithic parser
while providing internal modular architecture for maintainability.
"""

from .asdl_parser import ASDLParser

# Maintain exact same public interface
__all__ = ['ASDLParser']