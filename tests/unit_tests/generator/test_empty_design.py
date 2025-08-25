from src.asdl.generator import SPICEGenerator
from src.asdl.data_structures import ASDLFile, FileInfo


def test_empty_design_generation():
    asdl_file = ASDLFile(file_info=FileInfo(top_module=None, doc="Empty design"), modules={})

    generator = SPICEGenerator()
    spice_output, _ = generator.generate(asdl_file)

    assert "* SPICE netlist generated from ASDL" in spice_output
    assert "* Design: Empty design" in spice_output
    assert ".end" in spice_output
    assert ".include" not in spice_output
    assert ".subckt" not in spice_output
