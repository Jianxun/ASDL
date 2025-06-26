# Project Memory

## Project Overview
ASDL (Analog Structured Description Language) is a Python project to build classes that represent structured circuit topologies. The main goal is to parse ASDL YAML files (defined by ASDL_schema_v0p4) into proper data structures and convert them to SPICE netlists that are simulatable with ngspice.

Key components:
- YAML-based intermediate representation for analog circuits
- Python classes to represent circuit hierarchy and structure  
- YAML to SPICE netlist converter with PySpice validation
- Support for pattern expansion (differential pairs, arrays)
- Parameter substitution system
- Design intent capture
- **NEW**: Unused component validation with warnings

Schema structure:
- `file_info`: File metadata (top_module, doc, revision, author, date)
- `models`: Device/component templates with PDK mappings
- `modules`: Circuit hierarchy with ports, instances, and connectivity

## Current State
**🚀 THOROUGH DATA STRUCTURE REFACTOR COMPLETE ✅**

### **NEW**: Complete Legacy Removal & Architecture Cleanup (THOROUGH REFACTOR) ✅
**ACHIEVEMENT**: **COMPLETE removal of all legacy support** with thorough data structure cleanup

**🔥 BREAKING CHANGES IMPLEMENTED (As Requested):**
- **❌ REMOVED** legacy `DeviceType` enum completely (no backward compatibility)
- **❌ REMOVED** all DeviceModel legacy fields (`model`, `params`, `description`) 
- **❌ REMOVED** DeviceModel backward compatibility methods completely
- **❌ REMOVED** `Nets` class entirely (replaced with simple List[str])
- **❌ REMOVED** Instance `intent` field (replaced with universal metadata)
- **❌ REMOVED** all serialization methods from ASDLFile class

**✅ NEW CLEAN ARCHITECTURE:**

1. **Serialization Separation**: ✅ COMPLETE
   - Created dedicated `src/asdl/serialization.py` module
   - Moved ALL I/O logic out of data classes  
   - Pure data structures with single responsibility
   - Clean separation between data and serialization concerns

2. **PrimitiveType Enum**: ✅ COMPLETE
   - **NEW**: Clean `PrimitiveType` enum (PDK_DEVICE vs SPICE_DEVICE)
   - **REMOVED**: Ambiguous `DeviceType` enum completely
   - Clear classification based on primitive origin
   - 8/8 comprehensive test cases passing ✅

3. **Simplified DeviceModel**: ✅ COMPLETE  
   - **REQUIRED**: `device_line` field now non-optional
   - **REMOVED**: Legacy `model`, `params`, `description` fields
   - **REMOVED**: `has_device_line()`, `get_parameter_defaults()` methods
   - Clean, minimal structure for production use
   - 8/8 comprehensive test cases passing ✅

4. **Internal Nets Field**: ✅ COMPLETE
   - **REPLACED**: Complex `Nets` class with `internal_nets: List[str]`
   - Simple, direct approach without unnecessary abstraction
   - Preserves order, supports patterns, integrates with metadata
   - 9/9 comprehensive test cases passing ✅

5. **Universal Metadata Field**: ✅ COMPLETE
   - **REPLACED**: Instance `intent` with universal `metadata` field
   - Added to ALL structures: ASDLFile, FileInfo, DeviceModel, Port, Module, Instance
   - Consistent extensibility mechanism across all levels
   - 9/9 comprehensive test cases passing ✅

**✅ TEST RESULTS**: 34/34 data structure tests passing (complete validation) ✅

**🎯 PRODUCTION READY**: Clean architecture without legacy baggage, ready for future development

**🎉 CRITICAL PARAMETER PROPAGATION BUG FIX COMPLETED ✅**

