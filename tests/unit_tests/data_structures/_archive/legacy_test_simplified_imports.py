"""
Test cases for the simplified import system data structures.

This test suite validates the simplified ASDLFile import structure that uses
direct file paths and model_alias for local shorthand references.

Tests correspond to T1.1 in the MVP Import System Test Plan.
"""

import pytest
from src.asdl.data_structures import ASDLFile, FileInfo, Module, Instance, Port, PortDirection


class TestSimplifiedImports:
    """Test cases for simplified import data structures (T1.1)."""
    
    def test_simplified_imports_structure(self):
        """
        T1.1.1: Simplified Import Structure
        TESTS: ASDLFile with simple string imports
        VALIDATES: Direct file path imports work
        ENSURES: Clean MVP import structure
        """
        file_info = FileInfo(
            top_module="design_with_imports",
            doc="Design using simplified imports"
        )
        
        # Simple imports: alias -> file path
        imports = {
            "std_devices": "gf180mcu_std_tiles/devices.asdl",
            "amplifiers": "analog_ip/amplifiers.asdl",
            "test_lib": "libs/test_primitives.asdl"
        }
        
        asdl_file = ASDLFile(
            file_info=file_info,
            modules={
                "test_design": Module(
                    instances={
                        "AMP1": Instance(model="amplifiers.two_stage_ota", mappings={"in": "vin"})
                    }
                )
            },
            imports=imports
        )
        
        # Validate simplified imports structure
        assert asdl_file.imports is not None
        assert isinstance(asdl_file.imports, dict)
        assert len(asdl_file.imports) == 3
        
        # Check import values are simple strings
        assert asdl_file.imports["std_devices"] == "gf180mcu_std_tiles/devices.asdl"
        assert asdl_file.imports["amplifiers"] == "analog_ip/amplifiers.asdl"
        assert asdl_file.imports["test_lib"] == "libs/test_primitives.asdl"
        
        # All import values should be strings (not complex objects)
        for alias, path in asdl_file.imports.items():
            assert isinstance(alias, str)
            assert isinstance(path, str)
            assert path.endswith('.asdl')
        
    def test_model_alias_structure(self):
        """
        T1.1.2: model_alias Section Structure  
        TESTS: model_alias field for local module shorthand
        VALIDATES: Local aliasing works for imported modules
        ENSURES: Technology portability through aliases
        """
        file_info = FileInfo(top_module="portable_design")
        
        # Imports and model aliases
        imports = {
            "std_devices": "gf180mcu_std_tiles/devices.asdl",
            "spice_lib": "spice/primitives.asdl"
        }
        
        model_alias = {
            "nmos_unit": "std_devices.nmos_unit_short",
            "pmos_unit": "std_devices.pmos_unit_short", 
            "vsource": "spice_lib.vdc",
            "resistor": "spice_lib.resistor"
        }
        
        modules = {
            "current_mirror": Module(
                instances={
                    "M_REF": Instance(model="nmos_unit", mappings={"G": "bias"}),
                    "M_OUT1": Instance(model="nmos_unit", mappings={"G": "bias"}),
                    "R_BIAS": Instance(model="resistor", mappings={"plus": "vdd"})
                }
            )
        }
        
        asdl_file = ASDLFile(
            file_info=file_info,
            modules=modules,
            imports=imports,
            model_alias=model_alias
        )
        
        # Validate model_alias structure
        assert asdl_file.model_alias is not None
        assert isinstance(asdl_file.model_alias, dict)
        assert len(asdl_file.model_alias) == 4
        
        # Check alias mappings
        assert asdl_file.model_alias["nmos_unit"] == "std_devices.nmos_unit_short"
        assert asdl_file.model_alias["pmos_unit"] == "std_devices.pmos_unit_short"
        assert asdl_file.model_alias["vsource"] == "spice_lib.vdc"
        assert asdl_file.model_alias["resistor"] == "spice_lib.resistor"
        
        # All alias values should follow alias.module_name format
        for local_name, qualified_ref in asdl_file.model_alias.items():
            assert isinstance(local_name, str)
            assert isinstance(qualified_ref, str)
            assert "." in qualified_ref  # Should contain dot separator
            
    def test_combined_imports_and_aliases(self):
        """
        T1.1.3: Combined Import and Alias System
        TESTS: imports and model_alias work together
        VALIDATES: Complete import resolution structure
        ENSURES: MVP functionality for module references
        """
        file_info = FileInfo(top_module="complete_example")
        
        imports = {
            "pdk_primitives": "gf180mcu_pdk/primitives.asdl",
            "analog_blocks": "company_ip/analog.asdl"
        }
        
        model_alias = {
            "nmos": "pdk_primitives.nfet_03v3",
            "pmos": "pdk_primitives.pfet_03v3",
            "ota": "analog_blocks.two_stage_miller"
        }
        
        modules = {
            "inverter": Module(
                ports={
                    "in": Port(dir=PortDirection.IN),
                    "out": Port(dir=PortDirection.OUT)
                },
                instances={
                    "MP": Instance(model="pmos", mappings={"G": "in", "D": "out"}),
                    "MN": Instance(model="nmos", mappings={"G": "in", "D": "out"})
                }
            ),
            "amplifier_testbench": Module(
                instances={
                    "DUT": Instance(model="ota", mappings={"inp": "vin_p", "inn": "vin_n"}),
                    "INV1": Instance(model="inverter", mappings={"in": "clk"})
                }
            )
        }
        
        asdl_file = ASDLFile(
            file_info=file_info,
            modules=modules,
            imports=imports,
            model_alias=model_alias
        )
        
        # Validate complete structure
        assert asdl_file.imports is not None
        assert asdl_file.model_alias is not None
        assert len(asdl_file.imports) == 2
        assert len(asdl_file.model_alias) == 3
        
        # Check import-alias relationship
        # All alias targets should reference imported files
        for local_name, qualified_ref in asdl_file.model_alias.items():
            alias_name = qualified_ref.split('.')[0]
            assert alias_name in asdl_file.imports
            
        # Check instance references use local aliases
        inverter_instances = asdl_file.modules["inverter"].instances
        assert inverter_instances["MP"].model == "pmos"  # Uses alias, not full qualified name
        assert inverter_instances["MN"].model == "nmos"  # Uses alias, not full qualified name
        
        amp_instances = asdl_file.modules["amplifier_testbench"].instances
        assert amp_instances["DUT"].model == "ota"  # Uses alias
        assert amp_instances["INV1"].model == "inverter"  # Uses local module
        
    def test_empty_imports_and_aliases(self):
        """
        T1.1.4: Empty Import and Alias Handling
        TESTS: Optional nature of imports and model_alias
        VALIDATES: Files work without imports/aliases
        ENSURES: Graceful handling of minimal designs
        """
        file_info = FileInfo(top_module="standalone_design")
        
        # File with no imports or aliases
        minimal_file = ASDLFile(
            file_info=file_info,
            modules={
                "simple_resistor": Module(
                    spice_template="R{name} {plus} {minus} {resistance}",
                    parameters={"resistance": "1k"}
                )
            }
            # imports and model_alias default to None
        )
        
        assert minimal_file.imports is None
        assert minimal_file.model_alias is None
        assert len(minimal_file.modules) == 1
        
        # File with empty imports and aliases
        empty_file = ASDLFile(
            file_info=file_info,
            modules={
                "empty_design": Module(instances={})
            },
            imports={},  # Empty dict
            model_alias={}  # Empty dict
        )
        
        assert empty_file.imports is not None
        assert len(empty_file.imports) == 0
        assert empty_file.model_alias is not None
        assert len(empty_file.model_alias) == 0
        
    def test_import_path_validation(self):
        """
        T1.1.5: Import Path Format Validation
        TESTS: Import path string format requirements
        VALIDATES: .asdl file extension requirement
        ENSURES: Clear file resolution expectations
        """
        file_info = FileInfo(top_module="path_test")
        
        # Valid import paths
        valid_imports = {
            "simple": "file.asdl",
            "with_dir": "dir/file.asdl", 
            "nested": "a/b/c/file.asdl",
            "with_underscores": "pdk_lib/device_models.asdl",
            "with_numbers": "gf180mcu_v1.0/primitives.asdl"
        }
        
        asdl_file = ASDLFile(
            file_info=file_info,
            modules={"test": Module(instances={})},
            imports=valid_imports
        )
        
        # All imports should end with .asdl
        for alias, path in asdl_file.imports.items():
            assert path.endswith('.asdl')
            assert isinstance(path, str)
            assert len(path) > 5  # Minimum: "x.asdl"
            
    def test_model_alias_format_validation(self):
        """
        T1.1.6: model_alias Format Validation
        TESTS: model_alias qualified reference format
        VALIDATES: alias.module_name format requirement
        ENSURES: Clear module resolution expectations
        """
        file_info = FileInfo(top_module="alias_test")
        
        imports = {
            "lib1": "library1/modules.asdl",
            "lib2": "library2/devices.asdl"
        }
        
        # Valid model_alias formats
        valid_aliases = {
            "device1": "lib1.nmos_unit",
            "device2": "lib1.pmos_unit",
            "amp": "lib2.operational_amplifier",
            "res": "lib1.precision_resistor"
        }
        
        asdl_file = ASDLFile(
            file_info=file_info,
            modules={"test": Module(instances={})},
            imports=imports,
            model_alias=valid_aliases
        )
        
        # All aliases should follow alias.module_name format
        for local_name, qualified_ref in asdl_file.model_alias.items():
            assert "." in qualified_ref
            alias_part, module_part = qualified_ref.split(".", 1)
            assert alias_part in imports  # Alias part should exist in imports
            assert len(module_part) > 0  # Module part should not be empty
            assert isinstance(local_name, str)
            assert len(local_name) > 0  # Local name should not be empty

    def test_metadata_preserved_with_imports(self):
        """
        T1.1.7: Metadata Integration with Imports
        TESTS: metadata field works with imports and aliases
        VALIDATES: File-level metadata preserved
        ENSURES: Tool annotations work with import system
        """
        file_info = FileInfo(top_module="meta_test")
        
        asdl_file = ASDLFile(
            file_info=file_info,
            modules={"test": Module(instances={})},
            imports={"lib": "test/lib.asdl"},
            model_alias={"device": "lib.test_device"},
            metadata={
                "import_version": "mvp_1.0",
                "dependencies": ["gf180mcu", "company_ip"],
                "validation": {"syntax": "passed", "resolution": "pending"}
            }
        )
        
        assert asdl_file.metadata is not None
        assert asdl_file.metadata["import_version"] == "mvp_1.0"
        assert asdl_file.metadata["dependencies"] == ["gf180mcu", "company_ip"]
        assert asdl_file.metadata["validation"]["syntax"] == "passed"
        
        # Imports and aliases should coexist with metadata
        assert asdl_file.imports is not None
        assert asdl_file.model_alias is not None
        assert len(asdl_file.imports) == 1
        assert len(asdl_file.model_alias) == 1