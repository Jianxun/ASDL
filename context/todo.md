# Project Todo List

## Current Sprint - Pattern Expansion & Advanced Features (PHASE 5)

### 🎉 **SCHEMA DOCUMENTATION UPDATE COMPLETED ✅**
- [X] **Schema Refinement** ✅
  - [X] Updated ASDL_schema_v0p4 with latest Phase 3 & 4 enhancements ✅
  - [X] Corrected field naming: `file_info` → `design_info` ✅
  - [X] Enhanced model format documentation with `device_line` + `parameters` approach ✅
  - [X] Added comprehensive real PDK examples from inverter.yml ✅
  - [X] Documented perfect user workflow (xschem → ASDL → ngspice) ✅
  - [X] Added automatic parameter generation explanation ✅

### 🎉 **PHASE 4 COMPLETED ✅** (ngspice Simulation Testing & User Workflow Validation)
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

## PHASE 5: Pattern Expansion & Advanced Features (CURRENT PRIORITY)

### **Core Objective: Implement Advanced ASDL Features**
**Goal**: Add pattern expansion, parameter resolution, and complex circuit support while maintaining the perfect user workflow

### **Phase 5 Tasks**
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
- [ ] **Pattern Expansion System Implementation** (CURRENT PRIORITY - TDD)
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
  - [ ] **Step 4: Integration & Pipeline Tests** (CURRENT PRIORITY)
    - [ ] **End-to-End Pattern Expansion Tests** (15 comprehensive test cases)
      - [ ] **Category 1: Single Pattern Type Tests** (3 tests)
        - [ ] Basic Port Pattern Expansion (port `data_<p,n>` → `data_p, data_n`)
        - [ ] Basic Mapping Pattern Expansion (mapping `G: in_<p,n>` → expanded nets)
        - [ ] Basic Instance Pattern Expansion (instance `diff_<p,n>` → separate instances)
      - [ ] **Category 2: Combined Pattern Tests** (3 tests)
        - [ ] Port + Mapping Patterns (synchronized expansion)
        - [ ] Instance + Mapping Patterns (instance duplication with expanded connections)
        - [ ] Full Pattern Integration (all pattern types working together)
      - [ ] **Category 3: Real-World Circuit Tests** (3 tests)
        - [ ] Differential Pair Circuit (complete `<p,n>` expansion)
        - [ ] Current Mirror Array (instance patterns for multiple branches)
        - [ ] Hierarchical Circuit with Patterns (multi-level expansion)
      - [ ] **Category 4: Integration & Pipeline Tests** (3 tests)
        - [ ] Pattern Expansion + Parameter Handling (integration with Phase 3)
        - [ ] Pattern Expansion + Subcircuit Generation (integration with Phase 2)
        - [ ] End-to-End YAML → SPICE Pipeline (complete pipeline validation)
      - [ ] **Category 5: Edge Cases & Error Handling** (3 tests)
        - [ ] Mixed Pattern/Non-Pattern Components (selective expansion)
        - [ ] Invalid Pattern Combinations (error handling validation)
        - [ ] Large Pattern Expansion (scalability testing)
    - [ ] **Pipeline Integration Implementation**
      - [ ] Add expansion step to SPICE generation pipeline
      - [ ] Update generator to call pattern expansion before SPICE generation
      - [ ] Ensure expansion preserves existing functionality
    - [ ] **Integration Validation**
      - [ ] Verify pattern expansion works with hierarchical subcircuits
      - [ ] Validate parameter propagation through expanded instances
      - [ ] Confirm ngspice simulation compatibility

- [ ] **Parameter Resolution Enhancement**
  - [ ] Implement `$param` variable substitution system
  - [ ] Support parameter inheritance and scoping
  - [ ] Maintain expression evaluation as explicit step
  - [ ] Preserve original expressions until resolution

- [ ] **Complex Circuit Support**
  - [ ] Multi-level hierarchical circuit support
  - [ ] Advanced PDK device structures (composite devices)
  - [ ] Parasitic element handling
  - [ ] Complex parameter dependencies

- [ ] **Advanced Validation & Testing**
  - [ ] Pattern expansion test suite
  - [ ] Parameter resolution validation
  - [ ] Complex circuit simulation validation
  - [ ] Performance benchmarking for large circuits

