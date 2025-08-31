"""
Test cases for the unified Module class architecture.

This test suite validates the unified Module class that replaces the separate
DeviceModel and Module classes. The unified Module supports both primitive
(with spice_template) and hierarchical (with instances) modules.

Tests correspond to T0.1 in the ASDL Import System Test Plan.
"""

import pytest
from src.asdl.data_structures import (
    Module, Port, PortDirection, PortType, Instance, PrimitiveType
)


class TestUnifiedModule:
    """Test cases for unified Module class architecture (T0.1)."""
    
    def test_primitive_module_creation(self):
        """
        T0.1.1: Primitive Module Creation
        TESTS: Basic primitive module instantiation with spice_template
        VALIDATES: Module can represent PDK primitives (former DeviceModel functionality)
        ENSURES: spice_template field works correctly for inline SPICE generation
        """
        # Create a primitive module (former DeviceModel equivalent)
        module = Module(
            doc="NMOS transistor from GF180MCU PDK",
            ports={
                'D': Port(dir=PortDirection.IN_OUT, type=PortType.SIGNAL),
                'G': Port(dir=PortDirection.IN, type=PortType.SIGNAL),
                'S': Port(dir=PortDirection.IN_OUT, type=PortType.SIGNAL),
                'B': Port(dir=PortDirection.IN_OUT, type=PortType.SIGNAL)
            },
            parameters={'W': '1u', 'L': '0.28u', 'M': '1'},
            spice_template="MN {D} {G} {S} {B} nfet_03v3 W={W} L={L} M={M}",
            pdk="gf180mcu"
        )
        
        # Validate primitive module properties
        assert module.spice_template is not None
        assert module.spice_template == "MN {D} {G} {S} {B} nfet_03v3 W={W} L={L} M={M}"
        assert module.pdk == "gf180mcu"
        assert module.instances is None  # Primitive modules have no instances
        assert module.doc == "NMOS transistor from GF180MCU PDK"
        assert module.parameters['W'] == '1u'
        assert len(module.ports) == 4
        
    def test_hierarchical_module_creation(self):
        """
        T0.1.2: Hierarchical Module Creation
        TESTS: Hierarchical module instantiation with instances
        VALIDATES: Module can represent circuit hierarchies (existing Module functionality)
        ENSURES: instances field works correctly for subcircuit generation
        """
        # Create a hierarchical module (existing Module behavior)
        module = Module(
            doc="Basic CMOS inverter",
            ports={
                'in': Port(dir=PortDirection.IN, type=PortType.SIGNAL),
                'out': Port(dir=PortDirection.OUT, type=PortType.SIGNAL),
                'vdd': Port(dir=PortDirection.IN_OUT, type=PortType.SIGNAL),
                'vss': Port(dir=PortDirection.IN_OUT, type=PortType.SIGNAL)
            },
            parameters={'M': '1'},
            instances={
                'MP': Instance(
                    model='pmos_unit',
                    mappings={'G': 'in', 'D': 'out', 'S': 'vdd', 'B': 'vdd'},
                    parameters={'M': '2'}
                ),
                'MN': Instance(
                    model='nmos_unit', 
                    mappings={'G': 'in', 'D': 'out', 'S': 'vss', 'B': 'vss'},
                    parameters={'M': '1'}
                )
            }
        )
        
        # Validate hierarchical module properties
        assert module.instances is not None
        assert len(module.instances) == 2
        assert 'MP' in module.instances
        assert 'MN' in module.instances
        assert module.spice_template is None  # Hierarchical modules have no spice_template
        assert module.pdk is None  # PDK field only for primitives
        assert module.doc == "Basic CMOS inverter"
        assert module.parameters['M'] == '1'
        assert len(module.ports) == 4
        
    def test_module_type_classification(self):
        """
        T0.1.3: Module Type Classification
        TESTS: is_primitive() and is_hierarchical() methods
        VALIDATES: Clear distinction between primitive and hierarchical modules
        ENSURES: No ambiguity in module classification for SPICE generation
        """
        # Primitive module
        primitive_module = Module(
            spice_template="MN {D} {G} {S} {B} nfet_03v3",
            pdk="gf180mcu"
        )
        
        # Hierarchical module
        hierarchical_module = Module(
            instances={
                'M1': Instance(model='nmos_unit', mappings={'D': 'out'})
            }
        )
        
        # Test classification methods
        assert primitive_module.is_primitive()
        assert not primitive_module.is_hierarchical()
        
        assert hierarchical_module.is_hierarchical()
        assert not hierarchical_module.is_primitive()
        
    def test_spice_template_instances_mutual_exclusion(self):
        """
        T0.1.4: Mutual Exclusion Enforcement
        TESTS: Cannot have both spice_template and instances fields
        VALIDATES: Architectural constraint preventing hybrid modules
        ENSURES: Clear separation between primitive and hierarchical semantics
        """
        # Should raise ValueError when both spice_template and instances are provided
        with pytest.raises(ValueError, match="Module cannot have both spice_template and instances"):
            Module(
                spice_template="MN {D} {G} {S} {B} nfet_03v3",
                instances={
                    'M1': Instance(model='nmos_unit', mappings={'D': 'out'})
                }
            )
            
        # Should also raise ValueError if neither is provided
        with pytest.raises(ValueError, match="Module must have either spice_template or instances"):
            Module(
                doc="Invalid module with neither implementation"
            )
            
    def test_pdk_field_for_include_generation(self):
        """
        T0.1.5: PDK Field Integration
        TESTS: pdk field on primitive modules
        VALIDATES: PDK information preserved for .include statement generation
        ENSURES: Technology information flows to SPICE generation phase
        """
        # Primitive module with PDK field
        pdk_module = Module(
            spice_template="MN {D} {G} {S} {B} nfet_03v3 W={W} L={L}",
            pdk="gf180mcu",
            parameters={'W': '1u', 'L': '0.28u'}
        )
        
        # SPICE primitive without PDK (built-in SPICE device)
        spice_module = Module(
            spice_template="V{name} {plus} {minus} DC {voltage}",
            parameters={'voltage': '1.8'}
            # No pdk field - this is a built-in SPICE primitive
        )
        
        # Validate PDK field handling
        assert pdk_module.pdk == "gf180mcu"
        assert pdk_module.is_primitive()
        
        assert spice_module.pdk is None
        assert spice_module.is_primitive()
        
    def test_primitive_module_parameter_handling(self):
        """
        Additional test: Parameter handling in primitive modules
        TESTS: Parameters work correctly with spice_template
        VALIDATES: Template parameter substitution preparation
        ENSURES: Parameter values preserved for SPICE generation
        """
        module = Module(
            spice_template="MN {D} {G} {S} {B} nfet_03v3 W={W} L={L} nf={nf} M={M}",
            pdk="gf180mcu",
            parameters={
                'W': '4u',
                'L': '0.5u', 
                'nf': '2',
                'M': '1'
            }
        )
        
        assert module.parameters is not None
        assert module.parameters['W'] == '4u'
        assert module.parameters['L'] == '0.5u'
        assert module.parameters['nf'] == '2'
        assert module.parameters['M'] == '1'
        
    def test_hierarchical_module_parameter_handling(self):
        """
        Additional test: Parameter handling in hierarchical modules
        TESTS: Parameters work correctly with instances
        VALIDATES: Module-level parameters for hierarchical designs
        ENSURES: Parameter inheritance and override patterns work
        """
        module = Module(
            parameters={'M': '1', 'sizing_factor': '2.0'},
            instances={
                'M1': Instance(
                    model='nmos_unit',
                    mappings={'D': 'out', 'G': 'in'},
                    parameters={'M': '2'}  # Override module parameter
                )
            }
        )
        
        assert module.parameters is not None
        assert module.parameters['M'] == '1'
        assert module.parameters['sizing_factor'] == '2.0'
        assert module.instances['M1'].parameters['M'] == '2'
        
    def test_module_with_metadata_field(self):
        """
        Additional test: Metadata field integration
        TESTS: metadata field works with unified Module
        VALIDATES: Extensible metadata storage preserved
        ENSURES: Tool annotations and design intent can be stored
        """
        module = Module(
            spice_template="MN {D} {G} {S} {B} nfet_03v3",
            pdk="gf180mcu",
            metadata={
                "circuit_type": "analog",
                "verification_status": "validated",
                "layout_hints": {"placement": "symmetric"}
            }
        )
        
        assert module.metadata is not None
        assert module.metadata["circuit_type"] == "analog"
        assert module.metadata["verification_status"] == "validated"
        assert module.metadata["layout_hints"]["placement"] == "symmetric"