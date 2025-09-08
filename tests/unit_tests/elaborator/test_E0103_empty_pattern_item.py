from asdl.data_structures import ASDLFile, Module, Port, FileInfo, PortDirection, PortType
from asdl.elaborator import Elaborator


def test_E0103_empty_pattern_item_in_port_name():
    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="test_module"),
        modules={
            "test_module": Module(
                ports={
                    "in<,>": Port(dir=PortDirection.IN, type=PortType.SIGNAL),
                },
                spice_template="test_module {in<,>}",
            )
        },
    )

    elaborator = Elaborator()
    _, diagnostics = elaborator.elaborate(asdl_file)

    assert any(d.code == "E0103" for d in diagnostics)