### **Success Criteria**
- [ ] Pattern expansion works seamlessly with user workflow
- [ ] Parameter resolution maintains expression fidelity
- [ ] Complex circuits simulate correctly in ngspice
- [ ] Advanced features don't break existing functionality

## Future Phase 6: Advanced Integration & Optimization

### **Pattern Expansion System**
- [ ] Complex model support (multiple internal devices)
- [ ] Parasitic element handling
- [ ] Composite device structures
- [ ] Parameter resolution system
- [ ] Pattern expansion system (`<p,n>`, `[3:0]`)

## Next Sprint: Advanced Parameter Handling & Features

### **Hierarchical Parameter System** (NEW - PRIORITY)
- [ ] **Parameter Inheritance & Scoping**
  - [ ] Design parameter inheritance model (module → instance → device)
  - [ ] Implement parameter scoping rules (local overrides global)
  - [ ] Support multi-level parameter propagation
  - [ ] Handle parameter conflicts and resolution order
- [ ] **Advanced Parameter Features**
  - [ ] Parameter expressions with dependencies (`W = $L * aspect_ratio`)
  - [ ] Conditional parameters based on technology/process
  - [ ] Parameter validation and constraint checking
  - [ ] Default parameter inheritance from model definitions
- [ ] **Integration with Pattern Expansion**
  - [ ] Parameter propagation through expanded instances
  - [ ] Pattern-specific parameter overrides
  - [ ] Scoped parameters within expanded subcircuits
  - [ ] Performance optimization for large parameter sets

### **ASDLFile Round-trip & Debug Features**
- [X] **JSON Export**: Custom enum serialization for debugging ✅
- [X] **Manual Inspection**: Generated files saved to `/tests/unit_tests/generator/results/` ✅
- [ ] Add `save_to_file(filepath: str)` method to `ASDLFile` class
- [ ] Add `to_yaml()` method to convert `ASDLFile` back to YAML string
- [ ] Ensure round-trip preservation of YAML structure and data integrity (original `ASDLFile` only)
- [ ] Write tests for round-trip functionality (YAML → ASDLFile → YAML) - original data only
- [ ] Document round-trip limitation: only guaranteed before pattern expansion/parameter resolution

## Backlog Items

### **Future Pattern Expansion Features**
- [ ] **Array Expansion with `[]`**: Implement `data[3:0]` → `data[3], data[2], data[1], data[0]`
- [ ] **Combined Patterns**: Support `data_<p,n>[3:0]` (literal + array patterns)
- [ ] **Parameter-Based Sizing**: Support `data[N-1:0]` with parameter N

### **Parameter Handling & Port Mapping**
- [ ] **Parameter Order Consistency**: Make parameter ordering deterministic (use model-defined order) - **LOW PRIORITY**
- [ ] Advanced port constraint processing
- [ ] Net name sanitization and validation
- [ ] Unconnected port error handling

### **Enhanced Features**
- [ ] Support for multiple SPICE dialects (ngspice, spectre, etc.)
- [ ] Validation and error checking for ASDL inputs
- [ ] Layout intent handling and export
- [ ] Parameter optimization hints
- [ ] Integration with circuit simulators
- [ ] GUI or CLI interface for conversion

### **Documentation & Examples**
- [ ] Create comprehensive API documentation
- [ ] Add more example ASDL circuits
- [ ] Create tutorial/getting started guide
- [ ] Document design patterns and best practices

### **Testing & Quality**
- [X] Unit tests for all core components ✅ **15/21 FUNCTIONAL TESTS PASSING**
- [ ] Integration tests with real circuits
- [ ] Performance benchmarking
- [ ] Code coverage analysis
- [ ] Static type checking setup

## Completed Tasks

### **Phase 4: ngspice Simulation Testing & User Workflow Validation ✅ COMPLETE**
- [X] **Perfect User Workflow Implementation** ✅
  - [X] Validated xschem → netlist → copy device_line → ASDL → SPICE → ngspice workflow ✅
  - [X] Preserved device_line expressions exactly as-is from xschem netlists ✅
  - [X] Confirmed ngspice automatically resolves complex expressions using hard-coded values ✅
  - [X] Achieved ZERO manual intervention required for user workflow ✅

