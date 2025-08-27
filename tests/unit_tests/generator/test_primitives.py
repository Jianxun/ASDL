from src.asdl.generator import SPICEGenerator
from src.asdl.data_structures import ASDLFile, FileInfo, Module, Instance, Port, PortDirection, PortType


def test_primitive_module_inline_generation():
    nfet_module = Module(
        ports={
            "D": Port(dir=PortDirection.IN_OUT, type=PortType.SIGNAL),
            "G": Port(dir=PortDirection.IN, type=PortType.SIGNAL),
            "S": Port(dir=PortDirection.IN_OUT, type=PortType.SIGNAL),
            "B": Port(dir=PortDirection.IN_OUT, type=PortType.SIGNAL),
        },
        parameters={"L": "0.28u", "W": "3u", "M": 1},
        spice_template="MN{name} {D} {G} {S} {B} nfet_03v3 L={L} W={W} m={M}",
        pdk="gf180mcu",
    )

    test_module = Module(
        ports={
            "in": Port(dir=PortDirection.IN, type=PortType.SIGNAL),
            "out": Port(dir=PortDirection.OUT, type=PortType.SIGNAL),
            "vss": Port(dir=PortDirection.IN, type=PortType.SIGNAL),
        },
        instances={
            "M1": Instance(
                model="nfet_03v3",
                mappings={"D": "out", "G": "in", "S": "vss", "B": "vss"},
                parameters={"M": 2},
            )
        },
    )

    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="test_circuit"),
        modules={"nfet_03v3": nfet_module, "test_circuit": test_module},
    )

    generator = SPICEGenerator()
    spice_output, _ = generator.generate(asdl_file)

    assert ".subckt test_circuit" in spice_output
    assert ".subckt nfet_03v3" not in spice_output
    assert "MNM1 out in vss vss nfet_03v3 L=0.28u W=3u m=2" in spice_output


def test_parameter_substitution_in_primitives():
    resistor = Module(
        ports={
            "n1": Port(dir=PortDirection.IN_OUT, type=PortType.SIGNAL),
            "n2": Port(dir=PortDirection.IN_OUT, type=PortType.SIGNAL),
        },
        parameters={"R": "1k", "TC1": "0", "TC2": "0"},
        spice_template="R{name} {n1} {n2} {R} TC1={TC1} TC2={TC2}",
    )

    test_circuit = Module(
        instances={
            "R1": Instance(
                model="resistor",
                mappings={"n1": "in", "n2": "out"},
                parameters={"R": "2k"},
            ),
            "R2": Instance(
                model="resistor",
                mappings={"n1": "out", "n2": "gnd"},
                parameters={"R": "500", "TC1": "1e-3"},
            ),
        }
    )

    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="test_circuit"),
        modules={"resistor": resistor, "test_circuit": test_circuit},
    )

    generator = SPICEGenerator()
    spice_output, _ = generator.generate(asdl_file)

    assert "RR1 in out 2k TC1=0 TC2=0" in spice_output
    assert "RR2 out gnd 500 TC1=1e-3 TC2=0" in spice_output
