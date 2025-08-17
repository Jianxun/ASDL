# Product Requirements Document: ASDL Unified Import Strategy

## Executive Summary

This PRD defines the requirements for implementing a unified import mechanism in ASDL that enables complete separation of design logic from physical implementation. The system provides explicit import mapping, unit device abstraction, and parameterized imports to achieve technology independence and systematic design exploration.

**Product Vision**: Enable analog designs to be topology-focused like digital designs, with physical implementation details abstracted into reusable libraries. Support systematic design space exploration through parameterized imports.

**Target Users**: Analog circuit designers, IP library developers, and design automation engineers working with multiple PDKs and design variants.

## Product Objectives

### Primary Objectives
1. **Complete Abstraction**: Separate circuit topology from physical implementation details
2. **Technology Independence**: Enable same design to work across multiple PDKs with only import changes
3. **Design Exploration**: Support systematic exploration of device variants and implementations
4. **Dependency Clarity**: Make all design dependencies explicit and traceable

### Secondary Objectives
1. **Design Reuse**: Maximize IP portability across projects and technologies
2. **Automation Enablement**: Create foundation for LLM-driven design automation
3. **Maintainability**: Simplify design updates and variant management
4. **Tool Integration**: Support existing ASDL infrastructure and SPICE generation

## Core Architecture

### Three-Layer Import Architecture

**Layer 1: PDK Primitives** (Foundry devices - only in analog standard cell libraries)
```yaml
# gf180mcu_analog_std_lib.asdl
imports:
  nfet_03v3: gf180mcu.nfet_03v3
modules:
  nmos_unit_L0p28:
    mappings: {D: D, G: G, S: S, B: B}
    instances:
      M1: {model: nfet_03v3, params: {L: 0.28u, W: 3u, NF: 2, m: 1}}
```

**Layer 2: Analog Standard Cells** (Unit devices with fixed geometry)
```yaml
# Design files import unit devices, never PDK primitives directly
imports:
  nmos_unit: gf180mcu_analog_std_lib.nmos_unit_L0p28
  pmos_unit: gf180mcu_analog_std_lib.pmos_unit_L0p28
```

**Layer 3: Design Logic** (Geometry-free, multiplier-only)
```yaml
# Pure topology with relative sizing
instances:
  M_REF:  {model: nmos_unit, params: {m: 1}}    # Reference
  M_OUT1: {model: nmos_unit, params: {m: 2}}    # 2x current
  M_OUT2: {model: nmos_unit, params: {m: 4}}    # 4x current
```

## Functional Requirements

### FR-1: Unified Import Syntax
- **FR-1.1**: Single import syntax for all dependency types
- **FR-1.2**: Support analog standard cells, design cells, and external SPICE cells
- **FR-1.3**: Explicit local name to qualified source mapping
- **FR-1.4**: Clear import declarations show all dependencies
- **FR-1.5**: Validate import targets exist and are accessible

### FR-2: Unit Device Abstraction
- **FR-2.1**: Support geometry-free design using unit devices only
- **FR-2.2**: Allow multiplier-only sizing (no W/L/NF in design files)
- **FR-2.3**: Enable fixed-geometry unit devices in analog standard cell libraries
- **FR-2.4**: Support parameter inheritance with multiplier override
- **FR-2.5**: Maintain design intent through multiplier ratios

### FR-3: Technology Independence
- **FR-3.1**: Complete isolation of designs from PDK primitives
- **FR-3.2**: Enable PDK migration by changing only import statements
- **FR-3.3**: Support cross-technology design validation
- **FR-3.4**: Preserve circuit topology across technology nodes
- **FR-3.5**: Enable unit device characterization and optimization

### FR-4: Design Space Exploration
- **FR-4.1**: Support easy device variant swapping through imports
- **FR-4.2**: Enable A/B testing of different implementations
- **FR-4.3**: Allow behavioral to extracted netlist progression
- **FR-4.4**: Support implementation comparison workflows
- **FR-4.5**: Enable systematic performance optimization

### FR-5: Parameterized Imports (Advanced)
- **FR-5.1**: Support parameterized import statements with variables
- **FR-5.2**: Enable simulation sweeps across device variants
- **FR-5.3**: Allow implementation comparison through parameters
- **FR-5.4**: Support cross-PDK validation sweeps
- **FR-5.5**: Enable automated design space exploration

### FR-6: Namespace Management
- **FR-6.1**: Implement explicit local to qualified name mapping
- **FR-6.2**: Support same-library and cross-library imports
- **FR-6.3**: Provide clear namespace resolution rules
- **FR-6.4**: Prevent naming conflicts through explicit mapping
- **FR-6.5**: Enable library-scoped name resolution

### FR-7: Library Integration
- **FR-7.1**: Support analog standard cell library creation
- **FR-7.2**: Enable IP library organization and reuse
- **FR-7.3**: Support external SPICE netlist integration
- **FR-7.4**: Provide library versioning and compatibility
- **FR-7.5**: Enable library dependency tracking

## User Stories

### Epic 1: Basic Import Mechanism
**As an** analog circuit designer  
**I want to** import dependencies using explicit name mapping  
**So that** my design logic is separated from implementation details

