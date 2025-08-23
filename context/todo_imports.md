# ASDL Import System Development Todos (MVP Implementation)

## 🎯 Current Status: Phase 1.1 Implementation → In Progress

**Architecture Complete (2025-08-23):**
- ✅ **Simplified Import Syntax**: Direct file paths `library_dir/file_name.asdl`
- ✅ **model_alias Section**: Local module aliasing for technology portability
- ✅ **ASDL_PATH Resolution**: Unix-like path-based file discovery
- ✅ **Tool Separation**: ASDL handles imports, ams-compose handles versioning
- ✅ **Unit Device Strategy**: Primitive modules for LVS compatibility
- ✅ **Modular Structure**: Import system under `src/asdl/import/` following parser pattern
- ✅ **MVP Error Codes**: 6 critical diagnostic codes defined (I0501, I0502, I0511, I0521, I0523, I0524)

**MVP Design Decisions (Breaking Changes Allowed):**
- **Removed**: Complex library registry with `asdl.lib.yaml`
- **Removed**: `qualified.source.name` import syntax
- **Removed**: ImportDeclaration class complexity
- **Added**: `model_alias` section for local module shorthand
- **Added**: ASDL_PATH environment variable resolution
- **Simplified**: Direct file path imports as simple strings
- **Scoped**: MVP-focused, no backward compatibility constraints

**Phase 1.1 Implementation Started**: Data structure simplification for MVP

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

### **Import Resolution Flow**
1. **File Discovery**: ASDL_PATH resolution (CLI → config → env → defaults)
2. **Import Loading**: Load .asdl files and extract modules
3. **Alias Resolution**: Map local aliases to qualified module names
4. **Module Resolution**: Three-step lookup (local → alias → imports)

### **Phase 1 MVP Scope**
- Direct file path imports (`alias: path/file.asdl`)
- `model_alias` section parsing and resolution
- ASDL_PATH-based file discovery
- MVP error codes: I0501, I0502, I0511, I0521, I0523, I0524
- Modular structure under `src/asdl/import/` following parser pattern
- Integration with existing elaboration pipeline

## Implementation Components

### **Phase 1: Core Import Infrastructure**

#### **1.1 Data Structure Updates (MVP - Breaking Changes OK)**
- [ ] Add `model_alias` field to `ASDLFile` dataclass
- [ ] Simplify `imports` field from ImportDeclaration to simple Dict[str, str]
- [ ] Remove ImportDeclaration class entirely (breaking change)
- [ ] Update import-related tests for new simplified structure
- [ ] Verify schema generation works with updated structure

#### **1.2 Modular Import System Structure**
- [ ] Create `src/asdl/import/` directory with modular structure:
  - [ ] `__init__.py` - Public API exports
  - [ ] `core/path_resolver.py` - ASDL_PATH resolution logic
  - [ ] `core/file_cache.py` - File caching and circular dependency detection
  - [ ] `resolvers/module_resolver.py` - Three-step module lookup
  - [ ] `resolvers/alias_resolver.py` - model_alias resolution
  - [ ] `import_loader.py` - Main orchestrator class
  - [ ] `model_alias_parser.py` - Parser for model_alias section
  - [ ] `diagnostics.py` - MVP error codes (I0501, I0502, I0511, I0521, I0523, I0524)

#### **1.3 Parser Integration**
- [ ] Update `src/asdl/parser/sections/import_parser.py` for simple file paths
- [ ] Add model_alias parser following existing section parser patterns
- [ ] Update main parser to use new import structure

#### **1.4 Data Structure & Elaborator Updates**
- [ ] Add `model_alias` field to `ASDLFile` dataclass
- [ ] Update `src/asdl/elaborator/elaborator.py` for two-stage processing
- [ ] Update schema generation to include model_alias field

#### **1.5 CLI & Testing**
- [ ] Update CLI to support `--search-path` arguments  
- [ ] Add unit tests for import system modules (TDD approach)
- [ ] Add integration tests for end-to-end import workflows
- [ ] Add configuration support for search paths in `asdl.config.yaml`

### **Backlog: Enhanced Features** 
- [ ] **Phase 2 - Hardening**: Enhanced error codes (I0503, I0504, I0512-I0514, I0522)
- [ ] **Phase 2 - Quality**: Warnings for unused imports, redundant aliases (I0601-I0604)  
- [ ] **Phase 2 - Features**: Transitive imports, enhanced diagnostics
- [ ] **Phase 3 - Advanced**: Import caching, dependency visualization, cross-technology validation

## Testing Strategy

### **MVP Testing (TDD Approach)**
- [ ] **T1.1**: File resolution with ASDL_PATH (4 tests)
- [ ] **T1.2**: model_alias parsing and validation (3 tests)  
- [ ] **T1.3**: Module resolution three-step lookup (6 tests)
- [ ] **T1.4**: MVP error handling (6 tests for I0501, I0502, I0511, I0521, I0523, I0524)
- [ ] **T1.5**: End-to-end import workflow (3 tests)
- [ ] **T1.6**: CLI integration with search paths (2 tests)

### **Backlog Testing**
- [ ] Import loading with caching and circular dependency detection  
- [ ] Enhanced error handling and diagnostics
- [ ] Performance testing for large import graphs

## Success Criteria

### **MVP Definition of Done**
1. **Direct File Imports**: `alias: path/file.asdl` syntax working
2. **model_alias Support**: Local module aliasing functional  
3. **ASDL_PATH Resolution**: File discovery through search paths
4. **Module Resolution**: Three-step lookup (local → alias → imports)
5. **MVP Error Handling**: 6 critical error codes implemented (I0501, I0502, I0511, I0521, I0523, I0524)
6. **Modular Structure**: Clean separation under `src/asdl/import/` following parser pattern
7. **Integration**: Works with existing elaboration pipeline
8. **Testing**: All MVP unit and integration tests passing (24 total tests)

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
- `context/memory.md` - Updated with new architectural decisions
- Previous Phase 0 data structure work already completed and compatible