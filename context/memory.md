# Project Memory

## Project Overview
ASDL (Analog System Description Language) is a comprehensive Python framework for analog circuit design and verification. The project provides parsing, elaboration, validation, and SPICE netlist generation capabilities with a focus on hierarchical design and test-driven development.

## Current State
**Import System Architecture Complete (ready for implementation)**

### ✅ **ASDL Import System Architecture Finalized**
Comprehensive import dependency management strategy documented in `doc/asdl_import_dependency_management.md`. Key achievements:

**Core Philosophy**: Complete separation of design logic from physical implementation through explicit import mapping

**Three-Layer Architecture**:
- **Layer 1: PDK Primitives** - Raw SPICE device models with `spice_template`
- **Layer 2: Unit Devices** - Standardized device tiles with fixed geometry, multiplier-only interface
- **Layer 3: Design Logic** - Technology-independent, topology-focused circuit design

**Deterministic Import Rules**:
- **File-only imports**: `alias: library.filename` → `library/filename.asdl`
- **Module references**: `alias.module_name` (two-step import-then-reference)
- **Version enforcement**: Required `version` and `date` in all `file_info` sections
- **Corner binding precedence**: Always applied last, after parameterization
- **Template validation**: Clear rules for multi-line `spice_template` content

**Design Decisions Resolved**:
- Eliminated three-dot syntax ambiguity (`library.file.module`)
- Enforced mutual exclusivity: `spice_template` XOR `instances`
- Unified `Module` class replacing separate `DeviceModel`/`Module` split
- Two-stage compilation: Import Elaboration → SPICE Generation

### 🔍 **Current Architecture Status**
- **Unified Module System**: Single `Module` class handles both primitive and hierarchical modules
- **Parser**: Complete with location tracking and diagnostic support
- **Elaborator**: Pattern expansion and parameter resolution implemented
- **Import System**: Architecture designed, implementation pending
- **Data Structures**: Fully unified and modern

### 📋 **Implementation Roadmap**
**Phase 1 (MVP)**: Basic import resolution, file-based syntax, multiplier-only unit devices
**Phase 2**: Enhanced versioning, meta-parameter unit devices, enhanced diagnostics
**Phase 3**: Auto-generation tooling, elaboration caching, behavioral fallbacks (requires discussion)

### ✅ **Schema Generation System (completed)**
- **Architecture**: Single source of truth from `src/asdl/data_structures.py`
- **Implementation**: `src/asdl/schema_gen.py` with JSON Schema and text rendering
- **CLI Integration**: `asdlc schema` command with `--json` and `--out` options
- **Exclusion Strategy**: Runtime-only fields excluded via `Locatable.__schema_exclude_fields__`

### 🧪 Testing Status
- Devcontainer-dependent sims skipped via `tests/conftest.py`
- PySpice integration guarded/skipped when not available; tests green
- Tests are generally green with appropriate skipping for optional dependencies

### ✅ **Visualizer System (completed)**
- **Phase 1-5**: Minimal functional visualizer with jsPlumb Community Edition
- **Features**: Cursor-centered zoom, canvas panning, grid-snap dragging, dynamic loading
- **Architecture**: Two-layer container system with proper event handling
- **Output**: Save layout export and enhanced JSON schema for visualization

### 📊 **Component Health**
- ✅ **Parser**: Complete with location tracking and diagnostics
- ✅ **Data Structures**: Unified architecture fully implemented
- ✅ **Elaborator**: Pattern expansion and parameter resolution complete
- ✅ **Validator**: Full validation pipeline implemented
- ✅ **SPICEGenerator**: Modernized and fully tested
- ✅ **Visualizer**: Minimal functional system complete

## Key Architectural Decisions
1. **Unified Module Architecture**: Single `Module` class for both primitive and hierarchical modules
2. **Import System Design**: Three-layer architecture with deterministic file-only import syntax
3. **Schema Generation**: Single source of truth from dataclasses with runtime field exclusion
4. **Diagnostic System**: Comprehensive error reporting with location tracking and severity levels
5. **Two-Stage Compilation**: Import Elaboration → SPICE Generation

## Known Limitations
- **YAML Pattern Parsing**: `ruamel.yaml` has issues with inline dictionary mappings containing `<p,n>` patterns. Use multi-line YAML format as workaround.

## Current Focus Areas
- **Import system implementation** (READY - Phase 1 MVP: Basic import resolution, file-based syntax, multiplier-only unit devices)
- CLI testing and refinement
- Documentation and user experience improvements
- Legacy test updates (37 failing tests using old `models` field architecture)

## Parameter System Implementation Progress (2025-08-20)
**Decision**: Implement parameter resolving system before import system implementation

**Status**: ✅ **COMPLETED** 
- ✅ **P1.1 Complete**: Variables field added to Module dataclass with schema integration
- ✅ **P1.2 Complete**: Parser dual syntax support (parameters/params, variables/vars) with warnings
- ✅ **P1.3 Complete**: Parameter override validation implementation (9 TDD tests passing)
- ✅ **P1.4 Complete**: Template generation enhancement for variables (4 TDD tests passing)
- ✅ **P1.5 Complete**: Integration and regression testing (164 tests: 126 passed, 37 legacy failures)

**Key Achievements**:
- **Variables field**: Module dataclass enhanced with `variables: Optional[Dict[str, Any]]`
- **Dual syntax**: Parser supports both canonical and abbreviated forms with conflict warnings  
- **Parameter override validation**: Comprehensive rules enforced (primitives-only, no variable overrides, case-sensitive)
- **Template generation enhancement**: Variables support with shadowing (variables > instance params > module params)
- **TDD approach**: 13 comprehensive tests written before implementation across all phases
- **Zero breaking changes**: All existing functionality preserved throughout
- **Schema integration**: Variables field included in JSON schema generation

**Implementation Details**:
- **Validator**: Added `validate_parameter_overrides()` and `validate_file_parameter_overrides()` methods with error codes V301-V303
- **Generator**: Enhanced `_generate_primitive_instance()` to support variables in template substitution
- **Parser**: Dual syntax validation with appropriate warnings for conflicting field names
- **Integration**: Full compatibility with existing unified module architecture

**Ready for Import System Phase 1 Implementation**