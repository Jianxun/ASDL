"""
Data structures for diagnostics (errors, warnings, etc.).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .data_structures import Locatable

class DiagnosticSeverity(Enum):
    """Severity level of a diagnostic message."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"

@dataclass
class Diagnostic:
    """
    Represents a single diagnostic message.
    """
    message: str
    severity: DiagnosticSeverity
    location: Optional[Locatable] = None

    def __str__(self) -> str:
        """Provides a user-friendly string representation."""
        location = ""
        if self.location:
            location += f" at {self.location}"
        
        return f"[{self.severity.name}]{location}: {self.message}" 