- [X] **Devcontainer Environment Perfection** ✅
  - [X] Enhanced devcontainer configuration to mount full repository at `/foss/asdl` ✅
  - [X] Maintained `/foss/designs` compatibility for EDA tools ✅
  - [X] Verified ngspice accessibility and proper PATH configuration ✅
  - [X] Enabled concurrent ASDL development and EDA tool usage ✅

- [X] **PDK Integration Excellence** ✅
  - [X] Updated ASDL YAML to use correct GF180MCU PDK models (`nfet_03v3`, `pfet_03v3`) ✅
  - [X] Validated complex device lines with expressions work exactly as copied from xschem ✅
  - [X] Confirmed automatic expression resolution without parameter extraction ✅
  - [X] Demonstrated real-world PDK compatibility ✅

- [X] **Comprehensive Simulation Validation** ✅
  - [X] Operating Point Analysis: DC bias point validation ✅
  - [X] DC Transfer Characteristic: Input sweep analysis ✅
  - [X] Switching Transient Analysis: Digital pulse response ✅
  - [X] AC Small-Signal Response: Frequency domain analysis ✅
  - [X] Propagation Delay Measurement: Timing characterization ✅
  - [X] Load Capacitance Analysis: Drive capability testing ✅

### **Phase 3: Parameter Handling Enhancement ✅ COMPLETE**
- [X] **Enhanced Schema Design** ✅
  - [X] Added `device_line` field for raw PDK device lines with `{port}` placeholders
  - [X] Added `parameters` field for parameterizable values with defaults
  - [X] Standardized on `doc` field (replaced `description` for consistency)
  - [X] Maintained backward compatibility with legacy fields

- [X] **Automatic Parameter Generation** ✅
  - [X] Implemented automatic parameter appending: `M={M}` auto-generated from `parameters: {M: 1}`
  - [X] Clean separation: device definition vs parameterization
  - [X] Error-resistant: no manual parameter formatting required
  - [X] Scalable: supports any number of parameters

- [X] **Implementation & Integration** ✅
  - [X] Updated DeviceModel data structure with new fields and helper methods
  - [X] Enhanced parser to recognize new fields while maintaining backward compatibility
  - [X] Modified generator to use automatic parameter generation approach
  - [X] Updated test fixtures to use new schema format
  - [X] Verified end-to-end functionality with complete SPICE generation

### **Phase 2: Hierarchical Subcircuit Refactor ✅ COMPLETE**
- [X] **Step 1: Model Subcircuit Generation** ✅
  - [X] Added `generate_model_subcircuit()` method
  - [X] Models converted to `.subckt` definitions with primitive devices inside
  - [X] Identity port mapping within model subcircuits
  - [X] Proper SPICE device order maintained (D G S B for MOSFETs)

- [X] **Step 2: Instance Generation with X_ Prefix** ✅
  - [X] Updated `_generate_device_line()` to create subcircuit calls
  - [X] Device instances now generate as `X_` prefixed subcircuit calls
  - [X] Named port resolution implemented (order-independent)
  - [X] Model-defined port order used for subcircuit interface

- [X] **Step 3: Two-Level Port Resolution** ✅
  - [X] Level 1: ASDL model ports → SPICE device order (strict, identity mapping)
  - [X] Level 2: Instance mappings → Model ports (named, order-independent)
  - [X] Verified: reordered YAML mappings produce identical SPICE output
  - [X] Order independence confirmed through comprehensive testing

- [X] **Step 4: Generator Pipeline Update** ✅
  - [X] Pipeline order: Model subcircuits → Module subcircuits → Main → .end
  - [X] ngspice compatibility: `.subckt`/`.ends` pairing, indentation, X-prefix
  - [X] Proper SPICE file structure and formatting
  - [X] All pipeline structure tests passing

### **Phase 1: Foundation ✅ COMPLETE**
- [X] Initial project structure review
- [X] Context directory and files setup  
- [X] Project requirements analysis
- [X] Schema field name update: `design_info` → `file_info`
- [X] **Complete ASDL parser implementation with comprehensive test suite (44 passing tests)**
- [X] **Future-proofing parser with extensibility features and validation modes**
- [X] **Error handling and backward compatibility for schema versions**
- [X] **Device generation with template system (7 passing tests)**
- [X] **PySpice integration with validation layer (6 passing tests)**
- [X] **Case sensitivity resolution and enum serialization**
- [X] **Port mapping analysis and requirements definition**
- [X] **Manual inspection files for debugging**

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