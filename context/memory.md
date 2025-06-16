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
**Phase 1 Complete**: ASDL Parser + SPICE Generator + PySpice Integration
- ✅ **Parser**: 44 passing tests, complete ASDL YAML parsing
- ✅ **Generator**: 7 passing device generation tests, template-based SPICE output
- ✅ **PySpice Integration**: 6 passing tests, validation of generated SPICE netlists
- ✅ **Test Infrastructure**: 57 total passing tests across all components
- ✅ **Manual Inspection**: Generated JSON and SPICE files for debugging
- 🔄 **Next Phase**: Hierarchical subcircuit refactor (models as subcircuits)

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

### Critical Architectural Insight: Hierarchical Subcircuit Design
**Current Issue**: Models generate as primitive devices, limiting extensibility
**New Direction**: Models should become subcircuit definitions for modularity

**Rationale**:
- `nmos_unit` could be complex (cascode, parasitics, composite devices)
- Industry standard approach matches foundry PDK structure
- Enables reusable, hierarchical design methodology
- Clear separation between model interface and implementation

## Recent Changes

### PySpice Integration Implementation
- **PySpice Dependency**: Added PySpice>=1.5.0 for SPICE validation
- **Validation Layer**: `spice_validator.py` with `parse_spice_netlist()` function
- **Real ASDL Testing**: Used `tests/fixtures/inverter.yml` with proper ports and parameters  
- **Case Sensitivity Fix**: Resolved port name mismatch (lowercase → uppercase)
- **Parameter Fix**: Changed from variable `$M` to literal `M: 2` for cleaner SPICE
- **Test Coverage**: 6 comprehensive PySpice integration tests
- **Debug Output**: Manual inspection files saved to `/tests/unit_tests/generator/results/`

### Port Mapping Analysis
**Critical Discovery**: Current implementation has port mapping order dependency
- **Problem**: Changing instance mapping order affects SPICE output
- **Root Cause**: Dictionary iteration order affects parameter sequence
- **Priority**: Port order is STRICT requirement, parameter order is backlog item
- **Solution**: Requires hierarchical refactor with named port resolution

## Port Mapping Requirements (CRITICAL)
### Two-Level Port Mapping Strategy
1. **ASDL → SPICE Primitives**: Strict positional order (SPICE device requirements)
2. **ASDL Subcircuits**: Named port mapping (designer freedom)

### Implementation Rules
- **Model Definition**: Controls port order and parameter order (interface contract)
- **Instance Mappings**: Order-independent, resolved by name
- **SPICE Output**: Always uses model-defined order for consistency

### Example
```yaml
models:
  nmos_unit:
    ports: [G, D, S, B]    # Model defines interface order
instances:
  MP:
    mappings: {D: out, G: in, S: vdd, B: vdd}  # Any order → resolved by name
```

## New Requirements
### ASDLFile Round-trip Capability
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
1. **SPICE Format**: What specific SPICE formatting preferences or compatibility requirements for ngspice?

2. **Net Naming**: What conventions should we use for internal net names and port connections?

3. **Error Handling**: How should we handle unconnected ports and missing model references in SPICE output?

4. **SPICE Comments**: How much metadata (doc, intent) should be included as comments in generated SPICE?

## Backlog Items
- **Parameter Order Consistency**: Make parameter ordering deterministic (use model-defined order)
- **Pattern Expansion**: Implement `<p,n>` and `[3:0]` pattern expansion
- **Parameter Resolution**: Implement `$param` variable substitution
- **Advanced Validation**: Enhance SPICE validation beyond syntax checking

## Completed Questions
- **Class Structure**: ✅ Implemented with comprehensive data structures
- **Parser Implementation**: ✅ Complete with future-proofing and TDD
- **Validation Level**: ✅ Implemented configurable strict/lenient validation
- **Port Ordering**: ✅ **CRITICAL**: Models define port order, instances use named mapping
- **PySpice Integration**: ✅ Complete validation layer for SPICE syntax and connectivity 