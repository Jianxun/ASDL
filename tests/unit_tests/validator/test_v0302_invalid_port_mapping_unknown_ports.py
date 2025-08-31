"""
V0302: Invalid Port Mapping

Instance maps to unknown ports on the target module.
"""

from src.asdl.validator import ASDLValidator
from src.asdl.data_structures import ASDLFile, FileInfo, Module, Instance, Port, PortDirection, PortType


def test_v0302_invalid_port_mapping_unknown_ports():
    validator = ASDLValidator()

    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="top"),
        modules={
            "child": Module(
                ports={
                    "in": Port(dir=PortDirection.IN, type=PortType.SIGNAL),
                },
                instances={},
            ),
            "top": Module(
                instances={
                    "I1": Instance(model="child", mappings={"in": "n1", "bad": "n2"}),
                }
            ),
        },
    )

    diags = validator.validate_file(asdl_file)
    codes = [d.code for d in diags]
    assert codes.count("V0302") == 1

