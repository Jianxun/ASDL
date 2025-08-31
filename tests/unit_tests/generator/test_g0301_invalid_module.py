from src.asdl.generator import SPICEGenerator
from src.asdl.data_structures import ASDLFile, FileInfo, Module


def test_g0301_invalid_module_definition_emits_diagnostic_and_skips_generation():
    gen = SPICEGenerator()

    # Construct a valid module first, then mutate to invalid to bypass dataclass guard
    invalid = Module(spice_template="R{name} {n1} {n2} {R}")
    invalid.spice_template = None
    invalid.instances = None

    # Another valid hierarchical module to ensure section exists
    parent = Module(instances={})  # empty instances treated as hierarchical

    asdl_file = ASDLFile(
        file_info=FileInfo(top_module=None, doc="G0301 test"),
        modules={
            "invalid_mod": invalid,
            "parent": parent,
        },
    )

    output, diags = gen.generate(asdl_file)

    # Should emit ERROR diagnostic G0301 for the invalid module
    assert any(d.code == "G0301" and "invalid_mod" in d.details for d in diags)

    # Should include a helpful comment in the subckt section
    assert "ERROR G0301" in output
    assert "invalid_mod" in output

    # Should not emit any subckt/device lines for the invalid module
    assert ".subckt invalid_mod" not in output
