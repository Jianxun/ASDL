from src.asdl.generator import SPICEGenerator
from src.asdl.data_structures import ASDLFile, FileInfo, Module, Instance, Port, PortDirection, SignalType


def test_template_with_both_parameters_and_variables():
    transistor = Module(
        ports={
            "D": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
            "G": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
            "S": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
            "B": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
        },
        parameters={"L": "0.28u", "W": "1u", "M": 1},
        variables={"gm": "1e-3", "vth": "0.7", "temp": "27"},
        spice_template="MN{name} {D} {G} {S} {B} nfet_03v3 L={L} W={W} m={M} gm={gm} vth={vth} temp={temp}",
    )

    test_circuit = Module(
        instances={
            "M1": Instance(
                model="transistor",
                mappings={"D": "drain", "G": "gate", "S": "source", "B": "bulk"},
                parameters={"W": "2u", "M": 4},
            )
        }
    )

    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="test_circuit"),
        modules={"transistor": transistor, "test_circuit": test_circuit},
    )

    generator = SPICEGenerator()
    spice_output, _ = generator.generate(asdl_file)

    assert "L=0.28u" in spice_output
    assert "W=2u" in spice_output
    assert "m=4" in spice_output
    assert "gm=1e-3" in spice_output
    assert "vth=0.7" in spice_output
    assert "temp=27" in spice_output


def test_variable_shadowing_of_parameters():
    device = Module(
        ports={
            "n1": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
            "n2": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
        },
        parameters={"value": "1k", "temp": "25"},
        variables={"temp": "75"},
        spice_template="R{name} {n1} {n2} {value} temp={temp}",
    )

    test_circuit = Module(
        instances={
            "R1": Instance(
                model="device",
                mappings={"n1": "in", "n2": "out"},
                parameters={"value": "2k", "temp": "50"},
            )
        }
    )

    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="test_circuit"),
        modules={"device": device, "test_circuit": test_circuit},
    )

    generator = SPICEGenerator()
    spice_output, _ = generator.generate(asdl_file)

    assert "RR1 in out 2k temp=75" in spice_output


def test_template_with_variables_only():
    voltage_source = Module(
        ports={
            "plus": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
            "minus": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
        },
        variables={"voltage": "1.8", "rise_time": "10n", "fall_time": "10n"},
        spice_template="V{name} {plus} {minus} DC {voltage} rise={rise_time} fall={fall_time}",
    )

    test_circuit = Module(
        instances={
            "VDD": Instance(model="voltage_source", mappings={"plus": "vdd", "minus": "gnd"})
        }
    )

    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="test_circuit"),
        modules={"voltage_source": voltage_source, "test_circuit": test_circuit},
    )

    generator = SPICEGenerator()
    spice_output, _ = generator.generate(asdl_file)

    assert "VVDD vdd gnd DC 1.8 rise=10n fall=10n" in spice_output


def test_template_with_parameters_only():
    capacitor = Module(
        ports={
            "n1": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
            "n2": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
        },
        parameters={"C": "1p", "IC": "0"},
        spice_template="C{name} {n1} {n2} {C} IC={IC}",
    )

    test_circuit = Module(
        instances={
            "C1": Instance(model="capacitor", mappings={"n1": "node1", "n2": "node2"}, parameters={"C": "10p"})
        }
    )

    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="test_circuit"),
        modules={"capacitor": capacitor, "test_circuit": test_circuit},
    )

    generator = SPICEGenerator()
    spice_output, _ = generator.generate(asdl_file)

    assert "CC1 node1 node2 10p IC=0" in spice_output
