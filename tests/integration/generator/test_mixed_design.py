"""Integration test: mixed primitive and hierarchical design generation."""

from src.asdl.generator import SPICEGenerator
from src.asdl.data_structures import (
    ASDLFile, FileInfo, Module, Instance, Port, PortDirection, PortType
)


def test_mixed_primitive_hierarchical_design_integration():
    # Primitive modules
    nfet = Module(
        ports={
            "D": Port(dir=PortDirection.IN_OUT, type=PortType.SIGNAL),
            "G": Port(dir=PortDirection.IN, type=PortType.SIGNAL),
            "S": Port(dir=PortDirection.IN_OUT, type=PortType.SIGNAL),
            "B": Port(dir=PortDirection.IN_OUT, type=PortType.SIGNAL)
        },
        parameters={"L": "0.28u", "W": "3u"},
        spice_template="MN{name} {D} {G} {S} {B} nfet_03v3 L={L} W={W}",
        pdk="gf180mcu"
    )

    pfet = Module(
        ports={
            "D": Port(dir=PortDirection.IN_OUT, type=PortType.SIGNAL),
            "G": Port(dir=PortDirection.IN, type=PortType.SIGNAL),
            "S": Port(dir=PortDirection.IN_OUT, type=PortType.SIGNAL),
            "B": Port(dir=PortDirection.IN_OUT, type=PortType.SIGNAL)
        },
        parameters={"L": "0.28u", "W": "6u"},
        spice_template="MP{name} {D} {G} {S} {B} pfet_03v3 L={L} W={W}",
        pdk="gf180mcu"
    )

    # Hierarchical module - inverter
    inverter = Module(
        ports={
            "in": Port(dir=PortDirection.IN, type=PortType.SIGNAL),
            "out": Port(dir=PortDirection.OUT, type=PortType.SIGNAL),
            "vdd": Port(dir=PortDirection.IN, type=PortType.SIGNAL),
            "vss": Port(dir=PortDirection.IN, type=PortType.SIGNAL)
        },
        instances={
            "MN": Instance(
                model="nfet",
                mappings={"D": "out", "G": "in", "S": "vss", "B": "vss"},
                parameters={"W": "3u"}
            ),
            "MP": Instance(
                model="pfet",
                mappings={"D": "out", "G": "in", "S": "vdd", "B": "vdd"},
                parameters={"W": "6u"}
            )
        }
    )

    # Top-level hierarchical module
    buffer = Module(
        ports={
            "in": Port(dir=PortDirection.IN, type=PortType.SIGNAL),
            "out": Port(dir=PortDirection.OUT, type=PortType.SIGNAL),
            "vdd": Port(dir=PortDirection.IN, type=PortType.SIGNAL),
            "vss": Port(dir=PortDirection.IN, type=PortType.SIGNAL)
        },
        instances={
            "INV1": Instance(
                model="inverter",
                mappings={"in": "in", "out": "mid", "vdd": "vdd", "vss": "vss"}
            ),
            "INV2": Instance(
                model="inverter",
                mappings={"in": "mid", "out": "out", "vdd": "vdd", "vss": "vss"}
            )
        }
    )

    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="buffer", doc="Two-stage buffer"),
        modules={
            "nfet": nfet,
            "pfet": pfet,
            "inverter": inverter,
            "buffer": buffer
        }
    )

    generator = SPICEGenerator()
    spice_output, diagnostics = generator.generate(asdl_file)

    # Include deduplication - removed since generator no longer emits PDK includes
    # assert spice_output.count('.include "gf180mcu_fd_pr/models/ngspice/design.ngspice"') == 1

    # Subcircuits for hierarchical modules only
    assert ".subckt inverter" in spice_output
    assert ".subckt buffer" in spice_output
    assert ".subckt nfet" not in spice_output
    assert ".subckt pfet" not in spice_output

    # Inline primitives inside inverter
    assert "MNMN out in vss vss nfet_03v3 L=0.28u W=3u" in spice_output
    assert "MPMP out in vdd vdd pfet_03v3 L=0.28u W=6u" in spice_output

    # Hierarchical calls in buffer
    assert "X_INV1 in mid vdd vss inverter" in spice_output
    assert "X_INV2 mid out vdd vss inverter" in spice_output

            # Main circuit instantiation - removed since generator no longer emits XMAIN
        # assert "XMAIN in out vdd vss buffer" in spice_output


