# Project Todo List

## Current Sprint - Validation & Quality Enhancements

### 🎉 **CRITICAL PARAMETER PROPAGATION BUG FIX COMPLETED ✅**
- [X] **Critical Module Instance Parameter Propagation Bug Fix** ✅
  - [X] Identified missing parameter propagation in `_generate_subckt_call()` method ✅
  - [X] Enhanced method to match device instance parameter handling ✅
  - [X] Maintained backward compatibility for instances without parameters ✅
  - [X] Verified fix with real-world `two_stage_ota.yml` example ✅
  - [X] Confirmed all 48 existing generator tests still pass ✅
  - [X] Updated method documentation to reflect parameter support ✅
  - [X] Regenerated example SPICE files with correct parameter propagation ✅

**Critical Achievement**: Module instances now correctly pass parameters to subcircuit calls in SPICE output. The `two_stage_ota` example now generates `X_FIRST_STAGE ... M={M_first_stage}` instead of missing the parameter entirely. This fixes a fundamental bug that broke hierarchical parameterization in complex analog designs.

### 🎉 **NET DECLARATION VALIDATION COMPLETED ✅**
- [X] **Net Declaration Validation Feature** ✅
  - [X] Implement validation for undeclared nets in instance mappings ✅
  - [X] Handle pattern expansion validation (`out_<p,n>` → `out_p`, `out_n`) ✅
  - [X] Generate non-breaking warnings for undeclared nets ✅
  - [X] Integrate with existing warning system ✅
  - [X] Create comprehensive test suite (6 test cases) ✅
  - [X] Test real-world scenario (ota_5t module issue) ✅
  - [X] Verify backward compatibility with existing tests ✅
  - [X] Update context documentation ✅

**Technical Achievement**: SPICEGenerator now provides intelligent connectivity validation that catches undeclared nets while maintaining robust netlisting functionality. This addresses the specific issue identified in `two_stage_ota.yml` where `out_n` and `out_<p,n>` nets were used but not declared.

### 🎉 **CRITICAL PATTERN EXPANSION BUG FIX COMPLETED ✅**
- [X] **Major Circuit Correctness Bug Fix** ✅
  - [X] Identified critical bug in one-sided net pattern expansion ✅
  - [X] Fixed `_expand_mapping_patterns` to use `instance_index` for net patterns ✅
  - [X] Verified differential pairs now connect correctly (`MN_P→in_p`, `MN_N→in_n`) ✅
  - [X] Added comprehensive test coverage using `diff_pair_nmos.yml` fixture ✅
  - [X] Created `TestRealWorldDifferentialPair` class with 3 test methods ✅
  - [X] Fixed failing test expectation to match correct behavior ✅
  - [X] Verified all 51 expander tests pass ✅

**Critical Achievement**: Fixed bug that completely broke differential amplifier functionality. Pattern expansion now correctly routes signals to differential pairs and other multi-instance circuits.

### 🎉 **PORT ORDER CANONICAL COMPLIANCE COMPLETED ✅**
- [X] **Critical Bug Fix: SPICE Port Order** ✅
  - [X] Identified alphabetical sorting bug in `_get_port_list()` method ✅
  - [X] Fixed generator to preserve YAML declaration order instead of sorting ✅
  - [X] Validated that pattern expansion preserves correct order (`in_<p,n>` → `["in_p", "in_n"]`) ✅
  - [X] Updated test expectations to match canonical YAML order ✅
  - [X] Verified all 42 generator tests pass with corrected port order ✅
  - [X] Regenerated example SPICE files with correct port order ✅

**Technical Achievement**: SPICE `.subckt` declarations now follow the canonical order defined in the ASDL YAML `ports:` section, ensuring consistency and predictability across all generated netlists.

### 🎉 **UNUSED COMPONENT VALIDATION COMPLETED ✅**
- [X] **Core Unused Validation Feature** ✅
  - [X] Implement usage tracking for models and modules ✅
  - [X] Add recursive hierarchy analysis from top module ✅
  - [X] Generate warnings for unused components without breaking netlisting ✅
  - [X] Integrate with existing warning system ✅
  - [X] Create comprehensive test suite (5 test cases) ✅
  - [X] Verify backward compatibility with existing generator tests ✅
  - [X] Demonstrate feature with real-world examples ✅

