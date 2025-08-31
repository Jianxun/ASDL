from src.asdl.generator import SPICEGenerator
from src.asdl.generator.options import GeneratorOptions, TopStyle
from src.asdl.data_structures import ASDLFile, FileInfo, Module, Instance, Port, PortDirection, PortType


def test_top_style_flat_comments_only_top_wrappers():
    child = Module(
        ports={"a": Port(dir=PortDirection.IN_OUT, type=PortType.SIGNAL)},
        instances={},
    )
    top = Module(
        ports={"t": Port(dir=PortDirection.IN, type=PortType.SIGNAL)},
        instances={
            "U1": Instance(model="child", mappings={"a": "n1"}),
        },
    )

    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="top", doc="flat"),
        modules={"child": child, "top": top},
    )

    gen = SPICEGenerator(options=GeneratorOptions(top_style=TopStyle.FLAT))
    output, _ = gen.generate(asdl_file)
    lines = output.splitlines()

    # Child subckt should be normal (not commented)
    assert any(l.startswith(".subckt child") for l in lines)
    assert any(l == ".ends" for l in lines)

    # Top subckt wrappers should be commented
    assert any(l.startswith("* .subckt top") for l in lines)
    # Ensure commented .ends for top exists
    assert any(l.strip() == "* .ends" for l in lines)


