# ASDL Import System Development Todos

## Phase 0: Data Structure Unification (Breaking Refactor)
- [ ] **Delete DeviceModel class entirely** - aggressive cleanup
- [ ] **Remove `models` section completely** - no backward compatibility  
- [ ] **Rewrite parser** - single unified module parsing path only
- [ ] **Rewrite generator** - unified module handling (primitive vs hierarchical)
- [ ] **Update all existing ASDL files** - migrate `models` → `modules` with `spice_template`

## Phase 1: Core Import Infrastructure (MVP)
- [ ] Basic import syntax: `alias: library.filename`
- [ ] Library registry with `asdl.lib.yaml` support
- [ ] Single-level import resolution (no transitive imports)
- [ ] Qualified module references: `alias.module_name`
- [ ] Integration with existing elaboration pipeline

## Phase 2: Enhanced Import Features
- [ ] Transitive import resolution with circular detection
- [ ] Enhanced error diagnostics for import failures
- [ ] PDK integration with `.include` generation
- [ ] Core primitive vs hierarchical validation

## Phase 3: Advanced Features
- [ ] Parameterized imports with variable substitution
- [ ] Version constraint support
- [ ] Optional practice guideline linting (3-layer architecture suggestions)
- [ ] Cross-technology design validation

## Detailed Task Breakdown

### Phase 0 Tasks
- [ ] Remove `DeviceModel` class from `src/asdl/data_structures.py`
- [ ] Add `spice_template` field to unified `Module` class
- [ ] Add `ImportDeclaration` class to data structures
- [ ] Remove `models` section parsing from `src/asdl/parser.py`
- [ ] Implement unified module parsing (handle both primitive and hierarchical)
- [ ] Add mutual exclusion validation (`spice_template` XOR `instances`)
- [ ] Update `src/asdl/generator.py` for unified module handling:
  - [ ] Primitive modules → inline SPICE generation
  - [ ] Hierarchical modules → `.subckt` definition generation
- [ ] Migrate existing ASDL files to new format

### Phase 1 Tasks
- [ ] Create `src/asdl/library_registry.py`:
  - [ ] `LibraryRegistry` class
  - [ ] `asdl.lib.yaml` configuration support
  - [ ] `library.filename` → file path resolution
- [ ] Create `src/asdl/import_resolver.py`:
  - [ ] `ImportResolver` class
  - [ ] Basic import resolution and merging
  - [ ] Namespace management for imported modules
- [ ] Add `imports` section parsing to parser
- [ ] Validate `alias: library.filename[@version]` format
- [ ] Update `src/asdl/elaborator.py`:
  - [ ] Two-stage elaboration (imports first, then patterns)
  - [ ] Qualified name resolution (`alias.module_name`)

### Phase 2 Tasks
- [ ] Add circular dependency detection to import resolver
- [ ] Implement transitive import resolution
- [ ] Add PDK `.include` statement generation
- [ ] Enhanced diagnostic messages for import failures
- [ ] Core validation for primitive vs hierarchical modules

### Phase 3 Tasks
- [ ] Create `src/asdl/linting.py` for optional practice guidelines
- [ ] Implement parameterized import syntax (`${variable}` substitution)
- [ ] Add version constraint parsing and validation
- [ ] Cross-technology design validation tools

## Testing Tasks
- [ ] Unit tests for unified module parsing
- [ ] Unit tests for import syntax validation
- [ ] Unit tests for library registry path resolution
- [ ] Unit tests for import resolution algorithm
- [ ] Integration tests for primitive vs hierarchical SPICE generation
- [ ] Integration tests for multi-file designs with imports
- [ ] Integration tests for qualified module name resolution

## Documentation Tasks
- [ ] Update user documentation for new unified module syntax
- [ ] Create migration guide from old `models` to new `modules` format
- [ ] Document import system usage and best practices
- [ ] Document 3-layer architecture practice guidelines

## Breaking Changes Migration
- [ ] Identify all existing ASDL files using `models` section
- [ ] Create automated migration scripts for format conversion
- [ ] Update example files and tutorials
- [ ] Update test fixtures to new format
