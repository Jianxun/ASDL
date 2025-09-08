from asdl.data_structures import ASDLFile, Module, Instance, FileInfo
from asdl.elaborator import Elaborator


def test_E0402_undefined_variable_in_instance_parameter():
    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="test_module"),
        modules={
            "test_module": Module(
                variables={"WIDTH": "6u"},
                instances={
                    "M1": Instance(
                        model="nmos",
                        mappings={},
                        parameters={"W": "Width"},  # case mismatch triggers heuristic
                    )
                }
            )
        },
    )

    elaborator = Elaborator()
    _, diagnostics = elaborator.elaborate(asdl_file)

    assert any(d.code == "E0402" for d in diagnostics)

