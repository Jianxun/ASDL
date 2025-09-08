from asdl.data_structures import ASDLFile, Module, Port, FileInfo, PortDirection, PortType
from asdl.elaborator import Elaborator


def test_E0102_single_item_pattern_in_port_name():
    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="test_module"),
        modules={
            "test_module": Module(
                ports={
                    "in<p>": Port(dir=PortDirection.IN, type=PortType.SIGNAL),
                },
                spice_template="test_module {in<p>}",
            )
        },
    )

    elaborator = Elaborator()
    _, diagnostics = elaborator.elaborate(asdl_file)

    assert len(diagnostics) == 1
    d = diagnostics[0]
    assert d.code == "E0102"
    assert "single item" in d.details.lower()

