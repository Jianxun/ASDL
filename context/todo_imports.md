# ASDL Import System Development Todos

## 🎯 Current Status: Phase 0 Data Structures ✅ COMPLETED

**Achieved:**
- ✅ **Unified Module Architecture**: Merged DeviceModel and Module into single class
- ✅ **ASDLFile Simplification**: Removed models field, added imports field
- ✅ **Import Foundation**: Added ImportDeclaration class for alias: library.filename[@version]
- ✅ **Comprehensive Tests**: 29 tests passing across T0.1, T0.2, T0.3, T0.4
- ✅ **Breaking Changes**: Clean elimination of DeviceModel/Module redundancy

**Next:** Generator unification (T0.5) - update generator for unified module handling (primitive vs hierarchical)

## Phase 0: Data Structure Unification (Breaking Refactor) ✅ COMPLETED
- [x] **Delete DeviceModel class entirely** - aggressive cleanup
- [x] **Remove `models` section completely** - no backward compatibility  
- [x] **Rewrite parser** - single unified module parsing path only ✅ COMPLETED
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

### Phase 0 Tasks ✅ COMPLETED (Data Structures)
- [x] Remove `DeviceModel` class from `src/asdl/data_structures.py`
- [x] Add `spice_template` field to unified `Module` class
- [x] Add `ImportDeclaration` class to data structures
- [x] Add `pdk` field to Module for .include generation
- [x] Update `Instance` class methods for unified architecture
- [x] Remove `models` field from `ASDLFile`, add `imports` field
- [x] Add mutual exclusion validation (`spice_template` XOR `instances`)
- [x] Remove `models` section parsing from `src/asdl/parser.py` ✅ COMPLETED
- [x] Implement unified module parsing (handle both primitive and hierarchical) ✅ COMPLETED
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

## Testing Tasks ✅ COMPLETED (Phase 0)
- [x] **T0.1**: Unit tests for unified Module class architecture (8 tests)
- [x] **T0.2**: Unit tests for unified ASDLFile structure (6 tests)  
- [x] **T0.3**: Unit tests for ImportDeclaration foundation (7 tests)
- [x] **T0.4**: Unit tests for parser simplification ✅ COMPLETED
- [ ] **T0.5**: Unit tests for SPICE generation unification
- [ ] **T0.6**: Unit tests for core validation logic
- [ ] **T0.7**: Integration tests for format migration validation
- [ ] **T0.8**: Integration tests for regression prevention

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
