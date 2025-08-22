# Parser Error Codes (XCCSS Format)

## Overview

This document defines the complete set of parser diagnostic codes for the ASDL system using the XCCSS format (`XCCSS` where X=Component, CC=Category, SS=Specific Code).

**Current Status**: 8/15 MVP critical codes implemented, 7 missing for production readiness.

## MVP Critical Errors (Must Implement First)

These 15 codes prevent compilation-breaking errors and silent data corruption:

### **01 - YAML Syntax Errors** (All Implemented )

#### P0101: Invalid YAML Syntax 
- **Severity**: Error
- **Current**: Implemented
- **Details**: File cannot be parsed due to YAML syntax violations
- **Example**: Missing colons, invalid indentation, malformed structures
- **Test**: Verify parser rejects malformed YAML with precise error location

#### P0102: Invalid Root Type   
- **Severity**: Error
- **Current**: Implemented
- **Details**: Root must be dictionary, not list or scalar
- **Example**: `- file_info: ...` (starts with list)
- **Test**: Verify rejection of non-dictionary root with helpful suggestion

### **02 - Schema Structure Errors** 

#### P0201: Missing Required Section 
- **Severity**: Error
- **Current**: Implemented
- **Details**: Mandatory `file_info` section missing
- **Example**: File with only `modules:` section
- **Test**: Verify error when file_info absent

#### P0202: Invalid Section Type 
- **Severity**: Error  
- **Current**: Implemented
- **Details**: Section must be dictionary/mapping type
- **Example**: `modules: "not_a_dict"`
- **Test**: Verify type validation for all major sections

#### P0232: Duplicate Module Name L **MISSING - HIGH PRIORITY**
- **Severity**: Error
- **Current**: **Not Implemented**
- **Details**: Module names must be unique within file
- **Example**: Two modules named `inverter`
- **Implementation**: Add duplicate detection in `_parse_modules()`
- **Test**: Verify error on duplicate module names with both locations

### **03 - Semantic Logic Errors**

#### P0230: Module Type Conflict 
- **Severity**: Error
- **Current**: Implemented (P107)
- **Details**: Module cannot have both `spice_template` and `instances`
- **Example**: Module with both primitive and hierarchical definitions
- **Test**: Verify mutual exclusivity enforcement

#### P0231: Incomplete Module Definition 
- **Severity**: Error
- **Current**: Implemented (P108) 
- **Details**: Module must have either `spice_template` or `instances`
- **Example**: Module with neither primitive nor hierarchical definition
- **Test**: Verify completeness requirement

#### P0240: Missing Port Direction 
- **Severity**: Error
- **Current**: Implemented (P104)
- **Details**: Port must specify `dir` field
- **Example**: `port1: {type: voltage}` (missing dir)
- **Test**: Verify required field validation

#### P0241: Missing Port Type 
- **Severity**: Error  
- **Current**: Implemented (P104)
- **Details**: Port must specify `type` field
- **Example**: `port1: {dir: in}` (missing type)
- **Test**: Verify required field validation

#### P0242: Duplicate Port Name L **MISSING - HIGH PRIORITY**
- **Severity**: Error
- **Current**: **Not Implemented**
- **Details**: Port names must be unique within module
- **Example**: Two ports named `in` in same module
- **Implementation**: Add duplicate detection in `_parse_ports()`
- **Test**: Verify error on duplicate port names

#### P0250: Missing Instance Model 
- **Severity**: Error
- **Current**: Implemented (P104)
- **Details**: Instance must specify `model` field
- **Example**: `inst1: {mappings: {...}}` (missing model)
- **Test**: Verify required field validation

#### P0251: Duplicate Instance Name L **MISSING - HIGH PRIORITY**
- **Severity**: Error
- **Current**: **Not Implemented**
- **Details**: Instance names must be unique within module
- **Example**: Two instances named `M1` in same module
- **Implementation**: Add duplicate detection in `_parse_instances()`
- **Test**: Verify error on duplicate instance names

### **04 - Import Validation**

#### P0220: Invalid Import Format 
- **Severity**: Error
- **Current**: Implemented (P106)
- **Details**: Import must follow `library.filename[@version]` format
- **Example**: `alias: "justfilename"` (missing library.filename)
- **Test**: Verify format validation with suggestions

#### P0221: Duplicate Import Alias L **MISSING - HIGH PRIORITY**
- **Severity**: Error
- **Current**: **Not Implemented**
- **Details**: Import aliases must be unique within file
- **Example**: Two imports with alias `pdk`
- **Implementation**: Add duplicate detection in `_parse_imports()`
- **Test**: Verify error on duplicate aliases

### **05 - Type Validation Errors**

