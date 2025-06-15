# Project Memory

## Project Overview
ASDL (Analog Structured Description Language) is a Python project to build classes that represent structured circuit topologies. The main goal is to parse ASDL YAML files (defined by ASDL_schema_v0p4) into proper data structures and convert them to SPICE netlists that are simulatable with ngspice.

Key components:
- YAML-based intermediate representation for analog circuits
- Python classes to represent circuit hierarchy and structure  
- YAML to SPICE netlist converter
- Support for pattern expansion (differential pairs, arrays)
- Parameter substitution system
- Design intent capture

Schema structure:
- `file_info`: File metadata (top_module, doc, revision, author, date)
- `models`: Device/component templates with PDK mappings
- `modules`: Circuit hierarchy with ports, instances, and connectivity

## Current State
- Project structure is established with virtual environment and basic dependencies
- ASDL schema v0.4 is defined in `doc/ASDL_schema_v0p4`
- README.md describes the project vision and basic usage
- Dependencies include PyYAML, Click, pytest, and development tools
- Context management system is being initialized
- Planning phase: architecture analysis needed before implementation

## Key Decisions
- Using YAML as the human-readable intermediate representation format
- Target output: SPICE netlists compatible with ngspice
- Python-based implementation for flexibility and ecosystem integration
- Modular design with separate parser, resolver, and generator components
- Test-driven development approach specified in development guidelines

### Architecture Decisions (Confirmed)
1. **Pattern Expansion**: Keep patterns (`<p,n>`, `[3:0]`) in data structures, expand only during SPICE generation as explicit step (similar to Verilog elaboration)
2. **Parameter Resolution**: Keep original expressions (`$param`), make parameter evaluation an explicit step
3. **Model Mapping**: Use `model` field value as-is for PDK model card names
4. **Port Constraints**: Placeholder implementation, defer until basics are working
5. **Instance Intent**: Save as free-form dictionary metadata for later use
6. **Module Hierarchy**: Each `module` translates to a `.subckt` definition
7. **Implementation Approach**: Minimum viable product to get ASDL->SPICE flow working ASAP

## Recent Changes
- **Schema Update**: Changed `design_info` to `file_info` in ASDL schema v0.4 for semantic consistency
- **Code Update**: Updated all Python classes and references to use `FileInfo` instead of `DesignInfo`
- **Interface Analysis**: Defined clear interfaces between Parser → Expander → Resolver → Generator pipeline
- **Future-Proofing Implementation**: Enhanced parser with comprehensive future-proofing capabilities including:
  - Unknown field detection and handling (strict/lenient modes)
  - Intent metadata preservation for extensible design annotations
  - Backward compatibility with legacy schema versions  
  - Flexible enum handling for future device types
  - Comprehensive validation and error reporting
- **Scope Refinement**: Simplified port constraints to placeholder implementation, moved advanced constraint features to backlog for later implementation
- **Parser Completion**: Successfully implemented complete ASDL parser with 44 passing tests using systematic TDD approach
- **Priority Adjustment**: Decided to skip pattern expansion and implement SPICE generator next to achieve end-to-end functionality faster

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

2. **Port Ordering**: How should we order ports in .subckt definitions? (alphabetical, declaration order, explicit ordering)

3. **Parameter Handling**: How should we handle unresolved parameter expressions during SPICE generation?

4. **Net Naming**: What conventions should we use for internal net names and port connections?

5. **Error Handling**: How should we handle unconnected ports and missing model references in SPICE output?

6. **SPICE Comments**: How much metadata (doc, intent) should be included as comments in generated SPICE?

## Completed Questions
- **Class Structure**: ✅ Implemented with comprehensive data structures
- **Parser Implementation**: ✅ Complete with future-proofing and TDD
- **Validation Level**: ✅ Implemented configurable strict/lenient validation 