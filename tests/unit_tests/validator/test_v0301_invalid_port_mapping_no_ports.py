"""
V0301: Invalid Port Mapping

Instance maps ports but target module defines no ports.
"""

from src.asdl.validator import ASDLValidator
from src.asdl.data_structures import ASDLFile, FileInfo, Module, Instance


def test_v0301_invalid_port_mapping_when_target_has_no_ports():
    validator = ASDLValidator()

    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="top"),
        modules={
            "child": Module(ports=None, instances={}),
            "top": Module(
                instances={
                    "I1": Instance(model="child", mappings={"a": "n1"}),
                }
            ),
        },
    )

    diags = validator.validate_file(asdl_file)
    codes = [d.code for d in diags]
    assert codes.count("V0301") == 1

