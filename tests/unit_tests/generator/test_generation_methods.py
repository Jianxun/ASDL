"""
Focused, stable unit tests for SPICEGenerator behavior.

Avoids brittle assumptions about internal helper methods and legacy models.
Tests observable contracts of the unified generator API.
"""

import pytest
from src.asdl.generator import SPICEGenerator
from src.asdl.data_structures import (
    ASDLFile, FileInfo, Module, Instance, Port, PortDirection, 
    SignalType
)


class TestSPICEGeneratorBasics:
    """Basic SPICEGenerator contracts that should remain stable across refactors."""

    def test_generator_initialization(self):
        generator = SPICEGenerator()
        assert generator.comment_style == "*"
        assert generator.indent == "  "

    def test_port_order_preserved_in_subckt_header(self):
        generator = SPICEGenerator()
        module = Module(
            doc="Order test",
            ports={
                "in": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                "out": Port(dir=PortDirection.OUT, type=SignalType.VOLTAGE),
                "vdd": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
                "vss": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
            },
            instances={},
        )
        asdl_file = ASDLFile(file_info=FileInfo(doc="Test"), modules={"buf": module})
        subckt = generator.generate_subckt(module, "buf", asdl_file)
        assert subckt.split("\n")[1] == ".subckt buf in out vdd vss"

    def test_hierarchical_call_uses_port_order_and_sorts_params(self):
        generator = SPICEGenerator()
        child = Module(
            ports={
                "a": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
                "b": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
                "c": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
            },
            instances={},  # hierarchical module (no inner instances)
        )
        parent = Module(
            ports={"p": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE)},
            instances={
                "U1": Instance(
                    model="child",
                    mappings={"a": "n1", "b": "n2", "c": "n3"},
                    parameters={"z": 1, "a": 2},
                )
            },
        )
        asdl_file = ASDLFile(file_info=FileInfo(doc="Test"), modules={"child": child, "parent": parent})
        subckt = generator.generate_subckt(parent, "parent", asdl_file)
        assert "X_U1 n1 n2 n3 child a=2 z=1" in subckt

    def test_pdk_include_generation_deduplicates(self):
        generator = SPICEGenerator()
        m1 = Module(spice_template="R{name} {n1} {n2} {R}", pdk="gf180mcu")
        m2 = Module(spice_template="C{name} {n1} {n2} {C}", pdk="gf180mcu")
        m3 = Module(spice_template="D{name} {a} {b}", pdk="sky130")
        asdl_file = ASDLFile(file_info=FileInfo(top_module=None, doc="inc"), modules={
            "r": m1,
            "c": m2,
            "d": m3,
        })
        output, diags = generator.generate(asdl_file)
        assert output.count('gf180mcu_fd_pr/models/ngspice/design.ngspice') == 1
        assert output.count('sky130_fd_pr/models/ngspice/design.ngspice') == 1
        # Allow informational diagnostic for missing top
        assert all(d.code != "G0102" and d.code != "G0401" and not d.severity.name == "ERROR" for d in diags)


    def test_comment_style_and_indentation(self):
        generator = SPICEGenerator()
        prim = Module(ports={"n1": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
                             "n2": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE)},
                      spice_template="R{name} {n1} {n2} {R}",
                      parameters={"R": "1k"})
        top = Module(instances={"R1": Instance(model="prim", mappings={"n1": "a", "n2": "b"})})
        asdl_file = ASDLFile(file_info=FileInfo(top_module="top", doc="Comments"), modules={
            "prim": prim,
            "top": top,
        })
        output, _ = generator.generate(asdl_file)
        # has comment lines and indented content under subckt
        assert any(line.strip().startswith('*') for line in output.splitlines())
        assert any(line.startswith('  ') for line in output.splitlines())