### **NEW**: Parameter Propagation Bug Fix (CRITICAL FUNCTIONALITY RESTORE) ✅
**ACHIEVEMENT**: Fixed missing parameter propagation in module instances
- **Problem**: Module instances weren't passing parameters to subcircuit calls in SPICE output
- **Symptoms**: `X_FIRST_STAGE ... ota_5t` missing `M=2` parameter despite ASDL specification
- **Root Cause**: `_generate_subckt_call()` method only generated node list but ignored instance parameters
- **Solution**: Enhanced `_generate_subckt_call()` to match `_generate_device_line()` parameter handling
- **Result**: Module instances now correctly propagate parameters: `X_FIRST_STAGE ... ota_5t M={M_first_stage}`
- **Testing**: All 48 existing generator tests pass, real-world example verified
- **Impact**: Hierarchical parameterization now works correctly for complex designs

**Key Features**:
- **Consistent API**: Module instances now use same parameter format as device instances
- **Expression Support**: Parameter values with expressions (`M={M_first_stage}`) work correctly
- **Optional Parameters**: Instances without parameters still work (backward compatible)
- **Format Consistency**: Uses existing `_format_named_parameters()` method for consistency

**Technical Implementation**:
- Modified `_generate_subckt_call()` method in SPICEGenerator class
- Added instance parameter extraction: `instance_params = instance.parameters if instance.parameters else {}`
- Added parameter formatting and appending to subcircuit call
- Maintained same parameter format as device instances: `X_name nodes subckt_name param=value`
- Updated method documentation to reflect parameter support

**Before (BROKEN)**:
```spice
X_FIRST_STAGE in_n in_p first_stage_out vbn vss vdd ota_5t
X_SECOND_STAGE first_stage_out out vbn vss vdd common_source_pmos
```

**After (FIXED)**:
```spice
X_FIRST_STAGE in_n in_p first_stage_out vbn vss vdd ota_5t M={M_first_stage}
X_SECOND_STAGE first_stage_out out vbn vss vdd common_source_pmos M={M_second_stage}
```

### **PREVIOUS**: Net Declaration Validation Feature (CRITICAL CONNECTIVITY VALIDATION) ✅
**ACHIEVEMENT**: Implemented comprehensive validation for undeclared nets in instance mappings
- **Feature**: SPICEGenerator now validates that all nets used in mappings are properly declared
- **Scope**: Checks nets referenced in instance mappings against module ports and internal nets
- **Pattern Support**: Correctly handles pattern expansion (`out_<p,n>` → `out_p`, `out_n`)
- **Non-Breaking**: Generates helpful warnings but continues netlisting successfully
- **Real-World Impact**: Catches the specific issue identified in `two_stage_ota.yml` ota_5t module
- **Test Coverage**: 6 comprehensive test cases covering all validation scenarios
- **Integration**: Seamlessly integrated into existing validation pipeline
- **User Experience**: Clear warning messages that identify specific undeclared nets and affected modules
- **Result**: 48/48 generator tests passing (was 42, now 48 with new validation tests)

**Key Features**:
- **Connectivity Validation**: Validates that all net names in mappings are declared as ports or internal nets
- **Pattern Expansion Support**: Correctly expands and validates pattern-based net names
- **Module-Level Reporting**: Clearly identifies which module contains undeclared nets
- **Non-Disruptive**: Netlisting continues successfully despite validation warnings
- **Integration**: Uses existing Python warnings system for consistency with other validations

**Test Coverage**:
- Valid net declarations (no warnings generated)
- Basic undeclared net detection and warning generation
- Pattern expansion validation (`in_<p,n>`, `out_<p,n>`)
- Real-world scenario testing (ota_5t module issue)
- Edge cases (empty modules, mixed valid/invalid nets)
- Warning message content and format validation

**Technical Implementation**:
- Added `_validate_net_declarations()` method to SPICEGenerator class
- Added `_has_literal_pattern()` and `_expand_literal_pattern()` helper methods
- Integrated validation into `generate_subckt()` pipeline
- Maintains backward compatibility with existing code
- Reuses pattern expansion logic from expander module

