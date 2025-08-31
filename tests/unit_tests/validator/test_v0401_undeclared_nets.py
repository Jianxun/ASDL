"""
V0401: Undeclared Nets (WARNING)

Instance mappings reference nets not declared as ports or internal nets.
"""

from src.asdl.validator import ASDLValidator
from src.asdl.data_structures import ASDLFile, FileInfo, Module, Instance, Port, PortDirection, PortType
from src.asdl.diagnostics import DiagnosticSeverity


def test_v0401_undeclared_nets_warning():
    """
    Test that V0401 undeclared nets warning is currently suppressed.
    
    Note: This diagnostic is temporarily suppressed to provide a clean compile experience.
    It will be re-enabled later with refined validation logic.
    """
    validator = ASDLValidator()

    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="top"),
        modules={
            "child": Module(
                ports={"in": Port(dir=PortDirection.IN, type=PortType.SIGNAL)},
                instances={},  # satisfy Module invariant: needs spice_template or instances
            ),
            "top": Module(
                instances={"I1": Instance(model="child", mappings={"in": "n1", "x": "undecl"})},
            ),
        },
    )

    diags = validator.validate_file(asdl_file)
    v0401 = [d for d in diags if d.code == "V0401"]
    
    # Currently suppressed for clean compile experience
    assert len(v0401) == 0
    
    # TODO: Re-enable when V0401 is refined and re-implemented
    # assert len(v0401) == 1
    # assert v0401[0].severity == DiagnosticSeverity.WARNING

