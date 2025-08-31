from src.asdl.generator import SPICEGenerator
from src.asdl.data_structures import ASDLFile, FileInfo, Module, Instance, Port, PortDirection, PortType


def test_children_before_parents_and_top_last():
    # child is hierarchical (no inner instances) and should emit before parent and top
    child = Module(
        ports={"a": Port(dir=PortDirection.IN_OUT, type=PortType.SIGNAL)},
        instances={},
    )
    parent = Module(
        ports={"p": Port(dir=PortDirection.IN, type=PortType.SIGNAL)},
        instances={
            "U1": Instance(model="child", mappings={"a": "n1"}),
        },
    )
    top = Module(
        ports={"t": Port(dir=PortDirection.IN, type=PortType.SIGNAL)},
        instances={
            "U2": Instance(model="parent", mappings={"p": "n2"}),
        },
    )

    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="top", doc="ordering"),
        modules={
            # Deliberate insertion order: child, parent, top
            "child": child,
            "parent": parent,
            "top": top,
        },
    )

    gen = SPICEGenerator()
    output, _ = gen.generate(asdl_file)
    lines = [l for l in output.splitlines() if l.startswith(".subckt") or l.startswith("* .subckt")]

    # Expect exactly three subckt lines
    assert len(lines) == 3

    # Order must be: child first, then parent, then top last
    assert lines[0].endswith("child a")
    assert lines[1].endswith("parent p")
    assert lines[2].endswith("top t")


