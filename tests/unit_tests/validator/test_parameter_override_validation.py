"""
Test cases for parameter override validation (P1.3 - TDD).

This test suite validates parameter override rules following TDD approach 
for parameter system enhancement Phase P1.3.

Tests are written before implementation to define expected validation behavior:
- Parameter overrides only allowed for primitive modules (spice_template present)
- Error for parameter overrides on hierarchical modules (instances present)
- Error for any variable override attempts
- Comprehensive validation for both local and imported module scenarios

These tests will initially fail until validator implementation is complete.
"""

import pytest
from src.asdl.validator import ASDLValidator
from src.asdl.data_structures import (
    Instance, Module, Port, PortDirection, SignalType, ASDLFile, FileInfo
)
from src.asdl.diagnostics import Diagnostic, DiagnosticSeverity


class TestParameterOverrideValidation:
    """Test cases for parameter override validation rules (P1.3 TDD)."""
    
    def test_primitive_module_parameter_override_allowed(self):
        """
        P1.3.1: Primitive Module Parameter Override Allowed
        TESTS: Parameter overrides allowed for primitive modules (spice_template present)
        VALIDATES: Core rule - primitives can have parameter overrides
        ENSURES: Valid use case works without errors
        """
        validator = ASDLValidator()
        
        # Create primitive module (has spice_template)
        primitive_module = Module(
            spice_template="MN {D} {G} {S} {B} nfet_03v3 W={W} L={L}",
            pdk="gf180mcu",
            parameters={'W': '1u', 'L': '0.28u', 'M': '1'},
            ports={
                'D': Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
                'G': Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                'S': Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
                'B': Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE)
            }
        )
        
        # Create instance that overrides parameters
        instance = Instance(
            model="nmos_primitive",
            mappings={'D': 'drain', 'G': 'gate', 'S': 'source', 'B': 'bulk'},
            parameters={'W': '2u', 'M': '4'}  # Valid parameter overrides
        )
        
        # Validation should pass - no diagnostics returned
        diagnostics = validator.validate_parameter_overrides("M1", instance, primitive_module)
        assert len(diagnostics) == 0
        
    def test_hierarchical_module_parameter_override_error(self):
        """
        P1.3.2: Hierarchical Module Parameter Override Error
        TESTS: Parameter overrides rejected for hierarchical modules (instances present)
        VALIDATES: Core rule - hierarchical modules cannot have parameter overrides
        ENSURES: Invalid use case generates clear error
        """
        validator = ASDLValidator()
        
        # Create hierarchical module (has instances)
        hierarchical_module = Module(
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
            },
            parameters={'drive_strength': '1X'},  # Module-level parameters are OK
            ports={
                'in': Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                'out': Port(dir=PortDirection.OUT, type=SignalType.VOLTAGE),
                'vdd': Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
                'vss': Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE)
            }
        )
        
        # Create instance that tries to override parameters (invalid)
        instance = Instance(
            model="inverter_hierarchical",
            mappings={'in': 'input_sig', 'out': 'output_sig'},
            parameters={'drive_strength': '2X'}  # Invalid - trying to override hierarchical module
        )
        
        # Validation should fail - generate error diagnostic
        diagnostics = validator.validate_parameter_overrides("INV1", instance, hierarchical_module)
        assert len(diagnostics) == 1
        
        error = diagnostics[0]
        assert error.severity == DiagnosticSeverity.ERROR
        assert error.code == "V301"
        assert "hierarchical" in error.details.lower()
        assert "parameter override" in error.details.lower()
        assert "INV1" in error.details
        
    def test_variable_override_always_error(self):
        """
        P1.3.3: Variable Override Always Error
        TESTS: Variable overrides rejected for all module types
        VALIDATES: Variables are never overridable (primitive or hierarchical)
        ENSURES: Variable immutability enforced consistently
        """
        validator = ASDLValidator()
        
        # Test with primitive module first
        primitive_module = Module(
            spice_template="MN {D} {G} {S} {B} nfet_03v3",
            parameters={'W': '1u'},
            variables={'gm': 'computed', 'vth': '0.7'}  # Module has variables
        )
        
        # Create instance trying to override variables (invalid)
        instance = Instance(
            model="nmos_with_vars",
            mappings={'D': 'drain'},
            parameters={'W': '2u'},  # Valid parameter override
            # Note: In real implementation, we need to detect variable override attempts
            # This could be done by checking if instance parameters contain variable names
        )
        
        # For this test, we simulate variable override attempt detection
        # Implementation should check if any instance.parameters keys match module.variables keys
        diagnostics = validator.validate_parameter_overrides("M1", instance, primitive_module)
        
        # Should pass since no variable override attempted in this example
        assert len(diagnostics) == 0
        
        # Now test actual variable override attempt
        instance_with_var_override = Instance(
            model="nmos_with_vars",
            mappings={'D': 'drain'},
            parameters={
                'W': '2u',      # Valid parameter override
                'gm': 'override_attempt',  # Invalid - trying to override variable
                'vth': '0.8'    # Invalid - trying to override variable
            }
        )
        
        diagnostics = validator.validate_parameter_overrides("M2", instance_with_var_override, primitive_module)
        assert len(diagnostics) == 2  # Two variable override errors
        
        for diagnostic in diagnostics:
            assert diagnostic.severity == DiagnosticSeverity.ERROR
            assert diagnostic.code == "V302"
            assert "variable" in diagnostic.details.lower()
            assert "override" in diagnostic.details.lower()
            
    def test_empty_parameter_override_valid(self):
        """
        P1.3.4: Empty Parameter Override Valid
        TESTS: Instances without parameter overrides are always valid
        VALIDATES: No parameter overrides should never trigger validation errors
        ENSURES: Default case works for all module types
        """
        validator = ASDLValidator()
        
        # Test with primitive module
        primitive_module = Module(
            spice_template="MN {D} {G} {S} {B} nfet_03v3",
            parameters={'W': '1u', 'L': '0.28u'}
        )
        
        instance_no_params = Instance(
            model="nmos_primitive",
            mappings={'D': 'drain', 'G': 'gate'}
            # No parameters field - should be valid
        )
        
        diagnostics = validator.validate_parameter_overrides("M1", instance_no_params, primitive_module)
        assert len(diagnostics) == 0
        
        # Test with hierarchical module
        hierarchical_module = Module(
            instances={'M1': Instance(model='sub', mappings={'a': 'b'})},
            parameters={'size': 'large'}
        )
        
        instance_no_params_hier = Instance(
            model="hierarchical_module",
            mappings={'in': 'input'}
            # No parameters field - should be valid
        )
        
        diagnostics = validator.validate_parameter_overrides("TOP1", instance_no_params_hier, hierarchical_module)
        assert len(diagnostics) == 0
        
    def test_parameter_override_validation_comprehensive(self):
        """
        P1.3.5: Comprehensive Parameter Override Validation
        TESTS: Complex scenarios with multiple parameter and variable overrides
        VALIDATES: Validation correctly handles mixed valid/invalid overrides
        ENSURES: Detailed error reporting for complex cases
        """
        validator = ASDLValidator()
        
        # Create module with both parameters and variables
        mixed_module = Module(
            spice_template="MN {D} {G} {S} {B} nfet_03v3 W={W} L={L}",
            parameters={
                'W': '1u',      # Can be overridden
                'L': '0.28u',   # Can be overridden
                'M': '1'        # Can be overridden
            },
            variables={
                'gm': 'computed_gm',     # Cannot be overridden
                'vth': '0.7',            # Cannot be overridden
                'design_margin': '10%'   # Cannot be overridden
            }
        )
        
        # Create instance with mixed valid/invalid overrides
        instance_mixed = Instance(
            model="mixed_module",
            mappings={'D': 'drain'},
            parameters={
                'W': '3u',              # Valid - parameter override
                'L': '0.5u',            # Valid - parameter override  
                'gm': 'override_gm',    # Invalid - variable override
                'vth': '0.8',           # Invalid - variable override
                'M': '2'                # Valid - parameter override
            }
        )
        
        diagnostics = validator.validate_parameter_overrides("MIXED1", instance_mixed, mixed_module)
        
        # Should have exactly 2 errors (for the 2 variable overrides)
        assert len(diagnostics) == 2
        
        # Check that both variable override errors are reported
        error_details = [d.details for d in diagnostics]
        assert any('gm' in detail for detail in error_details)
        assert any('vth' in detail for detail in error_details)
        
        # All errors should be variable override errors
        for diagnostic in diagnostics:
            assert diagnostic.severity == DiagnosticSeverity.ERROR
            assert diagnostic.code == "V302"
            assert "variable" in diagnostic.details.lower()


