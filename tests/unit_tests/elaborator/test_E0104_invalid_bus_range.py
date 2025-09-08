from asdl.data_structures import ASDLFile, Module, Port, FileInfo, PortDirection, PortType
from asdl.elaborator import Elaborator


def test_E0104_invalid_bus_range_same_msb_lsb():
    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="test_module"),
        modules={
            "test_module": Module(
                ports={
                    "data[1:1]": Port(dir=PortDirection.IN, type=PortType.SIGNAL),
                },
                spice_template="test_module {data[1:1]}",
            )
        },
    )

    elaborator = Elaborator()
    _, diagnostics = elaborator.elaborate(asdl_file)

    assert len(diagnostics) == 1
    d = diagnostics[0]
    assert d.code == "E0104"
    assert "identical msb and lsb" in d.details.lower()

