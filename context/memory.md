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

### 🚀 **Phase 1.2 Ready for Implementation** 
- **Import System as Elaborator Phase**: Architecture finalized with import resolution as Phase 1 of elaboration
- **Component Placement**: Parser extensions in `sections/`, elaborator extensions in `elaborator/import/`
- **Error Code Strategy**: P05xx for parser syntax validation, E044x for elaborator reference resolution
- **MVP Error Codes**: P0503, E0441-E0445 defined and documented
- **Modular Structure**: 6 focused components under `src/asdl/elaborator/import/`

### ✅ **Completed Systems**
- **Phase 1.1 Import Data Structures**: ASDLFile with model_alias field, simplified imports, ImportDeclaration removal (Commit: 9d3bc9e)
- **Schema Generation**: JSON/text schema from data structures, CLI integration
- **Visualizer**: Functional with jsPlumb, zoom/pan/drag, layout export
- **Testing**: Green with dependency guards for PySpice/devcontainer

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
- **Import System Phase 1.2**: Implement import resolution as elaborator phase with modular architecture
- **Parser Extensions**: Add model_alias syntax validation (P0503)
- **Elaborator Enhancement**: Multi-phase elaboration (Import → Pattern → Variable)
- **CLI**: Add search-path arguments support
- **Testing**: TDD approach for import components

## Recent Design Evolution (2025-08-23)

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
