"""
Test cases for parser dual syntax support (P1.2 - TDD).

This test suite validates parser support for canonical and abbreviated field names
following TDD approach for parameter system enhancement Phase P1.2.

Tests are written before implementation to define expected parser behavior:
- Parse `parameters` OR `params` → store as `parameters`
- Parse `variables` OR `vars` → store as `variables`
- Validation warnings for using both forms in same module

These tests will initially fail until parser implementation is complete.
"""

import pytest
from src.asdl.parser import ASDLParser
from src.asdl.data_structures import ASDLFile, Module
from src.asdl.diagnostics import DiagnosticSeverity


class TestParameterVariableDualSyntax:
    """Test cases for dual syntax support in parser (P1.2 TDD)."""
    
    def test_parse_parameters_canonical_syntax(self):
        """
        P1.2.1: Parse Canonical Parameters Syntax
        TESTS: Parser handles `parameters` field correctly
        VALIDATES: Canonical syntax continues to work
        ENSURES: Backward compatibility maintained
        """
        yaml_content = """
file_info:
  top_module: "test"
modules:
  test_module:
    spice_template: "MN {D} {G} {S} {B} nfet_03v3 W={W} L={L}"
    parameters:
      W: "1u"
      L: "0.28u"
      M: "1"
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)
        
        # Should parse successfully without warnings
        assert asdl_file is not None
        assert len(diagnostics) == 0
        assert "test_module" in asdl_file.modules
        
        module = asdl_file.modules["test_module"]
        assert module.parameters is not None
        assert module.parameters["W"] == "1u"
        assert module.parameters["L"] == "0.28u"
        assert module.parameters["M"] == "1"
        
    def test_parse_params_abbreviated_syntax(self):
        """
        P1.2.2: Parse Abbreviated Parameters Syntax
        TESTS: Parser handles `params` field and stores as `parameters`
        VALIDATES: Abbreviated syntax is supported
        ENSURES: Internal storage always uses canonical name
        """
        yaml_content = """
file_info:
  top_module: "test"
modules:
  test_module:
    spice_template: "MN {D} {G} {S} {B} nfet_03v3 W={W} L={L}"
    params:
      W: "2u"
      L: "0.5u"
      M: "2"
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)
        
        # Should parse successfully without warnings
        assert asdl_file is not None
        assert len(diagnostics) == 0
        assert "test_module" in asdl_file.modules
        
        module = asdl_file.modules["test_module"]
        # Should be stored as 'parameters' regardless of input syntax
        assert module.parameters is not None
        assert module.parameters["W"] == "2u"
        assert module.parameters["L"] == "0.5u"
        assert module.parameters["M"] == "2"
        
    def test_parse_variables_canonical_syntax(self):
        """
        P1.2.3: Parse Canonical Variables Syntax
        TESTS: Parser handles `variables` field correctly
        VALIDATES: New variables field parsing works
        ENSURES: Variables field parsed and stored correctly
        """
        yaml_content = """
file_info:
  top_module: "test"
modules:
  test_module:
    spice_template: "MN {D} {G} {S} {B} nfet_03v3"
    variables:
      gm: "computed_runtime"
      vth: "0.7"
      id_sat: "formula_based"
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)
        
        # Should parse successfully without warnings
        assert asdl_file is not None
        assert len(diagnostics) == 0
        assert "test_module" in asdl_file.modules
        
        module = asdl_file.modules["test_module"]
        assert module.variables is not None
        assert module.variables["gm"] == "computed_runtime"
        assert module.variables["vth"] == "0.7"
        assert module.variables["id_sat"] == "formula_based"
        
    def test_parse_vars_abbreviated_syntax(self):
        """
        P1.2.4: Parse Abbreviated Variables Syntax
        TESTS: Parser handles `vars` field and stores as `variables`
        VALIDATES: Abbreviated syntax for variables is supported
        ENSURES: Internal storage always uses canonical name
        """
        yaml_content = """
file_info:
  top_module: "test"