### **NEW**: Port Order Canonical Compliance (CRITICAL BUG FIX) ✅
**ACHIEVEMENT**: Fixed SPICE port order to follow YAML declaration order instead of alphabetical sorting
- **Problem**: Generator was sorting module ports alphabetically, breaking canonical order from YAML
- **Impact**: `.subckt ota_5t in_n in_p out vbn vdd vss` → `.subckt ota_5t in_p in_n out vbn vss vdd`
- **Root Cause**: `_get_port_list()` method used `sorted(module.ports.keys())` instead of preserving YAML order
- **Solution**: Changed to `list(module.ports.keys())` to preserve Python 3.7+ dict insertion order
- **Validation**: Pattern expansion correctly preserves order: `in_<p,n>` → `["in_p", "in_n"]` 
- **Test Updates**: Updated 3 test expectations to match correct YAML declaration order
- **Result**: SPICE .subckt declarations now follow canonical order defined in ASDL YAML ports section

### **NEW**: Unused Component Validation Feature (COMPLETE) ✅
**ACHIEVEMENT**: Successfully implemented validation for declared but unused modules and models
- **Core Functionality**: SPICEGenerator now tracks usage and warns about unused components
- **Recursive Tracking**: Walks module hierarchy from top module to determine actual usage
- **Non-Breaking**: Generates warnings but continues netlisting successfully
- **Comprehensive Testing**: 5 test cases covering all scenarios (unused models, modules, multiple warnings, no warnings, recursive tracking)
- **Integration**: Seamlessly integrated with existing warning system
- **User Experience**: Clear warning messages that help developers identify dead code
- **Result**: 41/41 generator tests passing (was 36, now 41 with new validation tests)

**Key Features**:
- **Usage Tracking**: Recursively tracks which models and modules are actually instantiated
- **Smart Warnings**: Warns about unused models and modules (excluding top module)
- **Hierarchical Analysis**: Correctly handles nested module dependencies
- **Non-Disruptive**: Netlisting continues successfully despite unused components
- **Warning Integration**: Uses existing Python warnings system for consistency

**Test Coverage**:
- Unused model detection and warnings
- Unused module detection and warnings  
- Multiple unused components handling
- No false positives when all components are used
- Recursive module usage tracking through hierarchy

**Technical Implementation**:
- Added `_used_models` and `_used_modules` tracking sets to SPICEGenerator
- Added `_track_usage()` method for hierarchical usage analysis
- Added `_validate_unused_components()` method for warning generation
- Integrated validation into main `generate()` pipeline
- Maintains backward compatibility with existing code

### **Previous Achievements**: ✅ **Phase 5 COMPLETE** - All 126 tests passing ✅
- ✅ **Phase 1**: ASDL Parser + SPICE Generator + PySpice Integration (44+7+6=57 tests)
- ✅ **Phase 2**: Hierarchical Subcircuit Implementation (15/21 functional tests passing)
- ✅ **Phase 3**: Parameter Handling Enhancement (NEW DEVICE_LINE APPROACH)
- ✅ **Phase 4**: ngspice Simulation Testing (PERFECT USER WORKFLOW VALIDATED)
- ✅ **Phase 5**: Pattern Expansion & Advanced Features **COMPLETE (126/126 tests passing)**
  - ✅ **Step 1**: Pattern Parsing & Validation ✅
  - ✅ **Step 2**: Basic Literal Expansion (Port + Mapping patterns) ✅
  - ✅ **Step 3**: Instance Expansion (Synchronized instance+mapping expansion) ✅
  - ✅ **Step 4**: Instance Documentation & Schema Robustness ✅
  - ✅ **Step 5**: **TEST EXPECTATIONS FULLY UPDATED** ✅

### **NEW**: Test Expectation Refactoring Complete ✅
**ACHIEVEMENT**: Successfully updated all test expectations to match hierarchical subcircuit architecture
- **Scope**: Complete pre-release refactoring without legacy support
- **Device Generation Tests**: Updated to expect `.subckt` definitions instead of direct device lines
- **Pipeline Tests**: Updated to expect real PDK device names (`nfet_03v3`, `pfet_03v3`)
- **Port Resolution Tests**: Created missing fixtures and updated device line expectations
- **PySpice Integration**: Simplified parameter testing to work around PySpice limitations
- **Result**: 126/126 tests passing (was 11 failures, now 0 failures)

