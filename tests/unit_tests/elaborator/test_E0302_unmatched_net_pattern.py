from asdl.data_structures import ASDLFile, Module, Instance, FileInfo
from asdl.elaborator import Elaborator


def test_E0302_unmatched_net_pattern_without_instance_pattern():
    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="test_module"),
        modules={
            "test_module": Module(
                instances={
                    "M1": Instance(
                        model="nmos",
                        mappings={
                            "D": "out<1,2>",
                        },
                    )
                }
            )
        },
    )

    elaborator = Elaborator()
    _, diagnostics = elaborator.elaborate(asdl_file)

    assert any(d.code == "E0302" for d in diagnostics)