**Technical Achievement**: SPICEGenerator now provides intelligent validation that helps developers identify dead code while maintaining robust netlisting functionality.

## Current Sprint: **THOROUGH DATA STRUCTURE REFACTOR ✅ COMPLETE**

### **🎉 COMPLETE LEGACY REMOVAL & ARCHITECTURE CLEANUP ✅**
- [X] **Phase 1: PrimitiveType Enum** ✅
  - [X] ❌ **REMOVED** legacy DeviceType enum completely ✅
  - [X] ✅ **ADDED** clean PrimitiveType enum (PDK_DEVICE vs SPICE_DEVICE) ✅
  - [X] Comprehensive test coverage: 8/8 tests passing ✅

- [X] **Phase 2: Universal Metadata Field** ✅
  - [X] ✅ **ADDED** metadata field to ALL structures: ASDLFile, FileInfo, DeviceModel, Port, Module, Instance ✅
  - [X] ❌ **REMOVED** Instance intent field (replaced with metadata) ✅
  - [X] Comprehensive test coverage: 9/9 tests passing ✅

- [X] **Phase 3: Internal Nets Field** ✅
  - [X] ❌ **REMOVED** complex Nets class entirely ✅
  - [X] ✅ **REPLACED** with simple internal_nets: List[str] on Module ✅
  - [X] Comprehensive test coverage: 9/9 tests passing ✅

- [X] **Phase 4: Simplified DeviceModel** ✅
  - [X] ❌ **REMOVED** legacy fields (model, params, description) ✅
  - [X] ❌ **REMOVED** backward compatibility methods ✅
  - [X] ✅ **REQUIRED** device_line field (now non-optional) ✅
  - [X] Comprehensive test coverage: 8/8 tests passing ✅

- [X] **Phase 5: Serialization Separation** ✅
  - [X] ❌ **REMOVED** all serialization methods from ASDLFile ✅
  - [X] ✅ **CREATED** dedicated src/asdl/serialization.py module ✅
  - [X] Clean separation of data structures and I/O logic ✅

**🎯 PRODUCTION READY**: Clean architecture, 34/34 data structure tests passing ✅

## Next Sprint: Linter & Compiler Architecture Refactoring
- [X] **Phase 1: Parser Refactoring** ✅
  - [X] Rewrite parser to be pure, non-validating ✅
  - [X] Integrate `ruamel.yaml` for location tracking ✅
  - [X] Rewrite parser test suite using TDD ✅
  - [X] Implement location tracking for `FileInfo` ✅
- [X] **Phase 2: Full Location Tracking** ✅
  - [X] Add `Locatable` base class to all relevant data structures (`DeviceModel`, `Module`, `Port`, `Instance`). ✅
  - [X] Update parser to populate location data for all structures. ✅
  - [X] Update tests to assert correct location data for all structures. ✅
- [X] **Phase 3: Foundation** ✅
  - [X] Create shared `Diagnostic` data structures (`src/asdl/diagnostics.py`) ✅
  - [X] Create tests for diagnostic data structures ✅
- [X] **Phase 4: Diagnostic System Foundation** ✅
  - [X] Defined structured diagnostic codes for Parser, Elaborator, and Validator. ✅
  - [X] Created `doc/diagnostic_codes.md` to document all codes, their status, and test coverage. ✅
  - [X] Refactored `Diagnostic` data class to support structured data (`code`, `title`, `details`, `suggestion`). ✅
- [ ] **Phase 5: Elaboration & Analysis Pipeline**
  - [X] **Step 1: Create the `Elaborator` Foundation** ✅
    - [X] Create new file `src/asdl/elaborator.py` with the `Elaborator` class skeleton. ✅
    - [X] Create new test suite `tests/unit_tests/elaborator/`. ✅
    - [X] Document the design plan in `doc/elaborator_design_plan.md`. ✅
  - [X] **Step 2: Migrate Pattern Expansion (TDD)** ✅
    - [X] Incrementally move pattern expansion logic from `PatternExpander` to `Elaborator`. ✅
    - [X] Refactor all `ValueError` exceptions to `Diagnostic` reports. ✅
    - [X] Ensure all new logic is covered by tests in the new test suite. ✅
  - [ ] **Step 3: Implement Parameter Resolution (TDD)**
    - [ ] Add logic to the `Elaborator` to resolve and substitute parameter values.
    - [ ] Create tests for parameter resolution, including error cases (e.g., undefined parameters).
  - [ ] **Step 4: Implement Bus Pattern Expansion (TDD)**
    - [ ] Implement robust `_has_bus_pattern` detection logic.
    - [ ] Add `_expand_bus_pattern` method to handle range-based expansion (e.g., `[3:0]`).
    - [ ] Create tests for bus pattern expansion, including error cases.
  - [ ] **Step 5: Deprecate Old Code**
    - [ ] Delete `src/asdl/expander.py` and its associated tests.
    - [ ] Remove parameter resolution logic from `SPICEGenerator`.
  - [ ] Create new `Validator` module (`src/asdl/validator.py`)
