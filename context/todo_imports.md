# ASDL Import System Development Todos (MVP Implementation)

## 🎯 Current Status: Phase 1.1 Complete → Phase 1.2 Ready

**✅ Phase 1.1 COMPLETED (2025-08-23):**
- ✅ **Data Structure Simplification**: ASDLFile with model_alias field and simplified imports
- ✅ **ImportDeclaration Removal**: Breaking change to eliminate complexity
- ✅ **Parser Updates**: Simplified import_parser.py with MVP error codes (P0501, P0502)
- ✅ **Comprehensive Testing**: 7 test cases passing for simplified import structure
- ✅ **Schema Integration**: JSON schema generation working with new structure

**✅ Architecture Finalized (2025-08-23):**
- ✅ **Import as Elaborator Phase**: Import resolution integrated into elaboration pipeline
- ✅ **Error Code Strategy**: P05xx for parser syntax, E044x for elaborator reference resolution
- ✅ **Component Placement**: Parser extensions in sections/, elaborator extensions in import/
- ✅ **Clean Boundaries**: Parser handles syntax, elaborator handles cross-file resolution

**MVP Design Decisions (Breaking Changes Allowed):**
- **Removed**: Complex library registry with `asdl.lib.yaml`
- **Removed**: `qualified.source.name` import syntax
- **Removed**: ImportDeclaration class complexity (COMPLETED)
- **Added**: `model_alias` section for local module shorthand (COMPLETED)
- **Added**: ASDL_PATH environment variable resolution
- **Simplified**: Direct file path imports as simple strings (COMPLETED)
- **Scoped**: MVP-focused, no backward compatibility constraints

**Phase 1.2 Ready**: Import system as elaborator phase with modular architecture

## New Architecture Summary

### **Data Structure Requirements**
```python
@dataclass  
class ASDLFile:
    file_info: FileInfo
    imports: Optional[Dict[str, str]] = None      # file_alias: path/to/file.asdl
    model_alias: Optional[Dict[str, str]] = None  # local_name: file_alias.module_name
    modules: Dict[str, Module]
```

### **Enhanced Elaborator Flow (New Architecture)**
```python
class Elaborator:
    def elaborate(self, main_file: ASDLFile, search_paths: List[str] = None) -> ASDLFile:
        # PHASE 1: Import Resolution (NEW)
        resolved_file = self.import_resolver.resolve_imports(main_file, search_paths)
        
        # PHASE 2: Pattern Expansion (EXISTING)
        expanded_file = self.pattern_expander.expand_patterns(resolved_file)
        
        # PHASE 3: Variable Resolution (EXISTING)
        return self.variable_resolver.resolve_variables(expanded_file)
```

### **Error Code Strategy (Updated)**
- **Parser (P05xx)**: Syntax validation only
  - P0501: Invalid Import Path Type (COMPLETED)
  - P0502: Invalid Import File Extension (COMPLETED)  
  - P0503: Invalid Model Alias Format (NEW)
- **Elaborator (E044x)**: Reference resolution
  - E0441: Import File Not Found
  - E0442: Circular Import Detected
  - E0443: Module Not Found in Import
  - E0444: Import Alias Not Found
  - E0445: Model Alias Collision

### **Phase 1.2 MVP Scope (Updated Architecture)**
- Import resolution as Phase 1 of elaboration
- Parser extensions for model_alias syntax validation
- Elaborator extensions for cross-file reference resolution
- ASDL_PATH-based file discovery
- MVP error codes: P0503, E0441-E0445
- Modular structure under `src/asdl/elaborator/import/`
- Clean integration with existing pipeline

## Implementation Components

### **Phase 1: Core Import Infrastructure**

#### **✅ 1.1 Data Structure Updates (COMPLETED)**
- [x] Add `model_alias` field to `ASDLFile` dataclass
- [x] Simplify `imports` field from ImportDeclaration to simple Dict[str, str]
- [x] Remove ImportDeclaration class entirely (breaking change)
- [x] Update import-related tests for new simplified structure
- [x] Verify schema generation works with updated structure

#### **1.2 Parser Extensions (Updated Architecture)**
- [ ] Add `src/asdl/parser/sections/model_alias_parser.py`:
  - [ ] Parse model_alias section syntax following existing patterns
  - [ ] Basic format validation (alias.module_name)
  - [ ] Integration with LocatableBuilder/FieldValidator
  - [ ] Error codes: P0503 (Invalid Model Alias Format)
- [ ] Update parser integration to handle model_alias section

