# Known Bugs and Issues

## Critical Issues

### Variable Resolution Missing in Elaborator
**File**: `src/asdl/elaborator.py`  
**Severity**: High  
**Status**: Identified  
**Date**: 2025-08-20

**Problem**: Variable references in instance parameters are not being resolved during elaboration, causing literal variable names to appear in generated SPICE instead of their concrete values.

**Impact**: 
- Generated SPICE contains literal variable names instead of values
- Example: `m=nmos_M` instead of `m=1` in primitive device instances
- Breaks SPICE simulation as variable names are not valid parameter values
- Violates the parameter resolving system design where variables should be resolved at compile time

**Example Issue**:
```yaml
inverter:
  variables:
    nmos_M: 1
  instances:
    MN:
      parameters: {M: nmos_M}  # Should resolve to M: 1
```

**Generated SPICE (incorrect)**:
```spice
XMN out in vss vss nfet_03v3 L=0.28u W=3u m=nmos_M  # ❌ Literal variable name
```

**Expected SPICE**:
```spice  
XMN out in vss vss nfet_03v3 L=0.28u W=3u m=1  # ✅ Resolved value
```

**Root Cause**: The elaborator doesn't handle variable resolution - it only handles pattern expansion. Variable references in instance parameters are passed through unresolved to the generator.

**Solution Needed**: Enhance elaborator to resolve variable references in instance parameters using the parent module's `variables` field during the elaboration phase.

## High Priority Issues

### Legacy `models` Field References in Tests
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

### Legacy `models:` Sections in YAML Files
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

### Serialization Still References Models
**File**: `src/asdl/serialization.py:52`  
**Severity**: Medium  
**Status**: Identified  

**Problem**: Serialization code still includes `'models': result['models']` in output.

**Impact**:
- May cause runtime errors if `models` field doesn't exist
- Outputs obsolete format
- Inconsistent with data structure design

## Low Priority Issues

### Documentation References to Models
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

## Resolution Priority

1. **Critical**: Fix variable resolution in elaborator - breaks SPICE generation
2. **High**: Fix test failures - breaks development workflow  
3. **Medium**: Clean up YAML files and serialization
4. **Low**: Update documentation

## Recently Fixed Issues ✅

### 1. Validator Logic Bug - Unused Component Detection ✅ FIXED
**Status**: **RESOLVED** (2025-08-20)
- Fixed duplicate condition logic in `validate_unused_components()`
- Simplified logic to align with unified architecture

### 2. Missing Parameter Override Validation ✅ FIXED  
**Status**: **RESOLVED** (2025-08-20)
- Added `validate_file_parameter_overrides()` to CLI validation pipeline
- Now properly catches V301 errors for hierarchical parameter overrides

### 3. Missing Module Parameter Field Validation ✅ FIXED
**Status**: **RESOLVED** (2025-08-20)  
- Added V304 validation rule preventing hierarchical modules from declaring `parameters`
- Enforces parameter resolving system design rules

### 4. Missing Location Information in Diagnostics ✅ FIXED
**Status**: **RESOLVED** (2025-08-20)
- All validation errors now include precise file:line:column locations
- Format: `at unified_architecture_demo.asdl:148:7`

## Notes

- The unified architecture design correctly eliminated the separate `models` field in favor of using only the `modules` field
- The `test_unified_parsing.py` correctly tests rejection of `models` sections - this behavior should be preserved
- Validation pipeline is now complete with comprehensive rule coverage and location information