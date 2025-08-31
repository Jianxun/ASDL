"""
V0201: Invalid Module Parameter Declaration

Hierarchical modules (with instances) must not declare 'parameters'.
"""

from src.asdl.validator import ASDLValidator
from src.asdl.data_structures import ASDLFile, FileInfo, Module, Instance


def test_v0201_invalid_module_parameter_declaration():
    validator = ASDLValidator()

    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="top"),
        modules={
            "top": Module(
                instances={"U1": Instance(model="child", mappings={})},
                parameters={"drive": "1X"},
            ),
            "child": Module(instances={}),
        },
    )

    diags = validator.validate_file(asdl_file)
    codes = [d.code for d in diags]
    assert codes.count("V0201") == 1

