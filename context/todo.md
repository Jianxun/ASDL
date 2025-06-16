# Project Todo List

## Current Sprint - ngspice Simulation Testing (PHASE 4)

### 🎉 **PHASE 3 COMPLETED ✅** (Parameter Handling Enhancement)
**ALL CORE STEPS COMPLETE**:
- [X] **Enhanced Schema Implementation** ✅
  - [X] Add `device_line` field for raw PDK device lines with `{placeholders}` ✅
  - [X] Add `parameters` field for parameterizable values with defaults ✅
  - [X] Standardize on `doc` field for consistency with modules ✅
  - [X] Maintain backward compatibility with legacy `model` + `params` ✅

- [X] **Automatic Parameter Generation** ✅
  - [X] Implement automatic parameter appending to device lines ✅
  - [X] Clean separation: core device definition vs parameterization ✅
  - [X] Error-resistant design: no manual parameter formatting required ✅
  - [X] Support for any number of parameters ✅

- [X] **Parser & Generator Updates** ✅
  - [X] Update parser to recognize new `device_line` and `parameters` fields ✅
  - [X] Update generator to use automatic parameter generation ✅
  - [X] Implement backward compatibility fallback logic ✅
  - [X] Update test fixtures to use new schema format ✅

### **Enhanced Schema Format Now Supported** ✅
```yaml
models:
  nmos_unit:
    doc: "NMOS transistor unit cell"           # ✅ Consistent field naming
    type: nmos
    ports: [G, D, S, B]
    device_line: |                             # ✅ Clean PDK device line
      MN {D} {G} {S} {B} nch_lvt W=1u L=0.1u
    parameters:                                # ✅ Auto-appended as M={M}
      M: 1
```

### **Generated SPICE Output** ✅
```spice
* Model subcircuit definitions
* NMOS transistor unit cell
.subckt nmos_unit G D S B
  .param M=1                           # ✅ Parameter declaration
  MN D G S B nch_lvt W=1u L=0.1u M={M} # ✅ Auto-generated parameter reference
.ends

X_MP in out vdd vdd pmos_unit M=2      # ✅ Parameter override at instance
```

## PHASE 4: ngspice Simulation Testing (CURRENT PRIORITY)

### **Core Objective: Validate Generated Netlists with ngspice**
**Goal**: Verify that our generated SPICE netlists are simulatable and produce correct results

### **Phase 4 Tasks** (To be tackled in new chat)
- [ ] **ngspice Environment Setup**
  - [ ] Verify ngspice installation and basic functionality
  - [ ] Understand ngspice control file syntax and simulation commands
  - [ ] Set up basic DC/AC/transient simulation templates

- [ ] **Test Circuit Preparation**
  - [ ] Create simple test circuits (inverter, basic amplifier)
  - [ ] Add proper voltage sources and test conditions
  - [ ] Include PDK model files and process corner specifications
  - [ ] Set up simulation controls (.control blocks)

- [ ] **Simulation Validation**
  - [ ] Test basic DC operating point analysis
  - [ ] Verify device parameters and operating regions
  - [ ] Run transient simulations for dynamic behavior
  - [ ] Compare results with expected circuit behavior

- [ ] **Integration & Automation**
  - [ ] Create automated simulation test framework
  - [ ] Add simulation result validation and comparison
  - [ ] Document simulation setup and usage patterns
  - [ ] Integrate with existing test suite

### **Success Criteria**
- [ ] Generated SPICE netlists simulate successfully in ngspice
- [ ] Simulation results match expected circuit behavior
- [ ] Parameter variations work correctly (M=1 vs M=2)
- [ ] Both simple and complex PDK device lines simulate properly

## Future Phase 5: Advanced Features

### **Pattern Expansion System**
- [ ] Complex model support (multiple internal devices)
- [ ] Parasitic element handling
- [ ] Composite device structures
- [ ] Parameter resolution system
- [ ] Pattern expansion system (`<p,n>`, `[3:0]`)

## ASDLFile Round-trip & Debug Features (Next Sprint)
- [X] **JSON Export**: Custom enum serialization for debugging ✅
- [X] **Manual Inspection**: Generated files saved to `/tests/unit_tests/generator/results/` ✅
- [ ] Add `save_to_file(filepath: str)` method to `ASDLFile` class
- [ ] Add `to_yaml()` method to convert `ASDLFile` back to YAML string
- [ ] Ensure round-trip preservation of YAML structure and data integrity (original `ASDLFile` only)
- [ ] Write tests for round-trip functionality (YAML → ASDLFile → YAML) - original data only
- [ ] Document round-trip limitation: only guaranteed before pattern expansion/parameter resolution

## Backlog Items

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