### **NEW**: Parser Refactoring & Location Tracking (Linter Foundation) ✅
**ACHIEVEMENT**: Successfully refactored the ASDL parser into a pure, non-validating parser and implemented line/column tracking for high-quality diagnostics.
- **Architecture**: Separated parsing from validation. The parser's sole responsibility is now to convert YAML into raw data objects.
- **Technology**: Integrated `ruamel.yaml` library, replacing `PyYAML`, to enable location tracking.
- **Location Data**: Implemented logic to extract and store `start_line` and `start_col` for parsed objects, starting with `FileInfo`. A `Locatable` base class was created for reusability.
- **TDD Process**: Followed a strict test-driven development cycle to rewrite the parser's test suite from scratch, ensuring the new implementation is robust and well-tested.
- **Impact**: This is a foundational step for the ASDL Linter, as it allows for precise, user-friendly error reporting (e.g., "Error on line 15, column 5").

### **Architecture Validation**: Tests Confirm Hierarchical Design ✅
- **Models as Subcircuits**: All device models generate as `.subckt` definitions
- **Instance Calls**: All instances generate as `X_` prefixed subcircuit calls
- **Real PDK Integration**: Tests validate actual PDK device lines work correctly
- **Parameter Propagation**: Tests confirm enhanced parameter handling system

### Phase 4 Achievements: End-to-End Simulation Validation ✅
- ✅ **Perfect User Workflow**: xschem → netlist → copy device_line → ASDL → SPICE → ngspice (ZERO manual intervention)
- ✅ **ngspice Expression Handling**: Expressions preserved exactly as-is from xschem netlists work perfectly
- ✅ **Devcontainer Enhancement**: Full repository mounted at `/foss/asdl` with EDA tools properly configured
- ✅ **Complete Testbench Suite**: 6 simulation types validated (OP, DC transfer, switching, AC, propagation delay, load capacitance)
- ✅ **PDK Integration**: GF180MCU PDK models (`nfet_03v3`, `pfet_03v3`) working correctly
- ✅ **Smart Expression Resolution**: ngspice automatically resolves `ad='int((nf+1)/2) * W/nf * 0.18u'` using hard-coded values from same line

### Phase 3 Achievements: Enhanced Parameter Handling
- ✅ **Enhanced Schema**: New `device_line` + `parameters` approach for robust PDK integration
- ✅ **Consistent Field Names**: Standardized `doc` field across models and modules  
- ✅ **Automatic Parameter Generation**: Parameters auto-appended to device lines
- ✅ **Clean Separation**: Device definition separate from parameterization
- ✅ **Backward Compatibility**: Legacy `model` + `params` still supported

### Current Hierarchical Output Format with Enhanced Parameters
```spice
* Model subcircuit definitions
* NMOS transistor unit cell
.subckt nmos_unit G D S B
  .param M=1                           # ✅ Parameter declaration
  MN D G S B nch_lvt W=1u L=0.1u M={M} # ✅ Auto-generated parameter reference
.ends

* Instance calls with parameter propagation
X_MP in out vdd vdd pmos_unit M=2      # ✅ Parameter override
```

## Key Decisions

### Net Declaration Validation Design (NEW - CRITICAL DECISIONS)  
**✅ LESSON LEARNED**: Connectivity validation catches critical design errors early
- **Comprehensive Checking**: Validate all net names in mappings against declared ports and internal nets
- **Pattern Expansion Support**: Correctly handle pattern expansion (`out_<p,n>` → `out_p`, `out_n`)
- **Non-Breaking Philosophy**: Generate helpful warnings but continue netlisting successfully
- **Module-Level Reporting**: Clear identification of which module has undeclared nets
- **Real-World Impact**: Catches actual connectivity issues like the ota_5t module problem
- **Integration Strategy**: Leverage existing pattern expansion logic for consistency
- **Warning Quality**: Specific, actionable messages that help developers fix connectivity issues

