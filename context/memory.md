# Project Memory

## Project Overview
ASDL (Analog System Description Language) is a comprehensive Python framework for analog circuit design and verification. The project provides parsing, elaboration, validation, and SPICE netlist generation capabilities with a focus on hierarchical design and test-driven development.

## Current State

### 🔍 **Architecture Status**
- **Unified Module System**: Single `Module` class handles both primitive and hierarchical modules
- **Parser**: Modular architecture complete (was 550-line monolith)
- **Elaborator**: Pattern expansion and parameter resolution implemented
- **Validator**: Full validation pipeline with location tracking
- **Generator**: LVS-compatible SPICE generation
- **Import System**: Architecture finalized, modular structure designed, MVP error codes defined

### ✅ **Phase 1.2: Complete - Import System MVP Implementation**
- **Import System as Elaborator Phase**: All 6 core components implemented, tested, and integrated
- **Component Placement**: Parser extensions in `sections/`, elaborator extensions in `elaborator/import_/`
- **Error Code Strategy**: P05xx for parser syntax validation, E044x for elaborator reference resolution
- **MVP Error Codes**: P0503, E0441-E0445 implemented with comprehensive diagnostics
- **Orchestrator Complete**: ImportResolver with circular import detection and workflow coordination

### ✅ **Completed Systems**
- **Phase 1.1 Import Data Structures**: ASDLFile with model_alias field, simplified imports (Commit: 9d3bc9e)
- **Phase 1.2.1 Parser Extensions**: model_alias_parser.py with P0503 validation (Commit: 15d8040)
- **Phase 1.2.2 Import Infrastructure**: path_resolver.py + file_loader.py with caching/circular detection (Commit: 15d8040)
- **Phase 1.2.3 Reference Resolution**: module_resolver.py + alias_resolver.py + diagnostics.py (Commit: 5fcb92a)
- **Phase 1.2.4 Orchestrator**: import_resolver.py main coordinator with circular import fix (Commit: 06cfbb1)
- **Schema Generation**: JSON/text schema from data structures, CLI integration
- **Visualizer**: Functional with jsPlumb, zoom/pan/drag, layout export
- **Testing**: 41 import system tests passing (100% success rate) including orchestrator and parser extensions

## Key Architectural Decisions
1. **Unified Module Architecture**: Single `Module` class for both primitive and hierarchical modules
2. **Import System Design**: File-based imports with ASDL_PATH resolution and `model_alias` section (see `doc/import_system/`)
3. **Unit Device Strategy**: Unit devices implemented as primitive modules (not hierarchical) for LVS compatibility
4. **Modular Parser**: 550-line monolith split into focused components (see `doc/parser/`)
5. **XCCSS Diagnostic System**: Structured error codes replacing PXXX (see `doc/diagnostic_system/`)
6. **Two-Stage Compilation**: Import Elaboration → SPICE Generation
7. **Tool Separation**: ASDL handles imports/resolution, external tools (ams-compose) handle versioning/reproducibility

## Known Limitations
- **YAML Pattern Parsing**: `ruamel.yaml` has issues with inline dictionary mappings containing `<p,n>` patterns. Use multi-line YAML format as workaround.

## Current Focus Areas
- **Import System Phase 1.2.5**: Enhanced elaborator integration (3-phase processing: Import → Pattern → Variable)
- **CLI Integration**: Add --search-path arguments and import resolution support
- **Integration Testing**: End-to-end pipeline validation with real circuit examples
- **Documentation**: Import system usage guide and best practices
  - See also: context/import_implementations.md for a distilled implementation snapshot

## Recent Design Evolution

### **Phase 1.2.4 Completed (2025-08-24)**

### **Import System MVP Complete - Production Ready**
- **All 6 Core Components**: Fully implemented with comprehensive test coverage
- **Import Orchestrator**: Main workflow coordinator with recursive loading and flattening
- **Circular Import Fix**: Critical cache bypass bug fixed - moved circular check before cache lookup
- **Test Coverage**: 41 tests passing including orchestrator scenarios and edge cases
- **Error Handling**: Complete E0442 diagnostic generation with proper cycle description
- **Examples**: Working test cases in `examples/imports/` for debugging and validation

### **Key Architectural Achievement**
- **Two-Layer Circular Detection**: FileLoader (individual files) + ImportResolver (workflow orchestration)
- **Robust Error Recovery**: Graceful failure with clear diagnostics, continues processing other imports
- **Module Flattening**: Single output ASDLFile with all dependencies resolved and modules combined
- **Search Path Resolution**: Full ASDL_PATH support with fallback to project-relative paths

### **Phase 1.2.5 (2025-08-24)**

### **Orchestration Phase 0 Skeleton Integrated + CLI Import Resolution**
- Added `Elaborator.elaborate_with_imports(main_file_path, search_paths=None, top=None)` to orchestrate: import resolution → pattern expansion → variable resolution
- Updated CLI commands:
  - `elaborate`: resolves imports first; supports `--search-path` for resolution
  - `netlist`: resolves imports first; supports `--search-path`; runs validate → generator as before
- Import flattening normalizes instance `model` references:
  - Strips qualified prefixes (`alias.module` → `module`)
  - Applies `model_alias` to bind to local module names before downstream phases
- Added toy example under `examples/imports/toy` and verified end-to-end netlisting to `examples/imports/toy/top.spice`

## Previous Evolution (2025-08-23)

### **Phase 1.1 Completed - Data Structure Simplification**
- **Breaking Changes Applied**: ImportDeclaration class removed, simplified imports to Dict[str, str]
- **model_alias Field Added**: Local module aliasing for technology portability
- **Comprehensive Testing**: 7 test cases passing for simplified structure
- **Schema Integration**: JSON schema generation working with new fields

### **Phase 1.2 Architecture Finalized - Import as Elaborator Phase**
- **Architectural Boundary**: Import resolution integrated as Phase 1 of elaboration
- **Component Placement**: Parser extensions in `sections/`, elaborator extensions in `elaborator/import/`
- **Error Code Strategy**: P05xx for syntax, E044x for reference resolution
- **Modular Structure**: 6 focused components under `src/asdl/elaborator/import/`
- **Enhanced Pipeline**: Import Resolution → Pattern Expansion → Variable Resolution

### **Key Simplifications**
- **Direct File Paths**: `alias: "library_dir/file_name.asdl"` syntax
- **ASDL_PATH Resolution**: Unix-like path-based file discovery
- **Tool Separation**: ASDL handles imports, ams-compose handles versioning
- **Unit Device Strategy**: Primitive modules for LVS compatibility
