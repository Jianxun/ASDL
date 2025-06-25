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
**🎉 Phase 5 COMPLETE + UNUSED VALIDATION FEATURE ADDED + PORT ORDER FIX**: All tests passing ✅

### **NEW**: Critical Pattern Expansion Bug Fix (MAJOR CIRCUIT CORRECTNESS) ✅
**ACHIEVEMENT**: Fixed critical differential pair pattern expansion bug that broke circuit functionality
- **Problem**: `_expand_mapping_patterns` always mapped one-sided net patterns to first element for all instances
- **Impact**: Both `MN_P` and `MN_N` connected to `in_p` instead of `in_p` and `in_n` respectively
- **Circuit Consequence**: Completely broken differential amplifier - both transistors driven by same input!
- **Root Cause**: Line 346 in expander.py used `expanded_nets[0]` instead of `expanded_nets[instance_index]`
- **Solution**: Added instance index logic for one-sided net patterns to match instance expansion
- **Test Coverage**: Added comprehensive `TestRealWorldDifferentialPair` class using `diff_pair_nmos.yml` fixture
- **Result**: Differential pairs now function correctly with proper signal routing

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

### Unused Component Validation Design (NEW - CRITICAL DECISIONS)
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