"""
Test cases for Module variables field (P1.1 - TDD).

This test suite validates the new variables field in the unified Module class
following TDD approach for parameter system enhancement Phase P1.1.

Tests are written before implementation to define expected behavior:
- Variables field creation and usage
- Schema generation includes variables field  
- Validation that variables cannot be overridden in instances

These tests will initially fail until implementation is complete.
"""

import pytest
from src.asdl.data_structures import (
    Module, Port, PortDirection, Instance
)


class TestModuleVariablesField:
    """Test cases for Module variables field functionality (P1.1 TDD)."""
    
    def test_module_creation_with_variables_field(self):
        """
        P1.1.1: Module Creation with Variables Field
        TESTS: Basic module instantiation with variables field
        VALIDATES: variables field accepts Dict[str, Any] data
        ENSURES: variables field distinct from parameters field
        """
        # Create primitive module with both parameters and variables
        module = Module(
            doc="NMOS with computed variables",
            spice_template="MN {D} {G} {S} {B} nfet_03v3 W={W} L={L} M={M}",
            pdk="gf180mcu",
            parameters={'W': '1u', 'L': '0.28u', 'M': '1'},
            variables={'gm': 'computed_at_runtime', 'vth': '0.7'}
        )
        
        # Validate variables field exists and has correct values
        assert module.variables is not None
        assert isinstance(module.variables, dict)
        assert module.variables['gm'] == 'computed_at_runtime'
        assert module.variables['vth'] == '0.7'
        
        # Validate variables field is distinct from parameters
        assert module.parameters is not None
        assert module.parameters['W'] == '1u'
        assert len(module.variables) == 2
        assert len(module.parameters) == 3
        
    def test_module_creation_without_variables_field(self):
        """
        P1.1.2: Module Creation Without Variables Field
        TESTS: Module creation when variables field not provided
        VALIDATES: variables field defaults to None
        ENSURES: Existing functionality unchanged (backward compatibility)
        """
        # Create module without variables field (existing behavior)
        module = Module(
            spice_template="MN {D} {G} {S} {B} nfet_03v3",
            parameters={'W': '1u', 'L': '0.28u'}
        )
        
        # Validate variables field defaults to None
        assert module.variables is None
        assert module.parameters is not None
        assert len(module.parameters) == 2
        
    def test_hierarchical_module_with_variables(self):
        """
        P1.1.3: Hierarchical Module with Variables
        TESTS: Variables field works with hierarchical modules
        VALIDATES: variables can be used in hierarchical designs
        ENSURES: No conflicts between variables and instances fields
        """
        # Create hierarchical module with variables
        module = Module(
            doc="Inverter with design variables",
            instances={
                'MP': Instance(
                    model='pmos_unit',
                    mappings={'G': 'in', 'D': 'out'},
                    parameters={'M': '2'}
                ),
                'MN': Instance(
                    model='nmos_unit',
                    mappings={'G': 'in', 'D': 'out'},
                    parameters={'M': '1'}
                )
            },
            parameters={'drive_strength': '1X'},
            variables={'propagation_delay': 'computed', 'power_consumption': 'TBD'}
        )
        
        # Validate variables field works with hierarchical modules
        assert module.variables is not None
        assert module.variables['propagation_delay'] == 'computed'
        assert module.variables['power_consumption'] == 'TBD'
        assert module.instances is not None
        assert len(module.instances) == 2
        assert module.is_hierarchical()
        
    def test_empty_variables_dict(self):
        """
        P1.1.4: Empty Variables Dictionary
        TESTS: Empty variables dictionary behavior
        VALIDATES: Empty dict vs None distinction
        ENSURES: Explicit empty variables dict is preserved
        """
        # Create module with explicit empty variables dict
        module = Module(
            spice_template="V{name} {plus} {minus} DC {voltage}",
            parameters={'voltage': '1.8'},
            variables={}  # Explicit empty dict
        )
        
        # Validate empty variables dict is preserved (not None)
        assert module.variables is not None
        assert isinstance(module.variables, dict)
        assert len(module.variables) == 0
        assert module.parameters['voltage'] == '1.8'
        
    def test_variables_field_types_validation(self):
        """
        P1.1.5: Variables Field Type Validation
        TESTS: Various data types in variables field
        VALIDATES: variables accepts Any type values
        ENSURES: Type flexibility for computed values and expressions
        """
        # Create module with various variable types
        module = Module(
            spice_template="MN {D} {G} {S} {B} nfet_03v3",
            variables={
                'string_var': 'computed_value',
                'numeric_var': 42,
                'float_var': 3.14,
                'bool_var': True,
                'list_var': [1, 2, 3],
                'dict_var': {'nested': 'value'}
            }
        )
        
        # Validate all variable types are preserved
        assert module.variables['string_var'] == 'computed_value'
        assert module.variables['numeric_var'] == 42
        assert module.variables['float_var'] == 3.14
        assert module.variables['bool_var'] is True
        assert module.variables['list_var'] == [1, 2, 3]
        assert module.variables['dict_var']['nested'] == 'value'