- [ ] **Phase 5: Tooling Back-Ends**
  - [ ] Create Linter entry point script (`scripts/asdl_linter.py`)
  - [ ] Update compiler pipeline to use the new `Validator`

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
  - [X] Updated device generation tests to expect hierarchical subcircuits ✅
  - [X] Updated pipeline tests to expect real PDK device names (nfet_03v3, pfet_03v3) ✅
  - [X] Created missing test fixture (inverter_reordered.yml) ✅
  - [X] Updated PySpice tests to handle complex PDK parameter limitations ✅
  - [X] Removed all legacy test expectations (pre-release refactoring) ✅
  - [X] **Result**: 11 test failures → 0 test failures (126/126 passing) ✅

**✅ Pre-Release Achievement**: All tests now validate the current hierarchical subcircuit architecture

### 🎉 **PATTERN EXPANSION SYSTEM COMPLETED ✅**
- [X] **Pattern Expansion Rules Documentation** ✅
  - [X] Documented comprehensive literal expansion rules in `doc/pattern_expansion_rules.md` ✅
  - [X] Defined error conditions and validation rules ✅
  - [X] Clarified instance expansion behavior (separate instantiations) ✅
- [X] **CRITICAL MAPPING FORMAT CORRECTION** ✅
  - [X] Identified incorrect mapping format: `G_<p,n>: in_<p,n>` → `G: in_<p,n>` ✅
  - [X] Updated ASDL_schema documentation to show correct format ✅
  - [X] Fixed all examples in schema and example files ✅
  - [X] Recorded lesson learned in memory.md ✅
- [X] **SCHEMA v0.5 REFINEMENT & LANGUAGE DOCUMENTATION** ✅
  - [X] Created clean, concise ASDL_schema_v0p5 structure ✅
  - [X] Developed comprehensive language.md with semantic rules ✅
  - [X] Codified "Expansion only on RHS" mapping rule ✅
  - [X] Defined best practices and future extensions ✅
  - [X] Validated mapping lesson learned in official documentation ✅
- [X] **Pattern Expansion System Implementation** ✅
  - [X] **Step 1: Pattern Parsing & Validation Tests + Implementation** ✅
    - [X] Write tests for pattern detection (`_has_literal_pattern`) ✅
    - [X] Write tests for pattern extraction (`_extract_literal_pattern`) ✅
    - [X] Write tests for pattern validation (item counts, emptiness) ✅
    - [X] Implement pattern parsing methods ✅
  - [X] **Step 2: Basic Literal Expansion Tests + Implementation** ✅
    - [X] Write tests for port pattern expansion integration ✅
    - [X] Write tests for mapping pattern expansion (order-sensitive) ✅
    - [X] Write tests for one-sided pattern expansion ✅
    - [X] Implement `expand_port_patterns` method with literal pattern support ✅
    - [X] Implement `_expand_mapping_patterns` method with full pattern support ✅
  - [X] **Step 3: Instance Expansion Tests + Implementation** ✅ 
    - [X] Write tests for instance name expansion ✅
    - [X] Write tests for synchronized instance+mapping expansion ✅
    - [X] Write tests for separate instantiation behavior ✅
    - [X] Implement `expand_instance_patterns` method ✅
  - [X] **Step 4: Instance Documentation & Schema Robustness** ✅
    - [X] Added `doc` field as first-class citizen for instances ✅
    - [X] Fixed Pattern Expander to preserve `doc` field during expansion ✅
    - [X] Replaced manual field copying with `dataclasses.replace()` for future-proofing ✅
    - [X] Created 7 comprehensive documentation tests ✅
    - [X] Created 6 schema robustness tests ✅
    - [X] Fixed module parameter generation (`.param` declarations) ✅
    - [X] Fixed instance naming consistency (`X_{name}` format) ✅
    - [X] Fixed NoneType parameter handling ✅
  - [X] **Step 5: Test Expectation Updates & Architecture Validation** ✅
    - [X] Updated all test expectations to match hierarchical subcircuit architecture ✅
    - [X] Removed legacy support expectations (pre-release refactoring) ✅
    - [X] Created missing test fixtures ✅
    - [X] Fixed PySpice integration test limitations ✅
    - [X] Achieved perfect test status (126/126 passing) ✅

