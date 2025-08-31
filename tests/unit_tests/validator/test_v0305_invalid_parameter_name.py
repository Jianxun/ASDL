"""
V0305: Invalid Parameter Override

Attempting to override a non-existent parameter should produce V0305 with details.
"""

from src.asdl.validator import ASDLValidator
from src.asdl.data_structures import ASDLFile, FileInfo, Module, Instance


def test_v0305_invalid_parameter_name():
    validator = ASDLValidator()

    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="top"),
        modules={
            "prim": Module(spice_template="X {a}", parameters={"W": "1u"}),
            "top": Module(
                instances={
                    "I1": Instance(model="prim", mappings={}, parameters={"L": "0.5u"}),
                }
            ),
        },
    )

    diags = validator.validate_file(asdl_file)
    codes = [d.code for d in diags]
    assert codes.count("V0305") == 1

