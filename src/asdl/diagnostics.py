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
    code: str
    title: str
    details: str
    severity: DiagnosticSeverity
    location: Optional[Locatable] = None
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        """Provides a user-friendly string representation."""
        location = ""
        if self.location:
            location += f" at {self.location}"
        
        suggestion_text = f"\nSuggestion: {self.suggestion}" if self.suggestion else ""
        return f"[{self.severity.name} {self.code}]{location}: {self.title}\n{self.details}{suggestion_text}" 