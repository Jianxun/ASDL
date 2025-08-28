"""
Core types and interfaces for validator rules.
"""

from typing import List, Protocol

from ...data_structures import ASDLFile, Module
from ...diagnostics import Diagnostic


class ValidationContext:
    """Shared context for validation rules operating on an ASDL file."""

    def __init__(self, asdl_file: ASDLFile) -> None:
        self.asdl_file = asdl_file


class ModuleRule(Protocol):
    def validate(self, ctx: ValidationContext, module_name: str, module: Module) -> List[Diagnostic]:
        ...


class FileRule(Protocol):
    def validate_file(self, ctx: ValidationContext) -> List[Diagnostic]:
        ...


