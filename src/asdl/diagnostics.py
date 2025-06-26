"""
Data structures for diagnostic reporting in the ASDL toolchain.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class DiagnosticLevel(Enum):
    """Defines the severity level of a diagnostic message."""
    ERROR = "error"
    WARNING = "warning"


@dataclass
class Diagnostic:
    """
    Represents a single diagnostic message (error or warning).

    This structure is used by all analysis stages (expander, validator)
    to report findings in a standardized way.
    """
    level: DiagnosticLevel
    message: str
    module_name: Optional[str] = None
    instance_name: Optional[str] = None
    # Future enhancement: Add line/column numbers for precise error location
    # line: Optional[int] = None
    # column: Optional[int] = None

    def __str__(self) -> str:
        """Provides a user-friendly string representation."""
        location = ""
        if self.module_name:
            location += f" in module '{self.module_name}'"
        if self.instance_name:
            location += f" in instance '{self.instance_name}'"
        
        return f"[{self.level.name}]{location}: {self.message}" 