**✅ CRITICAL VALIDATION**: Fixed silent connectivity errors
- **Problem**: Undeclared nets in mappings could cause silent circuit failures
- **Example**: `out_n` and `out_<p,n>` used in ota_5t but not declared as ports or internal nets
- **Solution**: Comprehensive net declaration validation with pattern expansion support
- **Impact**: Developers immediately see connectivity issues during netlisting
- **Test Coverage**: Real-world scenario testing ensures robustness

### Unused Component Validation Design (PREVIOUS - CRITICAL DECISIONS)
**✅ LESSON LEARNED**: Validation should be helpful, not disruptive
- **Non-Breaking Philosophy**: Warnings guide developers but don't block netlisting
- **Global Instantiation Tracking**: Usage determined by scanning ALL modules for instantiations, not just reachable ones
- **No False Positives**: Components used within unused modules are correctly NOT flagged as unused
- **Top Module Exception**: Top module is never considered "unused" since it's the entry point
- **Warning Clarity**: Clear, actionable warning messages that identify specific unused components
- **Integration Strategy**: Leverage existing warning infrastructure for consistency

**✅ CRITICAL FIX**: Fixed cascading false positive warnings
- **Problem**: Components used within unused modules were incorrectly flagged as unused
- **Example**: `jumper` used in `bias_gen` → both flagged as unused when only `bias_gen` should be
- **Solution**: Changed from "reachable from top" to "instantiated anywhere" tracking
- **Impact**: Prevents noise in large hierarchies, focuses warnings on actual dead code
- **Test Coverage**: Added regression test to prevent this issue in future

### Pattern Expansion Rules (CRITICAL LESSON LEARNED)
**✅ LESSON LEARNED**: Mapping format correction for pattern expansion
- **WRONG**: `G_<p,n>: in_<p,n>` (pattern on both sides)
- **CORRECT**: `G: in_<p,n>` (model port name maps to expanded net pattern)
- **Core Principle**: Model ports are fixed device terminals (G, D, S, B), only the connected nets have patterns
- **Rationale**: 
  - Model defines fixed interface (G, D, S, B ports)
  - Instance expansion creates multiple copies of the same device
  - Each copy connects to different nets via pattern expansion on right-hand side
  - Left-hand side stays literal because device ports don't change
- **Applied Corrections**:
  - Updated `doc/ASDL_schema` examples and documentation
  - Fixed `examples/two_stage_ota.yml` mappings
  - Corrected expansion rule explanations
- **Impact**: This affects all pattern expansion implementation and validation

### Architecture Decisions (Confirmed)
1. **Pattern Expansion**: Keep patterns (`<p,n>`, `[3:0]`) in data structures, expand only during SPICE generation as explicit step (similar to Verilog elaboration)
2. **Parameter Resolution**: Keep original expressions (`$param`), make parameter evaluation an explicit step
3. **Model Mapping**: Use `model` field value as-is for PDK model card names
4. **Port Constraints**: Placeholder implementation, defer until basics are working
5. **Instance Intent**: Save as free-form dictionary metadata for later use
6. **Module Hierarchy**: Each `module` translates to a `.subckt` definition
7. **Implementation Approach**: Minimum viable product to get ASDL->SPICE flow working ASAP
8. **Validation Strategy**: Non-breaking warnings that improve developer experience

### PySpice Integration Decisions
9. **Validation Strategy**: Use PySpice for SPICE syntax validation and connectivity verification
10. **Enum Serialization**: Custom JSON encoder handles all enum types for debugging output
11. **Case Handling**: SPICE comparisons use lowercase normalization for case-insensitive validation
12. **Port Name Standards**: Use uppercase port names (G, D, S, B) to match ASDL conventions

### ✅ Hierarchical Subcircuit Design (IMPLEMENTED)
**COMPLETED**: Models are now subcircuit definitions for modularity and extensibility

