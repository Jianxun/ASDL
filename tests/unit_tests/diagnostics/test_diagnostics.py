"""
Tests for the diagnostic data structures.
"""

import pytest
from pathlib import Path
import sys

# Add src to path for testing
test_dir = Path(__file__).parent
project_root = test_dir.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from asdl.diagnostics import Diagnostic, DiagnosticSeverity
from asdl.data_structures import Locatable

class TestDiagnostics:
    """Tests for the Diagnostic data structures."""

    def test_diagnostic_creation(self):
        """Test basic creation of a Diagnostic message."""
        loc = Locatable(start_line=10, start_col=5)
        d = Diagnostic(
            code="E001",
            title="Test Error",
            details="This is a test error message.",
            severity=DiagnosticSeverity.ERROR,
            location=loc
        )

        assert d.code == "E001"
        assert d.title == "Test Error"
        assert d.details == "This is a test error message."
        assert d.severity == DiagnosticSeverity.ERROR
        assert d.location == loc

    def test_diagnostic_str_with_location(self):
        """Test the string representation of a diagnostic with a location."""
        loc = Locatable(start_line=10, start_col=5)
        d = Diagnostic(
            code="W001",
            title="Test Warning",
            details="This is a test warning.",
            severity=DiagnosticSeverity.WARNING,
            location=loc
        )
        expected_str = f"[WARNING W001] at {loc}: Test Warning\nThis is a test warning."
        assert str(d) == expected_str

    def test_diagnostic_str_without_location(self):
        """Test the string representation of a diagnostic without a location."""
        d = Diagnostic(
            code="I001",
            title="Test Info",
            details="This is an info message.",
            severity=DiagnosticSeverity.INFO
        )
        expected_str = "[INFO I001]: Test Info\nThis is an info message."
        assert str(d) == expected_str 