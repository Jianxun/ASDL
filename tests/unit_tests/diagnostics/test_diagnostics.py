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
            message="Test error",
            severity=DiagnosticSeverity.ERROR,
            location=loc
        )
        assert d.message == "Test error"
        assert d.severity == DiagnosticSeverity.ERROR
        assert d.location is not None
        assert d.location.start_line == 10
        assert d.location.start_col == 5

    def test_diagnostic_str_with_location(self):
        """Test the string representation of a diagnostic with a location."""
        loc = Locatable(start_line=10, start_col=5)
        d = Diagnostic(
            message="Test warning",
            severity=DiagnosticSeverity.WARNING,
            location=loc
        )
        expected_str = f"[WARNING] at {loc}: Test warning"
        assert str(d) == expected_str

    def test_diagnostic_str_without_location(self):
        """Test the string representation of a diagnostic without a location."""
        d = Diagnostic(
            message="Test info",
            severity=DiagnosticSeverity.INFO
        )
        assert str(d) == "[INFO]: Test info" 