modules:
  test_module:
    spice_template: "MN {D} {G} {S} {B} nfet_03v3"
    vars:
      computed_param: "runtime_value"
      design_var: "TBD"
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)
        
        # Should parse successfully without warnings
        assert asdl_file is not None
        assert len(diagnostics) == 0
        assert "test_module" in asdl_file.modules
        
        module = asdl_file.modules["test_module"]
        # Should be stored as 'variables' regardless of input syntax
        assert module.variables is not None
        assert module.variables["computed_param"] == "runtime_value"
        assert module.variables["design_var"] == "TBD"
        
    def test_parse_both_parameters_and_variables(self):
        """
        P1.2.5: Parse Both Parameters and Variables
        TESTS: Parser handles both fields in same module
        VALIDATES: Parameters and variables can coexist
        ENSURES: Correct separation of parameter vs variable data
        """
        yaml_content = """
file_info:
  top_module: "test"
modules:
  test_module:
    spice_template: "MN {D} {G} {S} {B} nfet_03v3 W={W}"
    parameters:
      W: "1u"
      L: "0.28u"
    variables:
      gm: "computed"
      vth: "measured"
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)
        
        # Should parse successfully without warnings
        assert asdl_file is not None
        assert len(diagnostics) == 0
        assert "test_module" in asdl_file.modules
        
        module = asdl_file.modules["test_module"]
        
        # Both fields should be present and distinct
        assert module.parameters is not None
        assert module.variables is not None
        
        assert module.parameters["W"] == "1u"
        assert module.parameters["L"] == "0.28u"
        assert len(module.parameters) == 2
        
        assert module.variables["gm"] == "computed"
        assert module.variables["vth"] == "measured"
        assert len(module.variables) == 2
        
    def test_parse_mixed_canonical_abbreviated_syntax(self):
        """
        P1.2.6: Parse Mixed Canonical and Abbreviated Syntax
        TESTS: Parser handles mix of canonical and abbreviated forms
        VALIDATES: Different field syntaxes can be used together
        ENSURES: Consistent internal storage regardless of input syntax
        """
        yaml_content = """
file_info:
  top_module: "test"
modules:
  test_module:
    spice_template: "MN {D} {G} {S} {B} nfet_03v3 W={W}"
    params:  # abbreviated
      W: "3u"
      L: "0.5u"
    variables:  # canonical
      gm: "computed_gm"
      design_margin: "10%"
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)
        
        # Should parse successfully without warnings
        assert asdl_file is not None
        assert len(diagnostics) == 0
        assert "test_module" in asdl_file.modules
        
        module = asdl_file.modules["test_module"]
        
        # Should be stored with canonical field names
        assert module.parameters is not None  # from 'params'
        assert module.variables is not None   # from 'variables'
        
        assert module.parameters["W"] == "3u"
        assert module.parameters["L"] == "0.5u"
        assert module.variables["gm"] == "computed_gm"
        assert module.variables["design_margin"] == "10%"


class TestDualSyntaxValidationWarnings:
    """Test cases for validation warnings with dual syntax (P1.2 TDD)."""
    
    def test_warning_both_parameters_and_params(self):
        """
        P1.2.7: Warning for Both parameters and params
        TESTS: Parser generates warning when both forms used
        VALIDATES: Ambiguous syntax detection works
        ENSURES: Clear guidance for users about syntax conflicts
        """
        yaml_content = """
file_info:
  top_module: "test"
modules:
  test_module:
    spice_template: "MN {D} {G} {S} {B} nfet_03v3"
    parameters:
      W: "1u"
    params:
      L: "0.28u"
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)
        
        # Should parse but generate warning
        assert asdl_file is not None
        assert len(diagnostics) == 1
        
        # Check warning details
        warning = diagnostics[0]
        assert warning.severity == DiagnosticSeverity.WARNING
        assert "parameters" in warning.details.lower()
        assert "params" in warning.details.lower()
        assert "both" in warning.details.lower()
        
        # Should merge both fields into parameters
        module = asdl_file.modules["test_module"]
        assert module.parameters is not None
        # Implementation should merge or choose one (behavior to be defined)
        
    def test_warning_both_variables_and_vars(self):
        """
        P1.2.8: Warning for Both variables and vars
        TESTS: Parser generates warning when both forms used
        VALIDATES: Ambiguous syntax detection works for variables
        ENSURES: Consistent warning behavior across field types
        """
        yaml_content = """
