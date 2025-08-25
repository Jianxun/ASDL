from src.asdl.generator import SPICEGenerator
from src.asdl.data_structures import ASDLFile, FileInfo, Module, Instance, Port, PortDirection, SignalType


def test_hierarchical_module_subcircuit_generation():
    inverter = Module(
        ports={
            "in": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
            "out": Port(dir=PortDirection.OUT, type=SignalType.VOLTAGE),
            "vdd": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
            "vss": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
        },
        parameters={"M": 1},
        instances={
            "M1": Instance(
                model="nfet",
                mappings={"D": "out", "G": "in", "S": "vss"},
                parameters={"M": "{M}"},
            ),
            "M2": Instance(
                model="pfet",
                mappings={"D": "out", "G": "in", "S": "vdd"},
                parameters={"M": "{M}"},
            ),
        },
    )

    nfet = Module(spice_template="MN{name} {D} {G} {S} nfet")
    pfet = Module(spice_template="MP{name} {D} {G} {S} pfet")

    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="inverter"),
        modules={"inverter": inverter, "nfet": nfet, "pfet": pfet},
    )

    generator = SPICEGenerator()
    spice_output, _ = generator.generate(asdl_file)

    assert ".subckt inverter in out vdd vss" in spice_output
    assert "MNM1 out in vss nfet" in spice_output
    assert "MPM2 out in vdd pfet" in spice_output
    assert ".ends" in spice_output
