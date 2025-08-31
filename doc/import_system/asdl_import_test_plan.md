# ASDL Import System Test Plan

## Overview

This document outlines the comprehensive test strategy for the ASDL import system development. Tests are organized by implementation phases, with each test case designed to validate specific architectural decisions and ensure system robustness.

**Testing Philosophy**: Test-driven development with aggressive refactoring for clean architecture. No backward compatibility constraints during MVP phase.

## Phase 0: Unified Module Architecture (Foundation)

### **Data Structure Unification Tests**

#### **T0.1: Unified Module Class Architecture**
**File**: `tests/unit_tests/data_structures/test_unified_module.py`

**T0.1.1: Primitive Module Creation**
```python
def test_primitive_module_creation(self):
    """
    TESTS: Basic primitive module instantiation with spice_template
    VALIDATES: Module can represent PDK primitives (former DeviceModel functionality)
    ENSURES: spice_template field works correctly for inline SPICE generation
    """
```

**T0.1.2: Hierarchical Module Creation**
```python
def test_hierarchical_module_creation(self):
    """
    TESTS: Hierarchical module instantiation with instances
    VALIDATES: Module can represent circuit hierarchies (existing Module functionality)
    ENSURES: instances field works correctly for subcircuit generation
    """
```

**T0.1.3: Module Type Classification**
```python
def test_module_type_classification(self):
    """
    TESTS: is_primitive() and is_hierarchical() methods
    VALIDATES: Clear distinction between primitive and hierarchical modules
    ENSURES: No ambiguity in module classification for SPICE generation
    """
```

**T0.1.4: Mutual Exclusion Enforcement**
```python
def test_spice_template_instances_mutual_exclusion(self):
    """
    TESTS: Cannot have both spice_template and instances fields
    VALIDATES: Architectural constraint preventing hybrid modules
    ENSURES: Clear separation between primitive and hierarchical semantics
    """
```

**T0.1.5: PDK Field Integration**
```python
def test_pdk_field_for_include_generation(self):
    """
    TESTS: pdk field on primitive modules
    VALIDATES: PDK information preserved for .include statement generation
    ENSURES: Technology information flows to SPICE generation phase
    """
```

#### **T0.2: ASDLFile Structure Simplification**
**File**: `tests/unit_tests/data_structures/test_unified_asdl_file.py`

**T0.2.1: Models Section Elimination**
```python
def test_no_models_field_exists(self):
    """
    TESTS: ASDLFile has no models field
    VALIDATES: Complete elimination of DeviceModel/Module redundancy
    ENSURES: Single unified representation reduces parser complexity
    """
```

**T0.2.2: Unified Modules Section**
```python
def test_modules_contains_both_types(self):
    """
    TESTS: modules field contains both primitive and hierarchical modules
    VALIDATES: Single namespace for all component types
    ENSURES: Simplified import resolution (no type-specific lookups)
    """
```

**T0.2.3: Module Reference Resolution**
```python
def test_instance_model_references(self):
    """
    TESTS: Instance.model references work for unified modules
    VALIDATES: Instance can reference both primitive and hierarchical modules
    ENSURES: No special handling needed for different module types
    """
```

#### **T0.3: Import Declaration Foundation**
**File**: `tests/unit_tests/data_structures/test_import_declarations.py`

**T0.3.1: Import Declaration Structure**
```python
def test_import_declaration_basic_structure(self):
    """
    TESTS: ImportDeclaration data structure creation
    VALIDATES: Foundation for alias: library.filename syntax
    ENSURES: Clean structure for future import resolution
    """
```

**T0.3.2: Qualified Source Parsing**
```python
def test_qualified_source_format(self):
    """
    TESTS: library.filename format validation
    VALIDATES: Clear resolution rules for import targets
    ENSURES: Unambiguous file path resolution
    """
```

**T0.3.3: Version Tag Support**
```python
def test_version_tag_parsing(self):
    """
    TESTS: Optional @version tag in imports
    VALIDATES: Foundation for version-specific imports
    ENSURES: Reproducible builds with version constraints
    """
```

### **Parser Refactoring Tests**

#### **T0.4: Parser Simplification**
**File**: `tests/unit_tests/parser/test_unified_parsing.py`

**T0.4.1: Models Section Rejection**
```python
def test_models_section_rejected(self):
    """
    TESTS: Parser rejects ASDL files with models section
    VALIDATES: Clean break from legacy format
    ENSURES: No ambiguity about supported format
    """
```

**T0.4.2: Unified Module Parsing**
```python
def test_unified_module_parsing(self):
    """
    TESTS: Single parsing path for all module types
    VALIDATES: Simplified parser logic without type-specific branches
    ENSURES: Consistent parsing behavior regardless of module type
    """
```

**T0.4.3: Mutual Exclusion Validation**
```python
def test_parser_enforces_mutual_exclusion(self):
    """
    TESTS: Parser validates spice_template XOR instances constraint
    VALIDATES: Early error detection for malformed modules
    ENSURES: Clear diagnostic messages for constraint violations
    """
```

**T0.4.4: Import Section Parsing Foundation**
```python
def test_imports_section_parsing(self):
    """
    TESTS: Basic imports section recognition and parsing
    VALIDATES: Foundation for import system syntax
    ENSURES: Proper data structure population for import resolution
    """
```

