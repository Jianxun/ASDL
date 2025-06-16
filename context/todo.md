# Project Todo List

## Current Sprint - Hierarchical Subcircuit Refactor

### PHASE 1 COMPLETED ✅
- [X] **ASDL Parser**: 44 passing tests, complete YAML parsing with future-proofing
- [X] **SPICE Generator Phase 1**: 7 passing device generation tests with template system  
- [X] **PySpice Integration**: 6 passing validation tests with enum serialization
- [X] **Test Infrastructure**: 57 total passing tests, manual inspection files generated
- [X] **Port Mapping Analysis**: Critical discovery of port order requirements

### **PHASE 2: Hierarchical Subcircuit Implementation (CURRENT PRIORITY)**

#### **Critical Architecture Change**
**Goal**: Convert models from primitive devices to subcircuit definitions
- Current: `models` → primitive device lines (limited)  
- Target: `models` → `.subckt` definitions (extensible, hierarchical)

#### **Core Implementation Tasks**
- [ ] **Refactor 1: Model Subcircuit Generation**
  - [ ] Create `generate_model_subcircuits()` method
  - [ ] Convert each model to `.subckt` definition with proper port order
  - [ ] Handle primitive devices (NMOS/PMOS) as single-device subcircuits
  - [ ] Ensure SPICE device order within subcircuits (D G S B for MOSFETs)

- [ ] **Refactor 2: Instance Generation with X_ Prefix**
  - [ ] Update `generate_instance()` to create subcircuit calls  
  - [ ] Add automatic `X_` prefix to instance names
  - [ ] Implement named port resolution (order-independent mappings)
  - [ ] Use model-defined port order for subcircuit interface

- [ ] **Refactor 3: Two-Level Port Resolution**
  - [ ] **Level 1**: ASDL model ports → SPICE device order (strict)
  - [ ] **Level 2**: Instance mappings → Model ports (named, order-independent)
  - [ ] Resolve `{D: out, G: in, S: vdd}` to model port sequence

- [ ] **Refactor 4: Generator Pipeline Update**
  - [ ] Update main `generate()` method to output models first, then modules
  - [ ] Ensure proper SPICE file structure: models → modules → main instantiation
  - [ ] Maintain PySpice compatibility

#### **Expected Output Format**
```spice
* Model definitions as subcircuits
.subckt nmos_unit G D S B
  MN D G S B nch_lvt W=1u L=0.1u
.ends

.subckt pmos_unit G D S B  
  MP D G S B pch_lvt W=1u L=0.1u
.ends

* Main circuit using subcircuit calls
.subckt inverter in out vdd vss
  X_MP in out vdd vdd pmos_unit M=2
  X_MN in out vss vss nmos_unit M=2
.ends
```

#### **Testing Strategy**
- [ ] Update existing PySpice integration tests to expect subcircuit structure
- [ ] Add model subcircuit generation tests
- [ ] Add `X_` prefix validation tests  
- [ ] Add named port resolution tests (verify order independence)
- [ ] Ensure all 57 tests continue to pass after refactor

### **Future Phase 3: Advanced Features**
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

### **Port Mapping & Parameter Handling**
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
- [X] Unit tests for all core components ✅ **57 PASSING TESTS**
- [ ] Integration tests with real circuits
- [ ] Performance benchmarking
- [ ] Code coverage analysis
- [ ] Static type checking setup

## Completed Tasks

### **Phase 1: Foundation ✅**
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

## Future Sprints
- [ ] Create comprehensive test suite for end-to-end pipeline

## Completed Tasks
- [X] Initial project structure review
- [X] Context directory and files setup
- [X] Project requirements analysis
- [X] Schema field name update: `design_info` → `file_info`
- [X] Basic data structure implementation with placeholders
- [X] Processing pipeline class structure setup
- [X] **Complete ASDL parser implementation with comprehensive test suite (44 passing tests)**
- [X] **Future-proofing parser with extensibility features and validation modes**
- [X] **Error handling and backward compatibility for schema versions**
- [X] **Unknown field detection and intent metadata preservation**
- [X] Updated implementation plan to reflect current sprint focus 