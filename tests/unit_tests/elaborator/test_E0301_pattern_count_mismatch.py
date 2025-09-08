from asdl.data_structures import ASDLFile, Module, Instance, FileInfo
from asdl.elaborator import Elaborator


def test_E0301_pattern_count_mismatch_between_instance_and_mapping():
    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="test_module"),
        modules={
            "test_module": Module(
                instances={
                    "M<p,n>": Instance(
                        model="nmos",
                        mappings={
                            "D": "out<1,2,3>",
                            "G": "in",
                        },
                    )
                }
            )
        },
    )

    elaborator = Elaborator()
    elaborated_file, diagnostics = elaborator.elaborate(asdl_file)

    assert any(d.code == "E0301" for d in diagnostics)
    assert elaborated_file is not None
    assert "M<p,n>" in elaborated_file.modules["test_module"].instances