class TestParameterOverrideValidationEdgeCases:
    """Test cases for edge cases in parameter override validation (P1.3 TDD)."""
    
    def test_module_without_parameters_or_variables(self):
        """
        P1.3.6: Module Without Parameters or Variables
        TESTS: Validation handles modules with no parameters/variables
        VALIDATES: Edge case with empty parameter/variable sets
        ENSURES: No false positives for modules without configurable fields
        """
        validator = ASDLValidator()
        
        # Create primitive module without parameters or variables
        minimal_module = Module(
            spice_template="V{name} {plus} {minus} DC {voltage}",
            # No parameters or variables defined
        )
        
        # Instance attempting parameter override on module with no parameters
        instance_with_params = Instance(
            model="voltage_source",
            mappings={'plus': 'vdd', 'minus': 'gnd'},
            parameters={'voltage': '1.8'}  # Module has no parameters to override
        )
        
        # Should generate error for attempting to override non-existent parameters
        diagnostics = validator.validate_parameter_overrides("V1", instance_with_params, minimal_module)
        assert len(diagnostics) == 1
        
        error = diagnostics[0]
        assert error.severity == DiagnosticSeverity.ERROR
        assert error.code == "V303"
        assert "no parameters" in error.details.lower()
        
    def test_case_sensitive_parameter_variable_names(self):
        """
        P1.3.7: Case Sensitive Parameter/Variable Names
        TESTS: Parameter/variable name matching is case sensitive
        VALIDATES: Exact name matching prevents false positives
        ENSURES: Case differences don't trigger incorrect validation errors
        """
        validator = ASDLValidator()
        
        module = Module(
            spice_template="MN {D} {G} {S} {B} nfet_03v3",
            parameters={'Width': '1u', 'Length': '0.28u'},  # Capitalized
            variables={'Gm': 'computed', 'Vth': '0.7'}       # Capitalized
        )
        
        # Instance with lowercase parameter names (should be treated as new parameters)
        instance = Instance(
            model="case_test",
            mappings={'D': 'drain'},
            parameters={
                'width': '2u',    # Different case from 'Width' - not an override
                'length': '0.5u', # Different case from 'Length' - not an override
                'gm': 'override', # Different case from 'Gm' - not a variable override
            }
        )
        
        # Should generate error for attempting to set non-existent parameters
        diagnostics = validator.validate_parameter_overrides("CASE1", instance, module)
        assert len(diagnostics) == 3  # Three unrecognized parameter names
        
        for diagnostic in diagnostics:
            assert diagnostic.severity == DiagnosticSeverity.ERROR
            assert diagnostic.code == "V303"  # Unrecognized parameter
            
    def test_parameter_override_with_none_values(self):
        """
        P1.3.8: Parameter Override with None Values
        TESTS: Validation handles None values in parameters/variables
        VALIDATES: None values don't cause validation errors
        ENSURES: Optional parameter handling works correctly
        """
        validator = ASDLValidator()
        
        module = Module(
            spice_template="MN {D} {G} {S} {B} nfet_03v3",
            parameters=None,  # Module has no parameters
            variables=None    # Module has no variables
        )
        
        instance = Instance(
            model="none_test",
            mappings={'D': 'drain'},
            parameters=None   # Instance has no parameter overrides
        )
        
        # Should pass validation - no overrides attempted
        diagnostics = validator.validate_parameter_overrides("NONE1", instance, module)
        assert len(diagnostics) == 0


