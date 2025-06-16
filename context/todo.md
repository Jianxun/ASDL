# Project Todo List

## Current Sprint - Parameter Handling for Passive Devices (NEXT PHASE)

### 🎉 PHASE 2 COMPLETED ✅ (Hierarchical Subcircuit Refactor)
**ALL CORE STEPS COMPLETE**:
- [X] **Refactor 1: Model Subcircuit Generation** ✅
  - [X] Create `generate_model_subcircuit()` method ✅
  - [X] Convert each model to `.subckt` definition with proper port order ✅
  - [X] Handle primitive devices (NMOS/PMOS) as single-device subcircuits ✅
  - [X] Ensure SPICE device order within subcircuits (D G S B for MOSFETs) ✅

- [X] **Refactor 2: Instance Generation with X_ Prefix** ✅
  - [X] Update `generate_instance()` to create subcircuit calls ✅
  - [X] Add automatic `X_` prefix to instance names ✅
  - [X] Implement named port resolution (order-independent mappings) ✅
  - [X] Use model-defined port order for subcircuit interface ✅

- [X] **Refactor 3: Two-Level Port Resolution** ✅
  - [X] **Level 1**: ASDL model ports → SPICE device order (strict) ✅
  - [X] **Level 2**: Instance mappings → Model ports (named, order-independent) ✅
  - [X] Resolve `{D: out, G: in, S: vdd}` to model port sequence ✅

- [X] **Refactor 4: Generator Pipeline Update** ✅
  - [X] Update main `generate()` method to output models first, then modules ✅
  - [X] Ensure proper SPICE file structure: models → modules → main instantiation ✅
  - [X] Maintain PySpice compatibility ✅

### **Test Status: 15/21 Functional Tests Passing ✅**
- [X] **PySpice Integration**: 6/6 passing ✅ (CRITICAL - SPICE syntax validation)
- [X] **Port Resolution**: 3/3 passing ✅ (CRITICAL - hierarchical mapping)  
- [X] **Pipeline Structure**: 5/5 passing ✅ (CRITICAL - ngspice compatibility)
- [X] **Device Generation**: 1/7 passing ⚠️ (EXPECTED - 6 tests check old primitive format)

### **Current Output Format** ✅
```spice
* Model subcircuit definitions
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

XMAIN in out vdd vss inverter
.end
```

## PHASE 3: Parameter Handling Enhancement (CURRENT PRIORITY)

### **Core Issue: Passive Device Parameter Mismatch**
**Problem**: Passive devices (R, L, C) have parameter handling mismatch in hierarchical structure

**Current Incorrect Behavior**:
```spice
.subckt res_1k plus minus
  R plus minus RES_1K    # Missing value parameter!
.ends
X_R1 net1 net2 res_1k value=1k  # Value at wrong level
```

**Expected Correct Behavior** (Need to investigate):
```spice
.subckt res_1k plus minus value=1k
  R plus minus RES_1K {value}    # Parameter propagation
.ends
X_R1 net1 net2 res_1k value=1k  # Or alternative approach
```

### **Phase 3 Tasks**
- [ ] **Investigate Parameter Propagation Methods**
  - [ ] Research SPICE subcircuit parameter passing (`{param}` syntax)
  - [ ] Determine best approach for passive device `value` parameters
  - [ ] Consider alternative: inline value vs parameterized subcircuits

- [ ] **Implement Parameter Propagation**
  - [ ] Update model subcircuit generation for passive devices  
  - [ ] Handle `value` parameter correctly in model subcircuits
  - [ ] Ensure instance parameters propagate to model appropriately

- [ ] **Update Tests**
  - [ ] Fix failing device generation tests for new format
  - [ ] Add tests for parameter propagation
  - [ ] Verify passive device functionality

- [ ] **Validation**
  - [ ] Ensure PySpice compatibility with parameter changes
  - [ ] Test with ngspice for parameter propagation
  - [ ] Verify all device types work correctly

## Future Phase 4: Advanced Features

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