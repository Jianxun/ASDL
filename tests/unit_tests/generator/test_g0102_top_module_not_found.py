from src.asdl.generator import SPICEGenerator
from src.asdl.data_structures import ASDLFile, FileInfo, Module


def test_g0102_top_module_not_found_emits_diagnostic_and_no_xmain():
    gen = SPICEGenerator()

    # Design specifies a top module that does not exist in modules
    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="top", doc="G0102 test"),
        modules={
            # Intentionally omit 'top'
            "child": Module(spice_template="R{name} {n1} {n2} {R}")
        },
    )

    output, diags = gen.generate(asdl_file)

    # Should emit ERROR diagnostic G0102
    assert any(d.code == "G0102" for d in diags)

    # Should not emit XMAIN line
    assert "XMAIN" not in output

    # Helpful comment in header about the error
    assert "G0102" in output