#### **1.3 Elaborator Import Infrastructure (New Architecture)**
- [ ] Create `src/asdl/elaborator/import/` directory:
  - [ ] `__init__.py` - Internal API exports
  - [ ] `import_resolver.py` - Main orchestrator (~150 lines)
  - [ ] `path_resolver.py` - ASDL_PATH resolution (~120 lines)
  - [ ] `file_loader.py` - File caching + circular detection (~100 lines)
  - [ ] `module_resolver.py` - Cross-file module lookup (~130 lines)
  - [ ] `alias_resolver.py` - model_alias resolution (~90 lines)
  - [ ] `diagnostics.py` - E044x error codes (~80 lines)

#### **1.4 Elaborator Integration (Enhanced Pipeline)**
- [ ] Update `src/asdl/elaborator/elaborator.py`:
  - [ ] Add import resolution as Phase 1
  - [ ] Integrate import_resolver with existing architecture
  - [ ] Support search_paths parameter
  - [ ] Preserve existing pattern expansion and variable resolution

#### **1.5 CLI & Testing (Updated Scope)**
- [ ] Update CLI to support `--search-path` arguments
- [ ] Add unit tests for import components (TDD approach)
- [ ] Add integration tests for enhanced elaborator workflow
- [ ] Add configuration support for search paths in `asdl.config.yaml`

### **Backlog: Enhanced Features** 
- [ ] **Phase 2 - Hardening**: Enhanced error codes (I0503, I0504, I0512-I0514, I0522)
- [ ] **Phase 2 - Quality**: Warnings for unused imports, redundant aliases (I0601-I0604)  
- [ ] **Phase 2 - Features**: Transitive imports, enhanced diagnostics
- [ ] **Phase 3 - Advanced**: Import caching, dependency visualization, cross-technology validation

## Testing Strategy

### **MVP Testing (TDD Approach - Updated)**
- [x] **T1.0**: Simplified import data structures (7 tests - COMPLETED)
- [ ] **T1.1**: Parser model_alias syntax validation (3 tests for P0503)
- [ ] **T1.2**: ASDL_PATH file resolution (4 tests)  
- [ ] **T1.3**: Cross-file module resolution (6 tests)
- [ ] **T1.4**: MVP error handling (5 tests for E0441-E0445)
- [ ] **T1.5**: Enhanced elaborator integration (3 tests)
- [ ] **T1.6**: CLI integration with search paths (2 tests)

### **Backlog Testing**
- [ ] Import loading with caching and circular dependency detection  
- [ ] Enhanced error handling and diagnostics
- [ ] Performance testing for large import graphs

## Success Criteria

### **MVP Definition of Done (Updated Architecture)**
1. **✅ Direct File Imports**: `alias: path/file.asdl` syntax working (COMPLETED)
2. **✅ model_alias Support**: Local module aliasing data structure (COMPLETED)
3. **Parser Extensions**: model_alias syntax validation with P0503
4. **Import Resolution**: Cross-file reference resolution as elaborator phase
5. **ASDL_PATH Resolution**: File discovery through search paths
6. **Module Resolution**: Three-step lookup (local → alias → imports)
7. **MVP Error Handling**: Error codes implemented (P0503, E0441-E0445)
8. **Modular Structure**: Clean separation under `src/asdl/elaborator/import/`
9. **Integration**: Import resolution as Phase 1 of enhanced elaborator
10. **Testing**: All MVP unit and integration tests passing (~24 total tests)

### **MVP Constraints (No Backward Compatibility)**
- ✅ **Breaking changes allowed** for cleaner architecture
- ✅ **Focus on MVP functionality** over legacy support
- [ ] Existing module/instance syntax preserved (core functionality)

## Documentation Tasks
- [ ] Update user guide with import system usage
- [ ] Create import system tutorial with examples
- [ ] Document ASDL_PATH configuration and best practices
- [ ] Update API documentation for new classes

## Notes
- **No Library Registry**: Simplified to direct file paths
- **No Versioning**: Delegated to external tools (ams-compose)
- **LVS Focus**: Unit devices as primitives maintains compatibility
- **Path-Based**: Familiar Unix-like resolution for developers
- **MVP-Focused**: 6 critical error codes for core functionality, hardening moved to backlog
- **Modular Design**: Following established parser structure pattern

## Context References
- `doc/import_system/asdl_import_dependency_management.md` - Complete architecture specification
- `doc/import_system/asdl_import_implementation_plan.md` - Updated implementation decisions (NEW)
- `context/memory.md` - Updated with new architectural decisions
- Phase 1.1 data structure work completed and committed (9d3bc9e)