"""
Test cases for the unified ASDLFile structure.

This test suite validates the simplified ASDLFile structure that removes the
separate models field and uses only the unified modules field. Also tests
the foundation for import declarations.

Tests correspond to T0.2 in the ASDL Import System Test Plan.
"""

import pytest
from src.asdl.data_structures import (
    ASDLFile, FileInfo, Module, Instance, Port, PortDirection, SignalType
)


class TestUnifiedASDLFile:
    """Test cases for unified ASDLFile structure (T0.2)."""
    
    def test_no_models_field_exists(self):
        """
        T0.2.1: Models Section Elimination
        TESTS: ASDLFile has no models field
        VALIDATES: Complete elimination of DeviceModel/Module redundancy
        ENSURES: Single unified representation reduces parser complexity
        """
        file_info = FileInfo(
            top_module="test_design",
            doc="Test ASDL file",
            revision="1.0"
        )
        
        # Create ASDLFile with only unified modules
        asdl_file = ASDLFile(
            file_info=file_info,
            modules={
                'nmos_unit': Module(
                    spice_template="MN {D} {G} {S} {B} nfet_03v3",
                    pdk="gf180mcu"
                ),
                'inverter': Module(
                    instances={
                        'M1': Instance(model='nmos_unit', mappings={'D': 'out'})
                    }
                )
            }
        )
        
        # Validate no models field exists
        assert hasattr(asdl_file, 'modules')
        assert not hasattr(asdl_file, 'models')  # Should not exist
        assert len(asdl_file.modules) == 2
        
    def test_modules_contains_both_types(self):
        """
        T0.2.2: Unified Modules Section
        TESTS: modules field contains both primitive and hierarchical modules
        VALIDATES: Single namespace for all component types
        ENSURES: Simplified import resolution (no type-specific lookups)
        """
        file_info = FileInfo(top_module="mixed_design")
        
        # Create modules with both primitive and hierarchical types
        modules = {
            # Primitive modules (former DeviceModel)
            'nmos_unit': Module(
                doc="NMOS unit device",
                spice_template="MN {D} {G} {S} {B} nfet_03v3 W={W} L={L}",
                pdk="gf180mcu",
                parameters={'W': '1u', 'L': '0.28u'}
            ),
            'pmos_unit': Module(
                doc="PMOS unit device", 
                spice_template="MP {D} {G} {S} {B} pfet_03v3 W={W} L={L}",
                pdk="gf180mcu",
                parameters={'W': '2u', 'L': '0.28u'}
            ),
            'vsource': Module(
                doc="Voltage source",
                spice_template="V{name} {plus} {minus} DC {voltage}",
                parameters={'voltage': '1.8'}
                # No pdk field - this is a built-in SPICE primitive
            ),
            
            # Hierarchical modules
            'inverter': Module(
                doc="CMOS inverter",
                ports={
                    'in': Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                    'out': Port(dir=PortDirection.OUT, type=SignalType.VOLTAGE)
                },
                instances={
                    'MP': Instance(
                        model='pmos_unit',
                        mappings={'G': 'in', 'D': 'out', 'S': 'vdd'},
                        parameters={'W': '4u'}
                    ),
                    'MN': Instance(
                        model='nmos_unit', 
                        mappings={'G': 'in', 'D': 'out', 'S': 'vss'},
                        parameters={'W': '2u'}
                    )
                }
            ),
            'testbench': Module(
                doc="Test circuit",
                instances={
                    'DUT': Instance(model='inverter', mappings={'in': 'vin', 'out': 'vout'}),
                    'VIN': Instance(model='vsource', mappings={'plus': 'vin', 'minus': 'gnd'}),
                    'VDD': Instance(model='vsource', mappings={'plus': 'vdd', 'minus': 'gnd'})
                }
            )
        }
        
        asdl_file = ASDLFile(
            file_info=file_info,
            modules=modules
        )
        
        # Validate unified namespace
        assert len(asdl_file.modules) == 5
        
        # Check primitive modules
        assert asdl_file.modules['nmos_unit'].is_primitive()
        assert asdl_file.modules['pmos_unit'].is_primitive()
        assert asdl_file.modules['vsource'].is_primitive()
        
        # Check hierarchical modules
        assert asdl_file.modules['inverter'].is_hierarchical()
        assert asdl_file.modules['testbench'].is_hierarchical()
        
        # All in same namespace - no type-specific lookups needed
        all_module_names = set(asdl_file.modules.keys())
        expected_names = {'nmos_unit', 'pmos_unit', 'vsource', 'inverter', 'testbench'}
        assert all_module_names == expected_names
        
    def test_instance_model_references(self):
        """
        T0.2.3: Module Reference Resolution
        TESTS: Instance.model references work for unified modules
        VALIDATES: Instance can reference both primitive and hierarchical modules
        ENSURES: No special handling needed for different module types
        """
        file_info = FileInfo(top_module="reference_test")
        
        modules = {
            'resistor': Module(
                spice_template="R{name} {plus} {minus} {resistance}",
                parameters={'resistance': '1k'}
            ),
            'amplifier': Module(
                instances={
                    'R1': Instance(model='resistor', mappings={'plus': 'in', 'minus': 'bias'})
                }
            ),
            'system': Module(
                instances={
                    'AMP1': Instance(model='amplifier', mappings={'in': 'vin', 'out': 'vout'}),
                    'R_LOAD': Instance(model='resistor', mappings={'plus': 'vout', 'minus': 'gnd'})
                }
            )
        }
        
        asdl_file = ASDLFile(
            file_info=file_info,
            modules=modules
        )
        
        # Test Instance references work for both types
        amp_instance = asdl_file.modules['amplifier'].instances['R1']
        assert amp_instance.model == 'resistor'  # References primitive module
        
        sys_amp_instance = asdl_file.modules['system'].instances['AMP1'] 
        assert sys_amp_instance.model == 'amplifier'  # References hierarchical module
        
        sys_resistor_instance = asdl_file.modules['system'].instances['R_LOAD']
        assert sys_resistor_instance.model == 'resistor'  # References primitive module
        
        # Validate references exist in unified namespace
        assert amp_instance.model in asdl_file.modules
        assert sys_amp_instance.model in asdl_file.modules
        assert sys_resistor_instance.model in asdl_file.modules
        
    def test_asdl_file_with_metadata(self):
        """
        Additional test: ASDLFile metadata field integration
        TESTS: metadata field works with unified ASDLFile structure
        VALIDATES: File-level metadata preserved in unified structure
        ENSURES: Tool annotations and design information can be stored
        """
        file_info = FileInfo(
            top_module="test_design",
            doc="Test design with metadata"
        )
        
        asdl_file = ASDLFile(
            file_info=file_info,
            modules={
                'nmos': Module(spice_template="MN {D} {G} {S} {B} nfet_03v3", pdk="gf180mcu")
            },
            metadata={
                "design_intent": "proof of concept",
                "technology": "gf180mcu",
                "simulation_corners": ["TT", "SS", "FF"],
                "verification_status": {
                    "drc": "clean",
                    "lvs": "clean", 
                    "simulation": "passing"
                }
            }
        )
        
        assert asdl_file.metadata is not None
        assert asdl_file.metadata["design_intent"] == "proof of concept"
        assert asdl_file.metadata["technology"] == "gf180mcu"
        assert asdl_file.metadata["simulation_corners"] == ["TT", "SS", "FF"]
        assert asdl_file.metadata["verification_status"]["drc"] == "clean"
        
    def test_empty_modules_section(self):
        """
        Additional test: ASDLFile with empty modules
        TESTS: ASDLFile can have empty modules dictionary
        VALIDATES: Minimal valid ASDLFile structure
        ENSURES: Empty designs are supported
        """
        file_info = FileInfo(
            top_module=None,  # No top module for empty design
            doc="Empty design template"
        )
        
        asdl_file = ASDLFile(
            file_info=file_info,
            modules={}  # Empty modules
        )
        
        assert asdl_file.modules is not None
        assert len(asdl_file.modules) == 0
        assert isinstance(asdl_file.modules, dict)
        
    def test_file_info_integration(self):
        """
        Additional test: FileInfo integration with unified structure
        TESTS: FileInfo works correctly with unified modules
        VALIDATES: top_module field references unified modules
        ENSURES: File metadata integrates properly
        """
        file_info = FileInfo(
            top_module="main_circuit",
            doc="Test circuit with file info",
            revision="2.0",
            author="Test Engineer",
            date="2024-03-20"
        )
        
        modules = {
            'main_circuit': Module(
                doc="Main circuit module",
                instances={
                    'SUBCKT1': Instance(model='helper_module', mappings={'in': 'input'})
                }
            ),
            'helper_module': Module(
                spice_template="X{name} {in} {out} helper_subckt",
                pdk="test_pdk"
            )
        }
        
        asdl_file = ASDLFile(
            file_info=file_info,
            modules=modules
        )
        
        # Validate file info
        assert asdl_file.file_info.top_module == "main_circuit"
        assert asdl_file.file_info.doc == "Test circuit with file info"
        assert asdl_file.file_info.revision == "2.0"
        
        # Validate top_module reference exists
        assert asdl_file.file_info.top_module in asdl_file.modules
        top_module = asdl_file.modules[asdl_file.file_info.top_module]
        assert top_module.is_hierarchical()
        assert 'SUBCKT1' in top_module.instances