#### P0501: Invalid Port Direction Enum L **MISSING - MEDIUM PRIORITY**
- **Severity**: Error
- **Current**: **Not Implemented**
- **Details**: Port direction must be valid enum (in, out, in_out)
- **Example**: `dir: "input"` (should be "in")
- **Implementation**: Add enum validation in port parsing
- **Test**: Verify enum validation with suggestions

#### P0502: Invalid Port Type Enum L **MISSING - MEDIUM PRIORITY**
- **Severity**: Error
- **Current**: **Not Implemented**  
- **Details**: Port type must be valid enum (voltage, current, etc.)
- **Example**: `type: "volt"` (should be "voltage")
- **Implementation**: Add enum validation in port parsing
- **Test**: Verify enum validation with suggestions

## Implementation Priority

### **Phase 1: Critical Duplicate Detection (Immediate)**
**Effort**: ~12 hours

1. **P0232: Duplicate Module Name** (4 hours)
   - Add `seen_modules` set in `_parse_modules()`
   - Check each module name against set
   - Generate error with both locations

2. **P0242: Duplicate Port Name** (3 hours)
   - Add `seen_ports` set in `_parse_ports()`
   - Check each port name against set
   - Generate error with both locations

3. **P0251: Duplicate Instance Name** (3 hours)
   - Add `seen_instances` set in `_parse_instances()`
   - Check each instance name against set
   - Generate error with both locations

4. **P0221: Duplicate Import Alias** (2 hours)
   - Add `seen_aliases` set in `_parse_imports()`
   - Check each alias against set
   - Generate error with both locations

### **Phase 2: Enum Validation (Next)**
**Effort**: ~6 hours

5. **P0501: Invalid Port Direction Enum** (3 hours)
   - Add enum validation in `_parse_ports()`
   - Provide suggestions for typos
   - Test all valid/invalid combinations

6. **P0502: Invalid Port Type Enum** (3 hours)
   - Add enum validation in `_parse_ports()`
   - Provide suggestions for typos
   - Test all valid/invalid combinations

**Total MVP Implementation Effort: ~18 hours**

## Hardening Errors (Future Enhancement)

These 56 additional codes improve user experience but don't break basic functionality:

### **Template Validation (8 codes) - Phase 3**
- P0305-P0312: SPICE template syntax, variable validation, mapping structure
- **Rationale**: Template errors caught in later elaboration/generation phases
- **Priority**: Medium (quality of life)

### **Advanced Type Safety (12 codes) - Phase 4**  
- P0503-P0507: Parameter types, value ranges, boolean validation
- P0210-P0213: FileInfo validation beyond basic structure
- **Rationale**: Type mismatches caught during elaboration
- **Priority**: Medium (user experience)

### **Style & Naming (15 codes) - Phase 5**
- P0233, P0243, P0252: Invalid identifier patterns
- P0603-P0607: Naming conventions, reserved keywords
- **Rationale**: Style issues don't break functionality
- **Priority**: Low (polish)

### **Import Advanced Validation (12 codes) - Phase 6**
- P0222-P0227: Self-reference, reserved names, version format
- **Rationale**: Advanced import errors caught during import resolution
- **Priority**: Low (edge cases)

### **Performance & Compatibility (9 codes) - Phase 7**
- P0801-P0803: File size, complexity warnings
- P0703-P0704: Deprecated fields, future compatibility
- **Rationale**: Optimization hints, not functional errors
- **Priority**: Low (optimization)

## Test Strategy

### **MVP Test Requirements**
Each MVP critical code needs 4 test types:

1. **Detection Test**: Verify error is properly detected
2. **Location Test**: Verify precise line/column information
3. **Suggestion Test**: Verify helpful error suggestions
4. **Edge Case Test**: Verify boundary conditions

**Total MVP Tests**: 15 codes × 4 tests = 60 comprehensive tests

### **Test File Organization**
```
tests/unit_tests/parser/
   test_mvp_critical_errors.py      # 15 MVP codes
   test_duplicate_detection.py      # P0232, P0242, P0251, P0221
   test_enum_validation.py          # P0501, P0502
   test_hardening_errors.py         # Future 56 codes
```

## Benefits of MVP-First Approach

1. **Production Ready**: Prevents silent data corruption and runtime crashes
2. **Rapid Value**: 18 hours vs 200+ hours for complete implementation
3. **User Confidence**: Core functionality works reliably
4. **Foundation**: Establishes patterns for systematic hardening
5. **Iterative**: User feedback guides hardening priorities

## Success Criteria

### **MVP Phase Complete When:**
- All 15 MVP critical codes implemented and tested
- Zero silent data corruption from duplicates
- Zero runtime enum errors
- Comprehensive test coverage (60 tests passing)
- Documentation complete with examples

### **Hardening Phases Complete When:**
- All 71 total parser codes implemented
- Language server integration ready
- Professional-grade user experience
- Complete edge case coverage