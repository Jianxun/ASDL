"""
V0601: Unused Modules (WARNING)

Modules defined but never instantiated should be reported (excluding top).
"""

from src.asdl.validator import ASDLValidator
from src.asdl.data_structures import ASDLFile, FileInfo, Module, Instance
from src.asdl.diagnostics import DiagnosticSeverity


def test_v0601_unused_modules_warning():
    validator = ASDLValidator()

    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="top"),
        modules={
            "child": Module(instances={}),
            "unused": Module(instances={}),
            "top": Module(instances={"U1": Instance(model="child", mappings={})}),
        },
    )

    diags = validator.validate_file(asdl_file)
    v0601 = [d for d in diags if d.code == "V0601"]
    assert len(v0601) == 1
    assert v0601[0].severity == DiagnosticSeverity.WARNING
    assert "unused" in v0601[0].details

