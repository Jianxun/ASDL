import pytest
from asdl.data_structures import (
    ASDLFile,
    Module,
    Instance,
    FileInfo,
)
from asdl.elaborator import Elaborator
from asdl.diagnostics import Diagnostic, DiagnosticSeverity


def test_mismatched_pattern_count_diagnostic():
    """
    Test that a diagnostic is generated when instance and mapping patterns
    have different item counts.
    """
    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="test_module"),
        models={},
        modules={
            "test_module": Module(
                instances={
                    "M<p,n>": Instance(
                        model="nmos",
                        mappings={
                            "D": "out<1,2,3>",
                            "G": "in",
                        },
                    )
                }
            )
        },
    )

    elaborator = Elaborator()
    elaborated_file, diagnostics = elaborator.elaborate(asdl_file)

    assert len(diagnostics) >= 1
    # Should have at least one pattern count mismatch diagnostic
    pattern_count_diagnostics = [d for d in diagnostics if "Pattern item counts must match: 2 vs 3" in d.details]
    assert len(pattern_count_diagnostics) >= 1
    diagnostic = pattern_count_diagnostics[0]
    assert diagnostic.severity == DiagnosticSeverity.ERROR
    
    # Check that the original instance is preserved on error
    assert elaborated_file is not None
    assert elaborated_file.modules is not None
    elaborated_module = elaborated_file.modules["test_module"]
    assert elaborated_module.instances is not None
    assert "M<p,n>" in elaborated_module.instances 