### **Generator Unification Tests**

#### **T0.5: SPICE Generation Unification**
**File**: `tests/unit_tests/generator/test_unified_generation.py`

**T0.5.1: Primitive Module SPICE Generation**
```python
def test_primitive_module_inline_generation(self):
    """
    TESTS: Modules with spice_template generate inline SPICE
    VALIDATES: Former DeviceModel SPICE generation preserved
    ENSURES: No subcircuit overhead for primitive devices
    """
```

**T0.5.2: Hierarchical Module SPICE Generation**
```python
def test_hierarchical_module_subcircuit_generation(self):
    """
    TESTS: Modules with instances generate .subckt definitions
    VALIDATES: Existing Module SPICE generation preserved
    ENSURES: Proper hierarchical netlisting
    """
```

**T0.5.3: PDK Include Generation**
```python
def test_pdk_include_statement_generation(self):
    """
    TESTS: PDK field drives .include statement generation
    VALIDATES: Technology integration with unified architecture
    ENSURES: Proper model file inclusion in generated SPICE
    """
```

**T0.5.4: Generator Type Detection**
```python
def test_generator_detects_module_type(self):
    """
    TESTS: Generator correctly identifies primitive vs hierarchical modules
    VALIDATES: Unified generator logic with type-specific output
    ENSURES: Correct SPICE format selection based on module content
    """
```

### **Validation and Error Handling Tests**

#### **T0.6: Core Validation Logic**
**File**: `tests/unit_tests/validator/test_unified_validation.py`

**T0.6.1: Module Completeness Validation**
```python
def test_module_must_have_implementation(self):
    """
    TESTS: Modules must have either spice_template or instances
    VALIDATES: No empty/incomplete module definitions
    ENSURES: All modules can generate valid SPICE
    """
```

**T0.6.2: Primitive Module Validation**
```python
def test_primitive_module_validation(self):
    """
    TESTS: spice_template format and parameter consistency
    VALIDATES: Template syntax and placeholder validation
    ENSURES: Valid SPICE generation from templates
    """
```

**T0.6.3: Hierarchical Module Validation**
```python
def test_hierarchical_module_validation(self):
    """
    TESTS: Instance references and port mappings
    VALIDATES: Existing Module validation logic preserved
    ENSURES: Valid subcircuit definitions
    """
```

**T0.6.4: Cross-Reference Validation**
```python
def test_instance_model_reference_validation(self):
    """
    TESTS: Instance.model references exist in modules section
    VALIDATES: No dangling references in unified namespace
    ENSURES: All instance models are resolvable
    """
```

### **Migration and Integration Tests**

#### **T0.7: Format Migration Validation**
**File**: `tests/integration/test_format_migration.py`

**T0.7.1: Legacy Format Rejection**
```python
def test_legacy_asdl_files_rejected(self):
    """
    TESTS: Existing ASDL files with models section fail parsing
    VALIDATES: Clean migration enforcement
    ENSURES: No silent format mixing
    """
```

**T0.7.2: Migrated Format Acceptance**
```python
def test_migrated_asdl_files_accepted(self):
    """
    TESTS: Converted ASDL files parse and generate correctly
    VALIDATES: Migration preserves functionality
    ENSURES: No regression in circuit representation
    """
```

**T0.7.3: End-to-End Pipeline**
```python
def test_unified_pipeline_functionality(self):
    """
    TESTS: Complete parse ’ elaborate ’ generate pipeline
    VALIDATES: All components work together with unified architecture
    ENSURES: System-level functionality preservation
    """
```

#### **T0.8: Regression Prevention**
**File**: `tests/integration/test_unified_regression.py`

**T0.8.1: Generated SPICE Equivalence**
```python
def test_spice_output_equivalence(self):
    """
    TESTS: Migrated designs generate equivalent SPICE netlists
    VALIDATES: No functional regression from architectural change
    ENSURES: Circuit behavior preservation
    """
```

**T0.8.2: Parameter Resolution Preservation**
```python
def test_parameter_resolution_unified(self):
    """
    TESTS: Parameter resolution works across unified modules
    VALIDATES: Existing parameter system integration
    ENSURES: Design parameterization still functional
    """
```

**T0.8.3: Pattern Expansion Compatibility**
```python
def test_pattern_expansion_unified(self):
    """
    TESTS: Existing pattern expansion works with unified modules
    VALIDATES: Pattern system integration preserved
    ENSURES: Bus and array generation still functional
    """
```

## Test Execution Strategy

### **Phase 0 Test Order**
1. **Data Structure Tests** (T0.1-T0.3): Foundation validation
2. **Parser Tests** (T0.4): Input handling validation  
3. **Generator Tests** (T0.5): Output generation validation
4. **Validation Tests** (T0.6): Error detection validation
5. **Integration Tests** (T0.7-T0.8): System-level validation

### **Success Criteria**
- All new unified tests pass
- Generated SPICE output equivalent to original system
- No functional regression in existing designs
- Clean elimination of DeviceModel/Module redundancy

### **Risk Mitigation**
- Comprehensive regression testing with existing designs
- SPICE output comparison for functional equivalence
- Incremental implementation with test feedback loops

---

**Note**: This test plan will be extended in subsequent phases to cover import resolution, library management, and advanced import features.