**Rationale**:
- `nmos_unit` can be complex (cascode, parasitics, composite devices)
- Industry standard approach matches foundry PDK structure
- Enables reusable, hierarchical design methodology
- Clear separation between model interface and implementation

**Implementation**:
- Models generate as `.subckt` definitions with primitive devices inside
- Instances generate as subcircuit calls with `X_` prefix
- Two-level port resolution: Level 1 (model → SPICE order), Level 2 (instance → model order)
- Pipeline order: models → modules → main → .end

### ✅ Enhanced Parameter Handling (NEW - PHASE 3)
**COMPLETED**: Robust parameter handling system with automatic parameter generation

**Key Design Decisions**:
13. **Schema Enhancement**: Added `device_line` + `parameters` fields to DeviceModel
14. **Field Consistency**: Standardized on `doc` field for both models and modules (not `description`)
15. **Automatic Parameter Appending**: Parameters automatically added to device lines as `param={param}`
16. **Clean Device Lines**: Core device definition separate from parameter references
17. **Error-Resistant Design**: No manual parameter formatting required

**Enhanced Schema Format**:
```yaml
models:
  nmos_unit:
    doc: "NMOS transistor unit cell"           # ✅ Consistent field name
    type: nmos
    ports: [G, D, S, B]
    device_line: |                             # ✅ Clean core definition
      MN {D} {G} {S} {B} nch_lvt W=1u L=0.1u
    parameters:                                # ✅ Separate parameterization
      M: 1
```

**Rationale**:
- **Robustness**: Copy exact PDK device lines from real schematics without error-prone manual parameter formatting
- **Maintainability**: Change parameters without touching device_line content
- **Scalability**: Works with any complexity of PDK device lines (like from xschem)
- **Separation of Concerns**: Core device definition vs parameterization clearly separated

## Recent Changes

### ✅ Port Mapping Validation Bug Fix (NEW - CRITICAL FIX) 
- **Issue Discovered**: Silent failure in port mapping validation - system was inserting `UNCONNECTED` instead of reporting errors
- **Root Cause**: Instance mappings were not validated against module port definitions
- **Example Bug**: `miller_comp` defines ports `[plus, minus]` but instance mapped to `[in, out, vss]` - silently failed
- **Solution Implemented**: Added `_validate_port_mappings()` method in SPICEGenerator
- **Validation Logic**: 
  - Checks all mapped ports exist in module definition
  - Reports clear error messages with invalid port names
  - Maintains UNCONNECTED behavior for intentionally unmapped ports
- **Test Coverage**: Added 2 comprehensive validation tests
- **Impact**: Prevents silent circuit errors and improves debugging experience
- **Fixed Example**: Corrected `two_stage_ota.yml` Miller compensation mapping to use proper port names

### ✅ Phase 5: Instance Documentation & Schema Robustness (NEW - COMPLETE)
- **Instance Documentation**: Added `doc` field as first-class citizen for instance documentation
- **SPICE Comment Generation**: Instance documentation converts to SPICE comments before instance lines
- **Pattern Expansion Fix**: Fixed Pattern Expander to preserve `doc` field during expansion
- **Schema-Robust Expansion**: Replaced manual field copying with `dataclasses.replace()` for future-proofing
- **Comprehensive Testing**: 7 new documentation tests + 6 schema robustness tests
- **Module Parameter Generation**: Fixed modules to generate `.param` declarations like models
- **Instance Naming Consistency**: All instances use `X_{name}` format (both device and module instances)
- **NoneType Parameter Fix**: Fixed generator to handle new vs legacy parameter field properly

**Key Improvements**:
- **Documentation Parity**: Instance documentation now works just like Python docstrings
- **Future-Proof Expansion**: Uses `dataclasses.replace()` to automatically inherit ALL fields
- **Complete Pipeline**: Parser → Expander → Generator all handle `doc` field correctly
- **Real-World Validation**: Two-stage OTA example shows documentation comments in generated SPICE
- **Robust Architecture**: Pattern expansion will automatically work with any future Instance schema changes

