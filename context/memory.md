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

Schema structure:
- `file_info`: File metadata (top_module, doc, revision, author, date)
- `models`: Device/component templates with PDK mappings
- `modules`: Circuit hierarchy with ports, instances, and connectivity

## Current State
**🎉 Phase 2 COMPLETE**: Hierarchical Subcircuit Refactor
- ✅ **Phase 1**: ASDL Parser + SPICE Generator + PySpice Integration (44+7+6=57 tests)
- ✅ **Phase 2**: Hierarchical Subcircuit Implementation (15/21 functional tests passing)
  - ✅ **Step 1**: Model Subcircuit Generation - Models converted to `.subckt` definitions
  - ✅ **Step 2**: Instance Generation with X_ Prefix - Instances as subcircuit calls
  - ✅ **Step 3**: Two-Level Port Resolution - Order-independent named port mapping  
  - ✅ **Step 4**: Generator Pipeline Update - Correct ordering and ngspice compatibility
- 🔄 **Next Phase**: Parameter handling for passive devices (R, L, C value parameters)

### Test Status Summary
- **✅ PySpice Integration**: 6/6 passing (CRITICAL - validates SPICE syntax)
- **✅ Port Resolution**: 3/3 passing (CRITICAL - validates hierarchical mapping)
- **✅ Pipeline Structure**: 5/5 passing (CRITICAL - validates ngspice compatibility)
- **❌ Device Generation**: 6/7 failing (EXPECTED - tests old primitive format, we now use hierarchical)

## Key Decisions

### Architecture Decisions (Confirmed)
1. **Pattern Expansion**: Keep patterns (`<p,n>`, `[3:0]`) in data structures, expand only during SPICE generation as explicit step (similar to Verilog elaboration)
2. **Parameter Resolution**: Keep original expressions (`$param`), make parameter evaluation an explicit step
3. **Model Mapping**: Use `model` field value as-is for PDK model card names
4. **Port Constraints**: Placeholder implementation, defer until basics are working
5. **Instance Intent**: Save as free-form dictionary metadata for later use
6. **Module Hierarchy**: Each `module` translates to a `.subckt` definition
7. **Implementation Approach**: Minimum viable product to get ASDL->SPICE flow working ASAP

### PySpice Integration Decisions
8. **Validation Strategy**: Use PySpice for SPICE syntax validation and connectivity verification
9. **Enum Serialization**: Custom JSON encoder handles all enum types for debugging output
10. **Case Handling**: SPICE comparisons use lowercase normalization for case-insensitive validation
11. **Port Name Standards**: Use uppercase port names (G, D, S, B) to match ASDL conventions

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

## Recent Changes

### ✅ Phase 2: Hierarchical Subcircuit Refactor (COMPLETE)

#### **Step 1: Model Subcircuit Generation ✅**
- **Implementation**: Added `generate_model_subcircuit()` method
- **Result**: Each model becomes a `.subckt` definition with primitive device inside
- **Example**: `nmos_unit` becomes `.subckt nmos_unit G D S B` with `MN D G S B nch_lvt` inside
- **Status**: Working perfectly with identity port mapping

#### **Step 2: Instance Generation with X_ Prefix ✅**
- **Implementation**: Updated `_generate_device_line()` to create subcircuit calls
- **Result**: Device instances become `X_` prefixed subcircuit calls
- **Example**: `MP` instance becomes `X_MP in out vdd vdd pmos_unit M=2`
- **Status**: Working perfectly with named port resolution

#### **Step 3: Two-Level Port Resolution ✅**
- **Implementation**: Order-independent instance mapping resolution
- **Level 1**: ASDL model ports → SPICE device order (strict, identity in subcircuits)
- **Level 2**: Instance mappings → Model ports (named, order-independent)
- **Verification**: Reordered YAML mappings produce identical SPICE output
- **Status**: Working perfectly - order independence confirmed

#### **Step 4: Generator Pipeline Update ✅**
- **Implementation**: Correct SPICE pipeline ordering for ngspice compatibility
- **Pipeline Order**: Model subcircuits → Module subcircuits → Main instantiation → .end
- **ngspice Features**: Proper `.subckt`/`.ends` pairing, indentation, X-prefix calls
- **Status**: Working perfectly - all pipeline tests pass

### **Current Hierarchical Output Format**
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

## New Requirements (Next Phase)
### Parameter Handling for Passive Devices
- **Issue**: Passive devices (R, L, C) have `value` parameter handling mismatch
- **Current**: Instance `value` parameters go to subcircuit call, but model doesn't expect them
- **Expected**: Model subcircuits should handle `value` parameters appropriately
- **Example Problem**: 
  ```spice
  .subckt res_1k plus minus
    R plus minus RES_1K    # Missing value parameter
  .ends
  X_R1 net1 net2 res_1k value=1k  # Value parameter at wrong level
  ```
- **Target Solution**: Investigate proper parameter propagation for passive devices

### ASDLFile Round-trip Capability (Future Sprint)
- **Requirement**: `ASDLFile` class must support round-trip YAML conversion (YAML → `ASDLFile` → YAML)
- **Use Case**: Future modifications to `ASDLFile` instances need to be saved back to YAML format
- **Implementation**: Add `save_to_file(filepath: str)` method to `ASDLFile` class
- **Data Preservation**: Must preserve all original YAML structure, comments, and formatting where possible
- **Limitation**: Round-trip is only guaranteed for **original/raw** `ASDLFile` instances (before pattern expansion and parameter resolution)
- **Rationale**: After processing pipeline (expansion/resolution), the compact original representation is lost and cannot be recovered

### ASDLFile Debug Functionality  
- **Requirement**: `ASDLFile` class should provide debug/inspection capabilities
- **Use Case**: Development and debugging of ASDL processing pipeline
- **Implementation**: Add `to_json()` or `dump_json()` method to convert `ASDLFile` to JSON format
- **Purpose**: Human-readable representation of internal data structures for debugging

## Open Questions  
1. **Parameter Propagation**: How should `value` parameters for passive devices (R, L, C) be handled in the hierarchical subcircuit model?

2. **Net Naming**: What conventions should we use for internal net names and port connections?

3. **Error Handling**: How should we handle unconnected ports and missing model references in SPICE output?

4. **SPICE Comments**: How much metadata (doc, intent) should be included as comments in generated SPICE?

## Backlog Items
- **Parameter Order Consistency**: Make parameter ordering deterministic (use model-defined order) - **LOW PRIORITY**
- **Pattern Expansion**: Implement `<p,n>` and `[3:0]` pattern expansion
- **Parameter Resolution**: Implement `$param` variable substitution
- **Advanced Validation**: Enhance SPICE validation beyond syntax checking

## Completed Questions
- **Class Structure**: ✅ Implemented with comprehensive data structures
- **Parser Implementation**: ✅ Complete with future-proofing and TDD
- **Validation Level**: ✅ Implemented configurable strict/lenient validation
- **Port Ordering**: ✅ **CRITICAL**: Models define port order, instances use named mapping
- **PySpice Integration**: ✅ Complete validation layer for SPICE syntax and connectivity 
- **Hierarchical Design**: ✅ Complete subcircuit-based hierarchical methodology 