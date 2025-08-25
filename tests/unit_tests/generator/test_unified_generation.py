"""
Test unified SPICE generation (T0.5).

Tests the generator's ability to handle unified module architecture with
primitive modules (spice_template) generating inline SPICE and hierarchical
modules (instances) generating .subckt definitions.
"""

import pytest
from src.asdl.generator import SPICEGenerator
from src.asdl.data_structures import (
    ASDLFile, FileInfo, Module, Instance, Port, PortDirection, SignalType
)


class TestUnifiedGeneration:
    """Test SPICE generator handling of unified module architecture."""
    
    def test_primitive_module_inline_generation(self):
        """
        TESTS: Modules with spice_template generate inline SPICE
        VALIDATES: Former DeviceModel SPICE generation preserved
        ENSURES: No subcircuit overhead for primitive devices
        """
        # Create primitive module with spice_template
        nfet_module = Module(
            ports={
                "D": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
                "G": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                "S": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
                "B": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE)
            },
            parameters={"L": "0.28u", "W": "3u", "M": 1},
            spice_template="MN{name} {D} {G} {S} {B} nfet_03v3 L={L} W={W} m={M}",
            pdk="gf180mcu"
        )
        
        # Create hierarchical module that uses the primitive
        test_module = Module(
            ports={
                "in": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                "out": Port(dir=PortDirection.OUT, type=SignalType.VOLTAGE),
                "vss": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE)
            },
            instances={
                "M1": Instance(
                    model="nfet_03v3",
                    mappings={"D": "out", "G": "in", "S": "vss", "B": "vss"},
                    parameters={"M": 2}
                )
            }
        )
        
        # Create ASDL file
        asdl_file = ASDLFile(
            file_info=FileInfo(top_module="test_circuit"),
            modules={
                "nfet_03v3": nfet_module,
                "test_circuit": test_module
            }
        )
        
        generator = SPICEGenerator()
        spice_output, diagnostics = generator.generate(asdl_file)
        
        # Should include PDK include for primitive module
        assert '.include "gf180mcu_fd_pr/models/ngspice/design.ngspice"' in spice_output
        
        # Should have .subckt for hierarchical module only
        assert ".subckt test_circuit" in spice_output
        assert ".subckt nfet_03v3" not in spice_output  # Primitive should not have subckt
        
        # Primitive should be generated inline within hierarchical module
        assert "MNM1 out in vss vss nfet_03v3 L=0.28u W=3u m=2" in spice_output
    
    def test_hierarchical_module_subcircuit_generation(self):
        """
        TESTS: Modules with instances generate .subckt definitions
        VALIDATES: Existing Module SPICE generation preserved
        ENSURES: Proper hierarchical netlisting
        """
        # Create hierarchical module
        inverter = Module(
            ports={
                "in": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                "out": Port(dir=PortDirection.OUT, type=SignalType.VOLTAGE),
                "vdd": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                "vss": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE)
            },
            parameters={"M": 1},
            instances={
                "M1": Instance(
                    model="nfet",
                    mappings={"D": "out", "G": "in", "S": "vss"},
                    parameters={"M": "{M}"}
                ),
                "M2": Instance(
                    model="pfet", 
                    mappings={"D": "out", "G": "in", "S": "vdd"},
                    parameters={"M": "{M}"}
                )
            }
        )
        
        # Create simple primitive modules for the instances
        nfet = Module(spice_template="MN{name} {D} {G} {S} nfet")
        pfet = Module(spice_template="MP{name} {D} {G} {S} pfet")
        
        asdl_file = ASDLFile(
            file_info=FileInfo(top_module="inverter"),
            modules={
                "inverter": inverter,
                "nfet": nfet,
                "pfet": pfet
            }
        )
        
        generator = SPICEGenerator()
        spice_output, diagnostics = generator.generate(asdl_file)
        
        # Should generate .subckt for hierarchical module
        assert ".subckt inverter in out vdd vss" in spice_output
        
        # Should have inline primitive instances
        assert "MNM1 out in vss nfet" in spice_output
        assert "MPM2 out in vdd pfet" in spice_output
        
        # Should close subcircuit
        assert ".ends" in spice_output
    
    def test_pdk_include_statement_generation(self):
        """
        TESTS: PDK field drives .include statement generation
        VALIDATES: Technology integration with unified architecture
        ENSURES: Proper model file inclusion in generated SPICE
        """
        # Create modules with different PDKs
        gf180_nfet = Module(
            spice_template="MN{name} {D} {G} {S} {B} nfet_03v3",
            pdk="gf180mcu"
        )
        
        sky130_nfet = Module(
            spice_template="MN{name} {D} {G} {S} {B} sky130_fd_pr__nfet_01v8",
            pdk="sky130"
        )
        
        # Module without PDK (SPICE primitive)
        resistor = Module(
            spice_template="R{name} {n1} {n2} {R}"
            # No pdk field - SPICE primitive
        )
        
        asdl_file = ASDLFile(
            file_info=FileInfo(top_module="test"),
            modules={
                "gf180_nfet": gf180_nfet,
                "sky130_nfet": sky130_nfet,
                "resistor": resistor
            }
        )
        
        generator = SPICEGenerator()
        spice_output, diagnostics = generator.generate(asdl_file)
        
        # Should include both PDKs but not duplicate
        assert '.include "gf180mcu_fd_pr/models/ngspice/design.ngspice"' in spice_output
        assert '.include "sky130_fd_pr/models/ngspice/design.ngspice"' in spice_output
        
        # Should not include anything for SPICE primitives
        assert "resistor" not in spice_output.split("* PDK model includes")[0]
    
    def test_generator_detects_module_type(self):
        """
        TESTS: Generator correctly identifies primitive vs hierarchical modules
        VALIDATES: Unified generator logic with type-specific output
        ENSURES: Correct SPICE format selection based on module content
        """
        # Primitive module
        primitive = Module(
            spice_template="C{name} {n1} {n2} {C}",
            parameters={"C": "1p"}
        )
        
        # Hierarchical module
        hierarchical = Module(
            instances={
                "C1": Instance(
                    model="cap_primitive",
                    mappings={"n1": "in", "n2": "out"}
                )
            }
        )
        
        asdl_file = ASDLFile(
            file_info=FileInfo(top_module="hierarchical"),
            modules={
                "cap_primitive": primitive,
                "hierarchical": hierarchical
            }
        )
        
        generator = SPICEGenerator()
        spice_output, diagnostics = generator.generate(asdl_file)
        
        # Primitive should be used inline, not as subcircuit
        assert ".subckt cap_primitive" not in spice_output
        
        # Hierarchical should be subcircuit
        assert ".subckt hierarchical" in spice_output
        
        # Primitive should appear inline within hierarchical
        assert "CC1" in spice_output  # Instance of capacitor primitive
    
    def test_mixed_primitive_hierarchical_design(self):
        """
        TESTS: Complete design with both primitive and hierarchical modules
        VALIDATES: Full unified architecture functionality
        ENSURES: Correct SPICE output for realistic circuit
        """
        # Primitive modules
        nfet = Module(
            ports={
                "D": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
                "G": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                "S": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
                "B": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE)
            },
            parameters={"L": "0.28u", "W": "3u"},
            spice_template="MN{name} {D} {G} {S} {B} nfet_03v3 L={L} W={W}",
            pdk="gf180mcu"
        )
        
        pfet = Module(
            ports={
                "D": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
                "G": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                "S": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
                "B": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE)
            },
            parameters={"L": "0.28u", "W": "6u"},
            spice_template="MP{name} {D} {G} {S} {B} pfet_03v3 L={L} W={W}",
            pdk="gf180mcu"
        )
        
        # Hierarchical module - inverter
        inverter = Module(
            ports={
                "in": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                "out": Port(dir=PortDirection.OUT, type=SignalType.VOLTAGE),
                "vdd": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                "vss": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE)
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
                "in": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                "out": Port(dir=PortDirection.OUT, type=SignalType.VOLTAGE),
                "vdd": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                "vss": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE)
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
        
        # Should have PDK include (only one, even though used multiple times)
        pdk_count = spice_output.count('.include "gf180mcu_fd_pr/models/ngspice/design.ngspice"')
        assert pdk_count == 1
        
        # Should have subcircuits for hierarchical modules only
        assert ".subckt inverter" in spice_output
        assert ".subckt buffer" in spice_output
        assert ".subckt nfet" not in spice_output  # primitive
        assert ".subckt pfet" not in spice_output  # primitive
        
        # Should have inline primitive instances in inverter
        assert "MNMN out in vss vss nfet_03v3 L=0.28u W=3u" in spice_output
        assert "MPMP out in vdd vdd pfet_03v3 L=0.28u W=6u" in spice_output
        
        # Should have hierarchical calls in buffer
        assert "X_INV1 in mid vdd vss inverter" in spice_output
        assert "X_INV2 mid out vdd vss inverter" in spice_output
        
        # Should have main circuit instantiation
        assert "XMAIN in out vdd vss buffer" in spice_output
    
    def test_parameter_substitution_in_primitives(self):
        """
        TESTS: Parameter substitution works correctly in spice_template
        VALIDATES: Template substitution with instance parameter overrides
        ENSURES: Proper parameter merging (module defaults + instance overrides)
        """
        resistor = Module(
            ports={
                "n1": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
                "n2": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE)
            },
            parameters={"R": "1k", "TC1": "0", "TC2": "0"},
            spice_template="R{name} {n1} {n2} {R} TC1={TC1} TC2={TC2}"
        )
        
        test_circuit = Module(
            instances={
                "R1": Instance(
                    model="resistor",
                    mappings={"n1": "in", "n2": "out"},
                    parameters={"R": "2k"}  # Override default
                    # TC1, TC2 should use module defaults
                ),
                "R2": Instance(
                    model="resistor", 
                    mappings={"n1": "out", "n2": "gnd"},
                    parameters={"R": "500", "TC1": "1e-3"}  # Override R and TC1
                    # TC2 should use module default
                )
            }
        )
        
        asdl_file = ASDLFile(
            file_info=FileInfo(top_module="test_circuit"),
            modules={
                "resistor": resistor,
                "test_circuit": test_circuit
            }
        )
        
        generator = SPICEGenerator()
        spice_output, diagnostics = generator.generate(asdl_file)
        
        # Check parameter substitution with overrides
        assert "RR1 in out 2k TC1=0 TC2=0" in spice_output  # R overridden
        assert "RR2 out gnd 500 TC1=1e-3 TC2=0" in spice_output  # R and TC1 overridden
    
    def test_error_handling_for_invalid_modules(self):
        """
        TESTS: Generator handles invalid module references gracefully
        VALIDATES: Diagnostic G0401 for missing models
        ENSURES: Robust error handling in unified architecture
        """
        test_module = Module(
            instances={
                "X1": Instance(
                    model="nonexistent_module",
                    mappings={"in": "in", "out": "out"}
                )
            }
        )
        
        asdl_file = ASDLFile(
            file_info=FileInfo(top_module="test"),
            modules={"test": test_module}
        )
        
        generator = SPICEGenerator()
        subckt = generator.generate_subckt(test_module, "test", asdl_file)
        output, diags = generator.generate(asdl_file)
        assert any(d.code == "G0401" for d in diags)
        assert "G0401" in subckt
    
    def test_empty_design_generation(self):
        """
        TESTS: Generator handles empty designs gracefully
        VALIDATES: Minimal valid SPICE output for empty designs
        ENSURES: No crashes on edge cases
        """
        asdl_file = ASDLFile(
            file_info=FileInfo(top_module=None, doc="Empty design"),
            modules={}
        )
        
        generator = SPICEGenerator()
        spice_output, diagnostics = generator.generate(asdl_file)
        
        # Should have header and .end
        assert "* SPICE netlist generated from ASDL" in spice_output
        assert "* Design: Empty design" in spice_output
        assert ".end" in spice_output
        
        # Should not have any includes or subcircuits
        assert ".include" not in spice_output
        assert ".subckt" not in spice_output