### ✅ Phase 5: Schema Refinement & Language Documentation (COMPLETE)
- **Schema v0.5**: Cleaned up and simplified ASDL schema structure
- **Language Documentation**: Created comprehensive `doc/language.md` with semantic rules
- **Mapping Rules Codified**: Explicitly documented "Expansion only on the RHS" rule
- **Best Practices**: Defined clear guidelines for ASDL usage
- **Future Extensions**: Documented planned enhancements
- **Validation**: New documentation validates the mapping format lesson learned

**Key Improvements**:
- Removed verbose examples and complexity from schema
- Separated semantic rules into dedicated language documentation
- Cleaner parameter definition with explicit types and units
- Simplified metadata structure with `design_intent` and `layout` sections
- Clear distinction between literal `<p,n>` and bus `[N:M]` expansion patterns

### ✅ Phase 4: Schema Documentation Update (COMPLETE)
- **Schema Refinement**: Updated ASDL_schema_v0p4 documentation with latest enhancements
- **Field Updates**: Corrected `file_info` → `design_info` naming
- **Enhanced Model Format**: Documented new `device_line` + `parameters` approach with comprehensive examples
- **Real PDK Integration**: Added examples showing complex device lines with expressions from GF180MCU PDK
- **User Workflow Documentation**: Documented perfect xschem → ASDL → ngspice workflow
- **Automatic Parameter Generation**: Documented how parameters are auto-appended to device lines

### ✅ Phase 3: Parameter Handling Enhancement (COMPLETE)

#### **Enhanced Schema Implementation ✅**
- **New DeviceModel Fields**: Added `device_line` (raw PDK line) and `parameters` (parameterizable values)
- **Field Consistency**: Standardized on `doc` field (replaced `description` for consistency with modules)
- **Backward Compatibility**: Preserved legacy `model` + `params` fields with fallback logic
- **Parser Updates**: Enhanced to recognize new fields and maintain backward compatibility

#### **Automatic Parameter Generation ✅**
- **Core Innovation**: Device lines automatically get parameters appended (`M={M}`)
- **Clean Separation**: Core device definition separate from parameter references
- **Error Prevention**: No manual parameter formatting = no typos or formatting errors
- **Implementation**: Generator automatically appends `param={param}` for all entries in `parameters` dict

#### **Robust PDK Integration Ready ✅**
- **Real-World Ready**: Can handle complex PDK device lines from xschem/foundry netlists
- **Example Capability**: Can now handle lines like:
  ```
  XM1 {D} {G} {S} {B} nfet_03v3 L=0.5u W=4u nf=2 ad='...' as='...' pd='...' ps='...' nrd='...' nrs='...' sa=0 sb=0 sd=0
  ```
- **Parameter Flexibility**: Any number of parameters automatically handled
- **Maintenance Free**: Change parameters without touching complex device line expressions

### **Current Enhanced Output Format**
```spice
* Model subcircuit definitions
* NMOS transistor unit cell
.subckt nmos_unit G D S B
  .param M=1                           # Parameter declaration with default
  MN D G S B nch_lvt W=1u L=0.1u M={M} # Auto-assembled with parameter reference
.ends

* Instance calls with parameter propagation
X_MP in out vdd vdd pmos_unit M=2      # Parameter override at instance level
```

## Linter & Compiler Architecture Refactor

A major architectural refactoring was designed to support a new standalone linter while maximizing code reuse with the existing compiler.

### Key Decisions
1.  **Shared Analysis Pipeline**: Both the linter and compiler will use a shared "Middle-End" analysis pipeline. This prevents code duplication for validation logic.

2.  **Multi-Stage Validation**: Validation is treated as a continuous process.
    -   **Stage 1 (Expander)**: `PatternExpander` is the first analysis stage. It no longer raises exceptions on errors (e.g., mismatched pattern counts). Instead, it logs them as `Diagnostic` objects and continues where possible.
    -   **Stage 2 (Validator)**: A new `Validator` module will contain all semantic checks (e.g., undeclared nets, unused components). It takes the output of the expander and appends its own findings to the list of diagnostics.