**Acceptance Criteria:**
- Can import unit devices with `local_name: qualified.source.name` syntax
- Can import design cells from other libraries
- Can import external SPICE netlists
- All dependencies declared explicitly in imports section

### Epic 2: Unit Device Design
**As an** analog circuit designer  
**I want to** design using only unit devices and multipliers  
**So that** my designs are geometry-free and technology independent

**Acceptance Criteria:**
- Can instantiate devices using only multiplier parameters
- No geometry information (W/L/NF) in design files
- Multiplier ratios express design intent clearly
- Unit devices provide fixed, optimized geometry

### Epic 3: Technology Migration
**As an** analog circuit designer  
**I want to** migrate designs across PDKs by changing only imports  
**So that** I can reuse IP across technology nodes

**Acceptance Criteria:**
- Same design topology works across multiple PDKs
- Only import statements change for PDK migration
- Design logic remains completely unchanged
- Performance can be compared systematically

### Epic 4: Design Exploration
**As an** analog circuit designer  
**I want to** explore device variants and implementations easily  
**So that** I can optimize performance systematically

**Acceptance Criteria:**
- Can swap device variants by changing single import line
- Can compare different IP implementations
- Can progress from behavioral to extracted models
- Design body remains unchanged during exploration

## Technical Constraints

### System Constraints
- **TC-1**: Must integrate with existing ASDL parser and elaborator
- **TC-2**: Must generate valid SPICE netlists with proper subcircuit calls
- **TC-3**: Must support existing ASDL data structures and patterns
- **TC-4**: Must maintain backward compatibility during transition

### Performance Constraints
- **TC-5**: Import resolution time < 100ms for typical designs
- **TC-6**: Support designs with 1000+ imported dependencies
- **TC-7**: Memory usage < 200MB for large import hierarchies
- **TC-8**: Fast incremental re-elaboration when imports change

### Design Constraints
- **TC-9**: Use explicit import mapping syntax
- **TC-10**: Enforce unit device abstraction for technology independence
- **TC-11**: Support three-layer architecture strictly
- **TC-12**: Maintain clear separation between layers

## Implementation Strategy

### Phase 1: Core Import Mechanism (Weeks 1-3)
- Implement unified import syntax parser
- Basic local to qualified name mapping
- Support for analog standard cells and design cells
- Simple namespace resolution
- Integration with existing elaborator

### Phase 2: Unit Device Abstraction (Weeks 4-6)
- Enforce geometry-free design constraints
- Multiplier-only parameter handling
- Unit device library framework
- Standard cell library creation tools
- Technology independence validation

### Phase 3: Advanced Features (Weeks 7-9)
- External SPICE netlist integration
- Complex namespace resolution rules
- Library versioning and compatibility
- Performance optimization
- Comprehensive error handling

### Phase 4: Parameterized Imports (Weeks 10-12)
- Variable substitution in import statements
- Simulation sweep parameter support
- Design space exploration tools
- Cross-PDK validation workflows
- Advanced automation features

## Success Criteria

### Functional Success
- **SC-1**: Complete separation of design logic from physical implementation
- **SC-2**: Technology migration requires only import statement changes
- **SC-3**: Unit device abstraction enforced throughout design hierarchy
- **SC-4**: All dependency types supported through unified syntax
- **SC-5**: Design exploration workflows enabled and validated

### Quality Success
- **SC-6**: 95% code coverage for import mechanism
- **SC-7**: Zero breaking changes to existing ASDL designs
- **SC-8**: < 2% performance overhead for import resolution
- **SC-9**: 100% of integration tests passing
- **SC-10**: Comprehensive error messages for import failures

### User Experience Success
- **SC-11**: Intuitive import syntax familiar to engineers
- **SC-12**: Clear documentation with examples for each use case
- **SC-13**: IDE support for import completion and validation
- **SC-14**: Design exploration workflows are 5x faster than manual
- **SC-15**: Technology migration time reduced by 90%

## Risk Assessment

### High-Risk Items
- **R-1**: Import resolution complexity may affect performance
- **R-2**: Unit device abstraction may be too restrictive for some designs
- **R-3**: Three-layer architecture may complicate existing workflows
- **R-4**: Parameterized imports may introduce template complexity

### Mitigation Strategies
- **M-1**: Implement caching and lazy evaluation for import resolution
- **M-2**: Provide escape mechanisms for special cases while encouraging best practices
- **M-3**: Gradual migration path with compatibility layers
- **M-4**: Start with simple parameterization, add complexity incrementally

## Dependencies

### Internal Dependencies
- ASDL parser and elaborator modifications
- SPICE generation pipeline updates
- Error handling system extensions
- Testing framework enhancements

### External Dependencies
- Analog standard cell library creation for target PDKs
- IP library organization and migration
- External SPICE netlist format compatibility
- Tool integration for design exploration workflows

## Future Considerations

### Advanced Automation
- LLM integration for design generation
- Automated design space exploration
- Machine learning-guided optimization
- Continuous integration for analog designs

### Ecosystem Integration
- IDE plugins for import management
- Library marketplace and distribution
- Design pattern recognition and reuse
- Cross-EDA tool compatibility

This PRD establishes the foundation for a revolutionary approach to analog design that achieves the same level of abstraction and automation that digital design has enjoyed for decades.