# Project Todo List

## 🎉 **ELABORATOR IMPLEMENTATION COMPLETED ✅** (MAJOR MILESTONE)

### **🚀 Ready for Next Sprint: SPICEGenerator Refactoring**
**FOUNDATION COMPLETE**: The `Elaborator` is now production-ready with comprehensive pattern expansion capabilities

**✅ Major Achievement Summary**:
- **13/13 elaborator tests passing** ✅
- **Complete PatternExpander replacement** ✅  
- **Enhanced diagnostic system** ✅
- **Order-sensitive pattern expansion** ✅
- **Comprehensive instance mapping expansion** ✅
- **Mixed pattern detection and validation** ✅

**Next Phase**: Refactor `SPICEGenerator` to consume elaborated ASDL files and deprecate `PatternExpander`

## Previous Sprint - Validation & Quality Enhancements (COMPLETED)

### 🎉 **CRITICAL PARAMETER PROPAGATION BUG FIX COMPLETED ✅**
- [X] **Critical Module Instance Parameter Propagation Bug Fix** ✅

**Critical Achievement**: Module instances now correctly pass parameters to subcircuit calls in SPICE output. The `two_stage_ota` example now generates `X_FIRST_STAGE ... M={M_first_stage}` instead of missing the parameter entirely. This fixes a fundamental bug that broke hierarchical parameterization in complex analog designs.

### 🎉 **NET DECLARATION VALIDATION COMPLETED ✅**
- [X] **Net Declaration Validation Feature** ✅

**Technical Achievement**: SPICEGenerator now provides intelligent connectivity validation that catches undeclared nets while maintaining robust netlisting functionality. This addresses the specific issue identified in `two_stage_ota.yml` where `out_n` and `out_<p,n>` nets were used but not declared.

### 🎉 **PARSER STABILIZATION & TEST SUITE HARDENING COMPLETED ✅**
- [X] **Task: Stabilize test suite after `Locatable` refactoring** ✅

### 🎉 **CRITICAL PATTERN EXPANSION BUG FIX COMPLETED ✅**
- [X] **Major Circuit Correctness Bug Fix** ✅

**Critical Achievement**: Fixed bug that completely broke differential amplifier functionality. Pattern expansion now correctly routes signals to differential pairs and other multi-instance circuits.

### 🎉 **PORT ORDER CANONICAL COMPLIANCE COMPLETED ✅**
- [X] **Critical Bug Fix: SPICE Port Order** ✅

**Technical Achievement**: SPICE `.subckt` declarations now follow the canonical order defined in the ASDL YAML `ports:` section, ensuring consistency and predictability across all generated netlists.

### 🎉 **UNUSED COMPONENT VALIDATION COMPLETED ✅**
- [X] **Core Unused Validation Feature** ✅

**Technical Achievement**: SPICEGenerator now provides intelligent validation that helps developers identify dead code while maintaining robust netlisting functionality.

## Current Sprint: **THOROUGH DATA STRUCTURE REFACTOR ✅ COMPLETE**

### **🎉 COMPLETE LEGACY REMOVAL & ARCHITECTURE CLEANUP ✅**
- [X] **Phase 1: PrimitiveType Enum** ✅
- [X] **Phase 2: Universal Metadata Field** ✅
- [X] **Phase 3: Internal Nets Field** ✅
- [X] **Phase 4: Simplified DeviceModel** ✅
- [X] **Phase 5: Serialization Separation** ✅

**🎯 PRODUCTION READY**: Clean architecture, 34/34 data structure tests passing ✅

## Next Sprint: Linter & Compiler Architecture Refactoring
- [X] **Phase 1: Parser Refactoring** ✅
- [X] **Phase 2: Full Location Tracking** ✅
- [X] **Phase 3: Foundation** ✅
- [X] **Phase 4: Diagnostic System Foundation** ✅
- [X] **Phase 5: Elaboration & Analysis Pipeline** ✅ **COMPLETE**
- [ ] **Phase 5: Parser Hardening (TDD)**
  - [X] **Roadblock Resolved**: Type-safe access to `ruamel.yaml` location data is working. ✅
  - [X] Implement and test `P200`: Unknown Top-Level Section (Warning). ✅
  - [ ] Implement and test `P102`: Missing Required Section.
  - [ ] Implement and test `P103`: Invalid Section Type.
  - [ ] Implement and test `P201`: Unknown Field (Warning).
- [ ] **Phase 6: SPICEGenerator Refactoring Pipeline** (NEXT PRIORITY)
  - [ ] **Step 4: Refactor SPICEGenerator to use Elaborator**
    - [ ] Update generator to consume elaborated ASDLFile from Elaborator.
    - [ ] Remove all pattern expansion logic from SPICEGenerator.
    - [ ] Pass parameter strings through as-is.
    - [ ] Refactor generator test suite to use elaborated fixtures.
    - [ ] Verify all existing functionality preserved.
  - [ ] **Step 5: Deprecate PatternExpander**
    - [ ] Delete `src/asdl/expander.py` and its associated tests.
    - [ ] Remove parameter resolution logic from `SPICEGenerator`.
    - [ ] Update any remaining references to use Elaborator.
