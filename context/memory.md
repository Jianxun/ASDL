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

## Open Questions
1. **Class Structure Details**: Finalize the exact Python class definitions and their relationships

2. **Pattern Syntax**: Confirm the exact syntax for pattern expansion (`<p,n>` vs `<P,N>`, `[3:0]` indexing)

3. **Parameter Expression**: What parameter expressions should we support (`$M`, `$M*4`, `$M+1`, etc.)?

4. **Net Declaration**: How should we handle the `nets.internal` list and port-to-net relationships?

5. **Error Handling**: What level of validation should we perform on the ASDL input?

6. **SPICE Format**: Any specific SPICE formatting preferences or compatibility requirements? 