3.  **Standardized Diagnostics**: A new `diagnostics.py` module will define common data structures (`Diagnostic`, `DiagnosticLevel`) to be used by all analysis stages.

4.  **Decoupled Back-Ends**:
    -   **Linter**: The linter is a simple back-end that runs the full analysis pipeline and then formats and prints the final list of diagnostics.
    -   **Compiler**: The compiler runs the same analysis pipeline, but first checks for fatal errors in the diagnostics list before proceeding to the `SPICEGenerator`.

5.  **Data Structure Refactoring**: We decided on several key improvements to the core data structures:
    -   **Serialization Logic Removed**: All `to_json`, `to_yaml`, and `save_to_file` methods will be removed from `ASDLFile` and moved to a dedicated `serialization.py` module, making the data classes pure data containers.
    -   **`DeviceModel` Simplified**: All legacy fields (`model`, `params`) will be removed to enforce a single, robust `device_line`-based workflow.
    -   **`PrimitiveType` Enum Introduced**: A new `PrimitiveType` enum (`PDK_DEVICE`, `SPICE_DEVICE`) will replace the old `DeviceType` to provide a clear, unambiguous classification based on the primitive's origin.
    -   **`Nets` Class Removed**: The `Nets` class is redundant. It will be replaced by a simpler `internal_nets: List[str]` field directly on the `Module` class for clarity.

## Open Questions  
1. ✅ **Pattern Expansion Rules Defined**: Comprehensive literal expansion rules documented in `doc/pattern_expansion_rules.md`

2. **Parameter Resolution**: What's the best approach for `$param` variable substitution in complex expressions?

3. **Net Naming**: What conventions should we use for internal net names and port connections?

4. **Error Handling**: How should we handle unconnected ports and missing model references in SPICE output?

5. **SPICE Comments**: How much metadata (doc, intent) should be included as comments in generated SPICE?

## Backlog Items
- **Pattern Expansion**: Implement `<p,n>` and `[3:0]` pattern expansion
- **Parameter Resolution**: Implement `$param` variable substitution
- **Advanced Validation**: Enhance SPICE validation beyond syntax checking
- **Parameter Order Consistency**: Make parameter ordering deterministic (use model-defined order) - **LOW PRIORITY**

## Completed Questions
- **Class Structure**: ✅ Implemented with comprehensive data structures
- **Parser Implementation**: ✅ Complete with future-proofing and TDD
- **Validation Level**: ✅ Implemented configurable strict/lenient validation
- **Port Ordering**: ✅ **CRITICAL**: Models define port order, instances use named mapping
- **PySpice Integration**: ✅ Complete validation layer for SPICE syntax and connectivity 
- **Hierarchical Design**: ✅ Complete subcircuit-based hierarchical methodology 
- **Parameter Handling**: ✅ **NEW**: Robust automatic parameter generation system implemented

- **Data Structure Refactoring Plan (Session of YYYY-MM-DD):**
  - **Decouple Serialization:** All serialization logic (e.g., `to_yaml`, `to_json`) will be moved from `src/asdl/data_structures.py` into a new, dedicated `src/asdl/serialization.py` module to improve separation of concerns.
  - **Simplify DeviceModel:** The `DeviceModel` will be streamlined to use a single, robust `device_line` approach, removing legacy fields (`model`, `params`). The `DeviceType` enum will be replaced with a clearer `PrimitiveType` enum (`PDK_DEVICE`, `SPICE_DEVICE`).
  - **Streamline Net Declaration:** The nested `Nets` class will be removed and replaced by a direct `internal_nets: Optional[List[str]]` field on the `Module` class.
  - **Universal Metadata:** A free-form `metadata: Optional[Dict[str, Any]]` field will be added to all major ASDL data structures to provide a uniform and extensible way to store annotations and design intent, replacing the `Instance.intent` field.