class TestVariablesInTemplateGeneration:
    """Test P1.4 variables support in template generation (TDD)."""
    
    def test_template_with_both_parameters_and_variables(self):
        """
        P1.4.1: Template Generation with Parameters and Variables
        TESTS: Template substitution uses both parameters and variables fields
        VALIDATES: Both field types available for template data
        ENSURES: Enhanced template capability preserved in generation
        """
        transistor = Module(
            ports={
                "D": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
                "G": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                "S": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
                "B": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE)
            },
            parameters={"L": "0.28u", "W": "1u", "M": 1},
            variables={"gm": "1e-3", "vth": "0.7", "temp": "27"},
            spice_template="MN{name} {D} {G} {S} {B} nfet_03v3 L={L} W={W} m={M} gm={gm} vth={vth} temp={temp}"
        )
        
        test_circuit = Module(
            instances={
                "M1": Instance(
                    model="transistor",
                    mappings={"D": "drain", "G": "gate", "S": "source", "B": "bulk"},
                    parameters={"W": "2u", "M": 4}  # Override parameters only
                )
            }
        )
        
        asdl_file = ASDLFile(
            file_info=FileInfo(top_module="test_circuit"),
            modules={
                "transistor": transistor,
                "test_circuit": test_circuit
            }
        )
        
        generator = SPICEGenerator()
        spice_output, diagnostics = generator.generate(asdl_file)
        
        # Check that both parameters and variables are substituted
        assert "L=0.28u" in spice_output       # parameter default
        assert "W=2u" in spice_output          # parameter overridden
        assert "m=4" in spice_output           # parameter overridden
        assert "gm=1e-3" in spice_output       # variable value
        assert "vth=0.7" in spice_output       # variable value
        assert "temp=27" in spice_output       # variable value
    
    def test_variable_shadowing_of_parameters(self):
        """
        P1.4.2: Variable Shadowing of Parameters
        TESTS: Variables take priority over parameters with same names
        VALIDATES: Variable shadowing behavior as designed
        ENSURES: Correct precedence: variables > instance params > module params
        """
        device = Module(
            ports={
                "n1": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
                "n2": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE)
            },
            parameters={"value": "1k", "temp": "25"},  # Default parameter values
            variables={"temp": "75"},  # Variable shadows parameter 'temp'
            spice_template="R{name} {n1} {n2} {value} temp={temp}"
        )
        
        test_circuit = Module(
            instances={
                "R1": Instance(
                    model="device",
                    mappings={"n1": "in", "n2": "out"},
                    parameters={"value": "2k", "temp": "50"}  # Try to override both
                    # 'value' should be overridden to '2k'
                    # 'temp' should remain '75' from variable (shadowing)
                )
            }
        )
        
        asdl_file = ASDLFile(
            file_info=FileInfo(top_module="test_circuit"),
            modules={
                "device": device,
                "test_circuit": test_circuit
            }
        )
        
        generator = SPICEGenerator()
        spice_output, diagnostics = generator.generate(asdl_file)
        
        # Variable 'temp' should shadow parameter override
        assert "RR1 in out 2k temp=75" in spice_output
        # NOT: "temp=50" (instance override blocked by variable shadowing)
        # NOT: "temp=25" (module parameter shadowed by variable)
    
    def test_template_with_variables_only(self):
        """
        P1.4.3: Template with Variables Only
        TESTS: Template generation works with variables field only
        VALIDATES: Variables-only module template substitution
        ENSURES: Variables field sufficient for template generation
        """
        voltage_source = Module(
            ports={
                "plus": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
                "minus": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE)
            },
            # No parameters field
            variables={"voltage": "1.8", "rise_time": "10n", "fall_time": "10n"},
            spice_template="V{name} {plus} {minus} DC {voltage} rise={rise_time} fall={fall_time}"
        )
        
        test_circuit = Module(
            instances={
                "VDD": Instance(
                    model="voltage_source",
                    mappings={"plus": "vdd", "minus": "gnd"}
                    # No parameter overrides
                )
            }
        )
        
        asdl_file = ASDLFile(
            file_info=FileInfo(top_module="test_circuit"),
            modules={
                "voltage_source": voltage_source,
                "test_circuit": test_circuit
            }
        )
        
        generator = SPICEGenerator()
        spice_output, diagnostics = generator.generate(asdl_file)
        
        # All variables should be substituted
        assert "VVDD vdd gnd DC 1.8 rise=10n fall=10n" in spice_output
    
    def test_template_with_parameters_only_unchanged(self):
        """
        P1.4.4: Template with Parameters Only (Regression Test)
        TESTS: Existing parameter-only templates continue to work
        VALIDATES: Backward compatibility maintained
        ENSURES: No regression in existing functionality
        """
        capacitor = Module(
            ports={
                "n1": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
                "n2": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE)
            },
            parameters={"C": "1p", "IC": "0"},
            # No variables field
            spice_template="C{name} {n1} {n2} {C} IC={IC}"
        )
        
        test_circuit = Module(
            instances={
                "C1": Instance(
                    model="capacitor",
                    mappings={"n1": "node1", "n2": "node2"},
                    parameters={"C": "10p"}  # Override capacitance
                )
            }
        )
        
        asdl_file = ASDLFile(
            file_info=FileInfo(top_module="test_circuit"),
            modules={
                "capacitor": capacitor,
                "test_circuit": test_circuit
            }
        )
        
        generator = SPICEGenerator()
        spice_output, diagnostics = generator.generate(asdl_file)
        
        # Should work exactly as before
        assert "CC1 node1 node2 10p IC=0" in spice_output