from src.asdl.generator import SPICEGenerator
from src.asdl.data_structures import ASDLFile, FileInfo, Module, Instance, Port, PortDirection, PortType


def test_g0201_unconnected_port_in_subckt_call_emits_diagnostic_and_skips_instance():
    gen = SPICEGenerator()

    # Child hierarchical module with ports a,b,c
    child = Module(
        ports={
            "a": Port(dir=PortDirection.IN, type=PortType.SIGNAL),
            "b": Port(dir=PortDirection.IN, type=PortType.SIGNAL),
            "c": Port(dir=PortDirection.IN, type=PortType.SIGNAL),
        },
        instances={},
    )

    # Parent references child but maps only port 'a'
    parent = Module(
        instances={
            "U1": Instance(model="child", mappings={"a": "n1"})
        }
    )

    asdl_file = ASDLFile(
        file_info=FileInfo(top_module=None, doc="G0201 test"),
        modules={
            "child": child,
            "parent": parent,
        },
    )

    subckt = gen.generate_subckt(parent, "parent", asdl_file)
    output, diags = gen.generate(asdl_file)

    # Should emit ERROR diagnostic G0201 with missing ports b,c
    assert any(d.code == "G0201" and "b" in d.details and "c" in d.details for d in diags)

    # Subckt text should contain a helpful error comment and no X_ call for U1
    assert "ERROR G0201" in subckt
    assert "U1" in subckt
    assert "X_U1" not in subckt
