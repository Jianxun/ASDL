# Known Bugs and Issues

## Critical Issues

### 1. Validator Logic Bug - Unused Component Detection ✅ FIXED
**File**: `src/asdl/validator.py:84-90`  
**Severity**: High  
**Status**: **RESOLVED**  
**Fixed Date**: 2025-08-20

**Problem**: The `validate_unused_components` method has duplicate conditions that cause all modules to be incorrectly categorized:

```python
for instance in module.instances.values():
    if instance.model in asdl_file.modules:
        # This is a device instance
        used_models.add(instance.model)
    elif instance.model in asdl_file.modules:  # <-- DUPLICATE CONDITION
        # This is a module instance  
        used_modules.add(instance.model)
```

**Impact**: 
- All instantiated modules get added to `used_models` but never to `used_modules`
- Causes false warnings like "Unused models: 'two_stage_buffer'" for top modules
- Causes false warnings for all hierarchically used modules

**Example Error**:
```
[WARNING V004]: Unused Models
Unused models detected: 'two_stage_buffer'. These models are defined but never instantiated.
[WARNING V005]: Unused Modules  
Unused modules detected: 'capacitor', 'current_mirror', 'inverter', 'nfet_03v3', 'pfet_03v3', 'rc_filter', 'resistor'. These modules are defined but never instantiated.
```

**Root Cause**: Copy-paste error in conditional logic

**Fix Applied**: Simplified logic to align with unified architecture - removed obsolete models/modules distinction and properly track used modules. Top module correctly excluded from unused warnings.

### 2. Legacy `models` Field References in Tests
**Files**: Multiple test files  
**Severity**: High  
**Status**: Identified  

**Problem**: Several test files access the obsolete `models` field that was removed during the unified architecture refactoring.

**Affected Files**:
- `tests/unit_tests/parser/test_models.py:37,38,78,80,85` - Accesses `asdl_file.models["name"]`
- `tests/integration/test_generator_pipeline.py:43,46` - Checks `asdl_file.models is not None` and counts models
- `tests/unit_tests/parser/test_location_tracking.py:61,62,66,67` - Accesses `asdl_file.models["name"]`  
- `tests/unit_tests/parser/test_basic_parsing.py:51` - Checks `asdl_file.models == {}`

**Impact**: 
- These tests will fail with `AttributeError: 'ASDLFile' object has no attribute 'models'`
- Breaks test suite functionality
- Tests are validating obsolete behavior

**Example Failures**:
```python
assert "nmos_test" in asdl_file.models  # AttributeError
model = asdl_file.models["nmos_test"]   # AttributeError
```

## Medium Priority Issues

### 3. Legacy `models:` Sections in YAML Files
**Files**: Multiple example and test YAML files  
**Severity**: Medium  
**Status**: Identified  

**Problem**: Many YAML files still contain obsolete `models: {}` sections that should be removed.

**Affected Files**:
- Examples: `diff_pair.yml`, `current_source.yml`, `common_source_amp.yml`, `two_stage_ota.yml`, `bias_gen.yml`
- Test fixtures: `inverter.yml`, `diff_pair_nmos.yml`, `inverter_reordered.yml`
- Documentation: Schema files in `doc/schema/`

**Impact**:
- Confusing to users following examples
- Inconsistent with current unified architecture
- May cause parser warnings/errors in strict mode

### 4. Serialization Still References Models
**File**: `src/asdl/serialization.py:52`  
**Severity**: Medium  
**Status**: Identified  

**Problem**: Serialization code still includes `'models': result['models']` in output.

**Impact**:
- May cause runtime errors if `models` field doesn't exist
- Outputs obsolete format
- Inconsistent with data structure design

## Low Priority Issues

### 5. Documentation References to Models
**Files**: Various documentation files  
**Severity**: Low  
**Status**: Identified  

**Problem**: Documentation still shows examples and references to the obsolete `models:` field.

**Affected Areas**:
- Import system documentation
- Schema documentation
- Example snippets

**Impact**:
- User confusion
- Outdated documentation

### Missing Parameter Override Validation ✅ FIXED
**File**: `src/asdl/cli/netlist.py:49-58`  
**Severity**: High  
**Status**: **RESOLVED**  
**Fixed Date**: 2025-08-20

**Problem**: The netlist CLI validation pipeline was missing parameter override validation, allowing forbidden parameter overrides on hierarchical modules to pass undetected.

**Impact**: 
- Parameter overrides on hierarchical modules (violating design rules) were not caught
- Could lead to LVS incompatible designs being generated
- Violated the parameter resolving system design principles

**Example**: `unified_architecture_demo.asdl` had parameter overrides on hierarchical modules (`inverter`, `rc_filter`) that should have triggered V301 errors but didn't.

**Fix Applied**: Added `validate_file_parameter_overrides(elaborated_file)` to the validation pipeline in netlist CLI.

## Resolution Priority

1. ✅ **COMPLETED**: Fix validator logic bug (#1) - breaks core functionality
2. ✅ **COMPLETED**: Fix missing parameter override validation - violates design rules
3. **High**: Fix test failures (#2) - breaks development workflow  
4. **Medium**: Clean up YAML files (#3) and serialization (#4)
5. **Low**: Update documentation (#5)

## Notes

- The unified architecture design correctly eliminated the separate `models` field in favor of using only the `modules` field
- The `test_unified_parsing.py` correctly tests rejection of `models` sections - this behavior should be preserved
- Some constructor calls with `models={}` parameters may still work if the dataclass accepts and ignores unknown fields