file_info:
  top_module: "test"
modules:
  test_module:
    spice_template: "MN {D} {G} {S} {B} nfet_03v3"
    variables:
      gm: "computed"
    vars:
      vth: "measured"
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)
        
        # Should parse but generate warning
        assert asdl_file is not None
        assert len(diagnostics) == 1
        
        # Check warning details
        warning = diagnostics[0]
        assert warning.severity == DiagnosticSeverity.WARNING
        assert "variables" in warning.details.lower()
        assert "vars" in warning.details.lower()
        assert "both" in warning.details.lower()
        
        # Should merge both fields into variables
        module = asdl_file.modules["test_module"]
        assert module.variables is not None
        # Implementation should merge or choose one (behavior to be defined)
        
    def test_no_warning_different_modules(self):
        """
        P1.2.9: No Warning for Different Modules
        TESTS: No warning when different modules use different syntax
        VALIDATES: Module-scope validation (not file-scope)
        ENSURES: Different modules can use different syntax preferences
        """
        yaml_content = """
file_info:
  top_module: "test"
modules:
  module1:
    spice_template: "MN1 {D} {G} {S} {B} nfet_03v3"
    parameters:  # canonical
      W: "1u"
  module2:
    spice_template: "MN2 {D} {G} {S} {B} nfet_03v3"
    params:  # abbreviated
      W: "2u"
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)
        
        # Should parse without warnings (different modules)
        assert asdl_file is not None
        assert len(diagnostics) == 0
        
        # Both modules should parse correctly
        assert "module1" in asdl_file.modules
        assert "module2" in asdl_file.modules
        assert asdl_file.modules["module1"].parameters["W"] == "1u"
        assert asdl_file.modules["module2"].parameters["W"] == "2u"


class TestInstanceParameterDualSyntax:
    """Test cases for dual syntax in instance parameters (P1.2 TDD)."""
    
    def test_instance_parameters_canonical(self):
        """
        P1.2.10: Instance Parameters Canonical Syntax
        TESTS: Instance parameters field works
        VALIDATES: Instance-level parameter syntax consistent
        ENSURES: Instance parameter overrides work with canonical syntax
        """
        yaml_content = """
file_info:
  top_module: "test"
modules:
  test_module:
    instances:
      M1:
        model: "nmos_unit"
        mappings:
          D: "drain"
        parameters:
          W: "2u"
          M: "4"
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)
        
        assert asdl_file is not None
        assert len(diagnostics) == 0
        
        module = asdl_file.modules["test_module"]
        instance = module.instances["M1"]
        assert instance.parameters is not None
        assert instance.parameters["W"] == "2u"
        assert instance.parameters["M"] == "4"
        
    def test_instance_params_abbreviated(self):
        """
        P1.2.11: Instance Parameters Abbreviated Syntax
        TESTS: Instance params field works and stores as parameters
        VALIDATES: Instance-level abbreviated syntax support
        ENSURES: Consistent behavior between module and instance levels
        """
        yaml_content = """
file_info:
  top_module: "test"
modules:
  test_module:
    instances:
      M1:
        model: "nmos_unit"
        mappings:
          D: "drain"
        params:  # abbreviated syntax
          W: "3u"
          M: "2"
"""
        parser = ASDLParser()
        asdl_file, diagnostics = parser.parse_string(yaml_content)
        
        assert asdl_file is not None
        assert len(diagnostics) == 0
        
        module = asdl_file.modules["test_module"]
        instance = module.instances["M1"]
        # Should be stored as 'parameters' regardless of input syntax
        assert instance.parameters is not None
        assert instance.parameters["W"] == "3u"
        assert instance.parameters["M"] == "2"