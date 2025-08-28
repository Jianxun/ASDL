"""
V0304: Invalid Variable Override

Instances may not override module variables.
"""

from src.asdl.validator import ASDLValidator
from src.asdl.data_structures import ASDLFile, FileInfo, Module, Instance


def test_v0304_invalid_variable_override():
    validator = ASDLValidator()

    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="top"),
        modules={
            "prim": Module(spice_template="X {a}", variables={"gm": "calc", "vth": "0.7"}),
            "top": Module(
                instances={
                    "I1": Instance(model="prim", mappings={}, parameters={"gm": "x", "vth": "y"}),
                }
            ),
        },
    )

    diags = validator.validate_file(asdl_file)
    codes = [d.code for d in diags]
    assert codes.count("V0304") == 2