class TestVariablesFieldSchemaGeneration:
    """Test cases for variables field schema generation (P1.1 TDD)."""
    
    def test_schema_generation_includes_variables_field(self):
        """
        P1.1.6: Schema Generation Includes Variables Field
        TESTS: Generated schema includes variables field definition
        VALIDATES: Schema generation system recognizes variables field
        ENSURES: API documentation includes variables field
        
        NOTE: This test will need schema generation system to be updated.
        Currently testing that the field exists and is accessible.
        """
        # Create module with variables field
        module = Module(
            spice_template="MN {D} {G} {S} {B} nfet_03v3",
            variables={'gm': 'runtime_computed'}
        )
        
        # Validate variables field is accessible via attribute access
        assert hasattr(module, 'variables')
        assert module.variables is not None
        assert 'gm' in module.variables
        
        # TODO: Add actual schema generation test once schema_gen.py is updated
        # This validates the field exists and can be serialized
        import dataclasses
        fields = {f.name for f in dataclasses.fields(module)}
        assert 'variables' in fields


class TestVariablesOverrideValidation:
    """Test cases for variables override validation (P1.1 TDD)."""
    
    def test_variables_cannot_be_overridden_in_instances(self):
        """
        P1.1.7: Variables Cannot Be Overridden in Instances
        TESTS: Validation prevents variable overrides in instance parameters
        VALIDATES: Variables vs parameters distinction in override rules
        ENSURES: Variables remain module-local and not instance-configurable
        
        NOTE: This test defines expected validation behavior.
        Implementation will add validation to prevent this pattern.
        """
        # Define a hierarchical module with variables
        parent_module = Module(
            instances={
                'M1': Instance(
                    model='some_module_with_variables',
                    mappings={'in': 'sig_in', 'out': 'sig_out'},
                    parameters={'W': '2u'}  # Valid parameter override
                    # variables override should be prevented by validation
                )
            },
            variables={'design_variable': 'parent_value'}
        )
        
        # For now, just validate the module creates successfully
        # TODO: Add validation that prevents variables in Instance.parameters
        assert parent_module.variables is not None
        assert parent_module.variables['design_variable'] == 'parent_value'
        assert parent_module.instances['M1'].parameters['W'] == '2u'
        
        # Future validation should prevent this pattern:
        # Instance(parameters={'design_variable': 'override'})  # Should raise error
        
    def test_variables_field_immutable_through_instances(self):
        """
        P1.1.8: Variables Field Immutable Through Instances
        TESTS: Variables cannot be modified via instance parameter overrides
        VALIDATES: Clear separation of parameters (overridable) vs variables (computed)
        ENSURES: Design integrity maintained across instance boundaries
        """
        # Create module that will be instantiated
        sub_module = Module(
            spice_template="MN {D} {G} {S} {B} nfet_03v3 W={W}",
            parameters={'W': '1u'},  # Can be overridden
            variables={'computed_gm': 'formula_based'}  # Cannot be overridden
        )
        
        # Create parent module that instantiates sub_module
        parent_module = Module(
            instances={
                'M1': Instance(
                    model='sub_module',
                    mappings={'D': 'drain'},
                    parameters={'W': '2u'}  # Valid parameter override
                    # 'computed_gm' override should be invalid
                )
            }
        )
        
        # Validate instance parameter override works for parameters
        assert parent_module.instances['M1'].parameters['W'] == '2u'
        
        # Variables remain untouchable at the sub_module level
        assert sub_module.variables['computed_gm'] == 'formula_based'
        
        # TODO: Add validation preventing variables in instance parameters