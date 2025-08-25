"""Test G0401: Unknown Model Reference (XCCSS)."""

from src.asdl.generator import SPICEGenerator
from src.asdl.data_structures import ASDLFile, FileInfo, Module, Instance


def test_g0401_unknown_model_reference_emits_diagnostic():
    gen = SPICEGenerator()

    parent = Module(
        instances={
            "X1": Instance(model="does_not_exist", mappings={}),
        }
    )
    asdl_file = ASDLFile(file_info=FileInfo(doc="Test"), modules={"top": parent})

    # Generate subckt to trigger instance processing
    subckt = gen.generate_subckt(parent, "top", asdl_file)
    output, diags = gen.generate(asdl_file)

    # Diagnostic emitted
    assert any(d.code == "G0401" for d in diags)
    # Helpful comment present in subckt output
    assert "G0401" in subckt