- [ ] **Phase 5: Tooling Back-Ends**
  - [ ] Create Linter entry point script (`scripts/asdl_linter.py`)

## Backlog: Advanced Validation & User Experience

### **Testing & Refinements**
- [ ] Thoroughly test `serialization.py` module

### **Enhanced Validation Features** (NEW PRIORITY)
- [ ] **Cross-Reference Validation**
  - [ ] Detect and warn about circular dependencies between modules
  - [ ] Validate parameter references (undefined parameters used)
  - [ ] Check for orphaned nets (declared but never connected)
  - [ ] Validate port width consistency in pattern expansions
- [ ] **Design Rule Checking (DRC)**
  - [ ] Basic electrical rules (no floating inputs/outputs)
  - [ ] Port direction consistency checking
  - [ ] Parameter range validation
  - [ ] Device constraint validation (W/L ratios, etc.)
- [ ] **Parameter Resolution (DEFERRED)**
  - [ ] Implement robust parameter resolution in `Elaborator`.
  - [ ] Handle hierarchical scope and expressions.
  - [ ] Add diagnostic reporting for undefined parameters and circular dependencies.

### **User Experience Enhancements**
- [ ] **Improved Error Messages**
  - [ ] Line number references in YAML files for errors/warnings
  - [ ] Suggestion system for common mistakes
  - [ ] Context-aware error descriptions
  - [ ] Color-coded warning levels (info, warning, error)
- [ ] **Documentation Generation**
  - [ ] Auto-generate circuit documentation from ASDL designs
  - [ ] HTML documentation with cross-references
  - [ ] Dependency graphs and usage maps
  - [ ] Parameter sensitivity analysis

## PHASE 5: Pattern Expansion & Advanced Features (COMPLETED)

### 🎉 **PHASE 5 COMPLETED ✅** (Pattern Expansion & Advanced Features + Test Expectation Updates)
**PERFECT TEST STATUS ACHIEVED**: 131/131 tests passing ✅

### 🎉 **TEST EXPECTATION REFACTORING COMPLETED ✅**
- [X] **Complete Test Architecture Update** ✅

**✅ Pre-Release Achievement**: All tests now validate the current hierarchical subcircuit architecture

### 🎉 **PATTERN EXPANSION SYSTEM COMPLETED ✅**
- [X] **Pattern Expansion Rules Documentation** ✅
- [X] **CRITICAL MAPPING FORMAT CORRECTION** ✅
- [X] **SCHEMA v0.5 REFINEMENT & LANGUAGE DOCUMENTATION** ✅
- [X] **Pattern Expansion System Implementation** ✅

## Current Sprint
- [X] Extract validation logic from SPICEGenerator using TDD approach
- [X] Implement ASDLValidator with port mapping validation
- [X] Implement ASDLValidator with net declaration validation  
- [X] Implement ASDLValidator with unused components validation
- [X] Remove all validation logic from SPICEGenerator (clean separation)
- [ ] Fix SPICEGenerator data structure compatibility issues
  - [ ] Fix DeviceType → PrimitiveType import
  - [ ] Fix DeviceModel method calls (params, get_doc(), get_parameter_defaults(), has_device_line())
  - [ ] Update method signatures to match new data structures
- [ ] Integrate ASDLValidator into main pipeline (before generation)
- [ ] Create end-to-end tests with validator + generator integration
- [ ] Test generator with real ASDL files after compatibility fixes

## Backlog
- [ ] Enhanced validation features
  - [ ] Cross-reference validation between modules
  - [ ] Circular dependency detection
  - [ ] Parameter type validation
- [ ] Generator improvements
  - [ ] Better error handling for malformed ASDL files
  - [ ] Support for more SPICE device types
  - [ ] Optimization for large hierarchical designs
- [ ] Documentation updates
  - [ ] Update README with new validation pipeline
  - [ ] Add examples showing validator usage
  - [ ] Document migration from old validation approach

## Completed Tasks
- [X] **MAJOR MILESTONE**: Complete elaborator implementation with 13/13 tests passing
- [X] **MAJOR MILESTONE**: Data structure refactoring with 34/34 tests passing  
- [X] **MAJOR MILESTONE**: Parser implementation with 23/23 tests passing
- [X] **MAJOR MILESTONE**: Validation extraction with 6/6 validator tests passing
- [X] Implement comprehensive pattern expansion system
- [X] Add location tracking and diagnostics to parser
- [X] Create structured diagnostic system
- [X] Refactor data structures for clean architecture
- [X] Remove legacy code and backward compatibility
- [X] Implement TDD approach for validation methods
- [X] Extract all validation logic from generator (214 lines removed)
- [X] Create comprehensive test suite for validator
- [X] Clean separation of concerns between validation and generation