class TestParameterOverrideValidationIntegration:
    """Integration tests for parameter override validation (P1.3 TDD)."""
    
    def test_full_asdl_file_parameter_validation(self):
        """
        P1.3.9: Full ASDL File Parameter Validation
        TESTS: Parameter override validation works on complete ASDL file
        VALIDATES: Integration with full file validation pipeline
        ENSURES: End-to-end parameter override validation works
        """
        validator = ASDLValidator()
        
        # Create complete ASDL file with multiple modules
        asdl_file = ASDLFile(
            file_info=FileInfo(top_module="test_top"),
            modules={
                'nmos_primitive': Module(
                    spice_template="MN {D} {G} {S} {B} nfet_03v3 W={W}",
                    parameters={'W': '1u'},
                    variables={'gm': 'computed'}
                ),
                'inverter_hierarchical': Module(
                    instances={
                        'MP': Instance(model='pmos_unit', mappings={'D': 'out'}),
                        'MN': Instance(model='nmos_unit', mappings={'D': 'out'})
                    },
                    parameters={'drive': '1X'}
                ),
                'test_top': Module(
                    instances={
                        'M1': Instance(
                            model='nmos_primitive',
                            mappings={'D': 'drain'},
                            parameters={'W': '2u'}  # Valid - primitive module
                        ),
                        'INV1': Instance(
                            model='inverter_hierarchical', 
                            mappings={'in': 'sig'},
                            parameters={'drive': '2X'}  # Invalid - hierarchical module
                        ),
                        'M2': Instance(
                            model='nmos_primitive',
                            mappings={'D': 'drain2'},
                            parameters={'gm': 'override'}  # Invalid - variable override
                        )
                    }
                )
            }
        )
        
        # Validate parameter overrides across entire file
        all_diagnostics = validator.validate_file_parameter_overrides(asdl_file)
        
        # Should find 2 errors: hierarchical override + variable override
        assert len(all_diagnostics) == 2
        
        # Check for hierarchical module override error
        hierarchical_errors = [d for d in all_diagnostics if d.code == "V301"]
        assert len(hierarchical_errors) == 1
        assert "INV1" in hierarchical_errors[0].details
        
        # Check for variable override error  
        variable_errors = [d for d in all_diagnostics if d.code == "V302"]
        assert len(variable_errors) == 1
        assert "M2" in variable_errors[0].details
        assert "gm" in variable_errors[0].details