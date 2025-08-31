import pytest
from asdl.data_structures import (
    ASDLFile,
    Module,
    Instance,
    FileInfo,
)
from asdl.elaborator import Elaborator


def test_basic_instance_expansion():
    """
    Test that a simple <p,n> pattern in an instance name is correctly
    expanded, along with its mappings.
    """
    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="test_module"),
        modules={
            "test_module": Module(
                instances={
                    "M<p,n>": Instance(
                        model="nmos",
                        mappings={
                            "D": "out_<p,n>",
                            "G": "in",
                            "S": "vss",
                            "B": "vss",
                        },
                    )
                }
            )
        },
    )

    elaborator = Elaborator()
    elaborated_file, diagnostics = elaborator.elaborate(asdl_file)

    assert not diagnostics
    assert elaborated_file.modules is not None

    elaborated_module = elaborated_file.modules["test_module"]
    assert elaborated_module.instances is not None

    assert "Mp" in elaborated_module.instances
    assert "Mn" in elaborated_module.instances
    assert "M<p,n>" not in elaborated_module.instances

    instance_p = elaborated_module.instances["Mp"]
    assert instance_p.model == "nmos"
    assert instance_p.mappings == {"D": "out_p", "G": "in", "S": "vss", "B": "vss"}

    instance_n = elaborated_module.instances["Mn"]
    assert instance_n.model == "nmos"
    assert instance_n.mappings == {"D": "out_n", "G": "in", "S": "vss", "B": "vss"} 