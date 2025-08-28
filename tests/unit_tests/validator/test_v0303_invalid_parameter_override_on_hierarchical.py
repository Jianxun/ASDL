"""
V0303: Invalid Parameter Override

Parameter overrides are not allowed when the target module is hierarchical.
"""

from src.asdl.validator import ASDLValidator
from src.asdl.data_structures import ASDLFile, FileInfo, Module, Instance


def test_v0303_invalid_parameter_override_on_hierarchical():
    validator = ASDLValidator()

    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="top"),
        modules={
            "child": Module(instances={}),
            "hier": Module(instances={"U": Instance(model="child", mappings={})}),
            "top": Module(
                instances={
                    "I1": Instance(model="hier", mappings={}, parameters={"drive": "2X"}),
                }
            ),
        },
    )

    diags = validator.validate_file(asdl_file)
    codes = [d.code for d in diags]
    assert codes.count("V0303") == 1