**✅ Key Achievement This Phase**: Complete pattern expansion system with perfect test validation

## Completed Tasks

### **Phase 5: Advanced Features (COMPLETE)**
- [X] **Unused Component Validation** ✅
  - [X] Hierarchical usage tracking from top module ✅
  - [X] Warning generation for unused models and modules ✅
  - [X] Non-breaking validation that preserves netlisting ✅
  - [X] Comprehensive test coverage (5 scenarios) ✅
  - [X] Integration with existing warning system ✅
  - [X] Backward compatibility maintained ✅

### **PHASE 4 COMPLETED ✅** (ngspice Simulation Testing & User Workflow Validation)
**PERFECT USER WORKFLOW ACHIEVED**:

**✅ Ideal User Workflow Validated:**
1. User creates device in xschem schematic ✅
2. User adjusts device size in xschem ✅
3. User netlists the schematic ✅
4. User copies device line exactly to ASDL YAML `device_line` ✅
5. ASDL preserves expressions exactly as-is ✅
6. ngspice simulates perfectly with ZERO manual intervention ✅

**✅ Technical Achievements:**
- [X] **Devcontainer Enhancement** ✅
  - [X] Full repository mounted at `/foss/asdl` with EDA tools properly configured ✅
  - [X] ngspice accessible and working correctly ✅
  - [X] Concurrent access to ASDL codebase and EDA tool environment ✅

- [X] **PDK Integration Perfection** ✅
  - [X] GF180MCU PDK models (`nfet_03v3`, `pfet_03v3`) working correctly ✅
  - [X] Complex device lines with expressions work exactly as-is from xschem ✅
  - [X] ngspice automatically resolves `ad='int((nf+1)/2) * W/nf * 0.18u'` using hard-coded values ✅

- [X] **Complete Simulation Validation** ✅
  - [X] Operating Point Analysis ✅
  - [X] DC Transfer Characteristic ✅
  - [X] Switching Transient Analysis ✅
  - [X] AC Small-Signal Response ✅
  - [X] Propagation Delay Measurement ✅
  - [X] Load Capacitance Analysis ✅

**✅ Key Discovery**: ngspice is smarter than expected - it automatically resolves complex expressions using hard-coded parameter values from the same device line, eliminating the need for manual parameter extraction or expression flattening.

### 🎉 **PORT MAPPING VALIDATION BUG FIX COMPLETED ✅** (CRITICAL QUALITY IMPROVEMENT)
**SILENT FAILURE ELIMINATED**: Port mapping validation now catches inconsistencies that were previously ignored ✅

## Setup & Planning ✅ COMPLETED
- [X] Setup context management files
- [X] Analyze ASDL schema v0.4 structure
- [X] Review architecture decisions with user
- [X] Update schema field name from `design_info` to `file_info`
- [X] Implement basic Python class definitions and data structures
- [X] Define interfaces between parser, resolver, and generator
- [X] Create detailed implementation plan
- [X] Update implementation plan with current sprint status

## Development Environment ✅ COMPLETED
- [X] Verify virtual environment setup
- [X] Install/verify all dependencies
- [X] Setup development tools (black, flake8, pytest)
- [X] Create initial source code structure

## Current Sprint
- [ ] **Refactor Core Data Structures**: Implement the changes outlined in `doc/data_structure_design.md` and recorded in `context/memory.md`.
  - [ ] Move serialization logic from `data_structures.py` to a new `serialization.py` file.
  - [ ] Refactor `DeviceModel` and `DeviceType`.
  - [ ] Replace `Nets` class with `internal_nets` on `Module`.
  - [ ] Add the universal `metadata` field to all relevant classes.

## Backlog
[List of tasks for future sprints]

## Completed Tasks
[List of completed tasks] 