# ASDL Import System Development Todos

## Phase 1: Core Import Infrastructure (MVP)

### Parser & Data Structure Extensions
- [ ] Add `imports` field to `ASDLFile` dataclass
- [ ] Create `ImportDeclaration` dataclass for `local_name: qualified.source.name` mappings  
- [ ] Extend YAML parser to recognize and validate `imports` section
- [ ] Support both `library.module` and `library.file.module` import formats
- [ ] Add import context tracking for resolution chains

### Library Registry System
- [ ] Create `LibraryRegistry` class for managing library discovery
- [ ] Support `asdl.lib.yaml` configuration files for library path mappings
- [ ] Implement path resolution algorithm for library locations
- [ ] Handle library search order and precedence rules

### Import Resolution Engine  
- [ ] Build `ImportResolver` to resolve qualified names to actual file paths
- [ ] Extract specific modules from multi-module ASDL files
- [ ] Implement dependency chain resolution with circular import detection
- [ ] Add proper error handling and diagnostics for import failures

## Phase 2: Unit Device Abstraction

### Enhanced Parameter System
- [ ] Upgrade parameter resolver to handle multiplier-only instances
- [ ] Support `m` parameter for device sizing in unit devices
- [ ] Validate unit device constraints (only multiplier parameter allowed)
- [ ] Enable parameter expression evaluation in import contexts

### PDK Integration Support
- [ ] Create analog standard cell library structure templates
- [ ] Implement three-layer architecture validation (PDK → Unit Devices → Design Logic)
- [ ] Support technology-independent design patterns
- [ ] Add device model abstraction for different PDKs

## Phase 3: Advanced Features

### Parameterized Imports
- [ ] Add parameter substitution in import paths using `${variable}` syntax
- [ ] Support design exploration through parameterized device variants
- [ ] Enable technology sweeps and cross-PDK validation
- [ ] Implement model fidelity progression (behavioral → schematic → extracted)

### Integration & Testing
- [ ] Integrate import resolution with existing SPICE generation pipeline
- [ ] Update generator to handle imported device models and modules
- [ ] Create comprehensive test suite covering all import scenarios
- [ ] Add validation for import dependency management and conflicts

## Implementation Notes

### Key Files to Modify
- `src/asdl/data_structures.py` - Add import data structures
- `src/asdl/parser.py` - Extend YAML parsing for imports
- `src/asdl/resolver.py` - Enhance parameter resolution for imports  
- `src/asdl/elaborator.py` - Integrate import resolution into elaboration
- `src/asdl/generator.py` - Handle imported components in SPICE generation

### Design Principles
- Maintain backward compatibility with existing ASDL files
- Build incrementally starting with simple library.module imports
- Defer complex workspace-level management to later phases
- Focus on three core dependency types: analog standard cells, design cells, external SPICE

### Test Strategy
- Unit tests for each import resolution component
- Integration tests with multi-file designs
- Cross-technology validation scenarios
- Error handling and diagnostic message quality

## Open Questions
1. **Corner Management**: How should testbench-level corner control integrate with import system?
2. **Namespace Resolution**: Specific rules for local vs qualified imports within libraries?
3. **SPICE Generation**: How do imports connect to PDK integration and corner-aware netlist generation?
4. **Library Versioning**: Should we support versioned imports for library management?

## Session Progress Tracking
- **Session 2025-08-18**: Analyzed codebase, reviewed import strategy document, created development plan