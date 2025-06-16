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
**🎉 Phase 3 COMPLETE**: Parameter Handling Enhancement for Passive Devices
- ✅ **Phase 1**: ASDL Parser + SPICE Generator + PySpice Integration (44+7+6=57 tests)
- ✅ **Phase 2**: Hierarchical Subcircuit Implementation (15/21 functional tests passing)
- ✅ **Phase 3**: Parameter Handling Enhancement (NEW DEVICE_LINE APPROACH)
- 🔄 **Next Phase**: ngspice Simulation Testing

### Phase 3 Achievements
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

### ✅ Enhanced Parameter Handling (NEW - PHASE 3)
**COMPLETED**: Robust parameter handling system with automatic parameter generation

**Key Design Decisions**:
12. **Schema Enhancement**: Added `device_line` + `parameters` fields to DeviceModel
13. **Field Consistency**: Standardized on `doc` field for both models and modules (not `description`)
14. **Automatic Parameter Appending**: Parameters automatically added to device lines as `param={param}`
15. **Clean Device Lines**: Core device definition separate from parameter references
16. **Error-Resistant Design**: No manual parameter formatting required

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
1. **ngspice Simulation**: How well do our generated netlists simulate in ngspice? What simulation setup is needed?

2. **Net Naming**: What conventions should we use for internal net names and port connections?

3. **Error Handling**: How should we handle unconnected ports and missing model references in SPICE output?

4. **SPICE Comments**: How much metadata (doc, intent) should be included as comments in generated SPICE?

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