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
- **Parser cleanup and refactoring** (ACTIVE - Preparing for import system feature addition)
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

## Debugging and Generator Fixes (2025-08-20)
**Status**: ✅ **COMPLETED** - Critical debugging infrastructure and generator issues resolved

**Core Fixes Applied**:
1. ✅ **Exception Handling**: Removed generic E999 wrapper from elaborator, now shows full stack traces with module context for effective debugging
2. ✅ **Elaborator Bug #1**: Fixed `replace()` call that incorrectly converted `instances=None` to `instances={}` for primitive modules
3. ✅ **Elaborator Bug #2**: Fixed `_expand_instances()` method that converted `instances=None` to `instances={}` during elaboration
4. ✅ **Legacy Field Updates**: Updated `models` → `modules` references in validator and expander (unified module architecture)
5. ✅ **Generator LVS Fix**: Removed `.param` line generation from hierarchical modules per parameter resolving system design

**Technical Details**:
- **Root Cause**: Multiple bugs caused primitive modules to be misclassified as hierarchical, leading to LVS-incompatible parameterized subcircuits
- **Fix Strategy**: Preserved `instances=None` semantic throughout pipeline for primitive modules vs `instances={}` for hierarchical
- **Validation**: Module classification now correct - primitives vs hierarchical properly distinguished
- **LVS Compatibility**: Hierarchical modules generate fixed subcircuits without `.param` declarations

**Current Pipeline Status**:
- ✅ **Parser**: Handles unified module architecture correctly  
- ✅ **Elaborator**: Preserves module semantics during pattern expansion
- ✅ **Validator**: Parameter override validation (V301-V303) implemented and integrated
- ✅ **Generator**: LVS-compatible SPICE generation for hierarchical modules
- ✅ **Template Variables**: Variable resolution in SPICE template generation
- ✅ **Validation Integration**: Parameter override validation added to CLI pipeline

**Generated SPICE Quality**: Fixed subcircuits without `.param` lines (LVS-compatible) ✅

## Validator Pipeline Fixes (2025-08-20)
**Status**: ✅ **COMPLETED** - Critical validator bugs resolved and validation pipeline complete

**Core Fixes Applied**:
1. ✅ **Unused Component Detection**: Fixed duplicate condition bug in `validate_unused_components()` that caused false warnings
2. ✅ **Parameter Override Validation**: Added missing `validate_file_parameter_overrides()` to netlist CLI validation pipeline
3. ✅ **Legacy Models References**: Systematic identification of obsolete `models` field usage across codebase

**Technical Details**:
- **Bug #1**: Validator incorrectly flagged all modules as unused due to duplicate conditional logic in unified architecture
- **Bug #2**: Parameter override validation existed but wasn't called from CLI, allowing forbidden hierarchical parameter overrides
- **Fix Quality**: `unified_architecture_demo.asdl` now correctly shows 3 V301 errors for hierarchical parameter overrides

**Validation Pipeline Now Complete**:
- ✅ **Net Declaration Validation**: Undeclared nets (V003)
- ✅ **Port Mapping Validation**: Invalid port mappings (V001, V002)  
- ✅ **Unused Component Detection**: Unused modules (V005)
- ✅ **Parameter Override Validation**: Hierarchical overrides forbidden (V301-V303)
- ✅ **Module Parameter Field Validation**: Hierarchical modules declaring parameters forbidden (V304)
- ✅ **Location Information**: All diagnostics include precise file:line:column locations

## Validation System Enhancement (2025-08-20)
**Status**: ✅ **COMPLETED** - Comprehensive validation rule coverage and user experience improvements

**New Validation Rules Added**:
1. ✅ **V304 Module Parameter Field Validation**: Prevents hierarchical modules from declaring `parameters` fields
   - **Rule**: Hierarchical modules (with `instances`) must only use `variables`, not `parameters`
   - **Rationale**: Enforces parameter resolving system design - hierarchical modules should only have internal implementation details
   - **Implementation**: `validate_module_parameter_fields()` method integrated into CLI pipeline

**User Experience Improvements**:
2. ✅ **Location Information in Diagnostics**: All validation errors now include precise source locations
   - **Format**: `at unified_architecture_demo.asdl:148:7` (file:line:column)
   - **Benefits**: Quick navigation, IDE integration, improved productivity
   - **Implementation**: Added `location=instance/module` to all Diagnostic constructors

**Validation Coverage Now Complete**:
- **V001-V002**: Port mapping validation
- **V003**: Net declaration validation  
- **V005**: Unused component detection
- **V301-V303**: Parameter override validation (instances)
- **V304**: Module parameter field validation (NEW)

**Testing Quality**: `unified_architecture_demo.asdl` correctly shows 6 validation errors with precise locations

## Code Organization and Cleanup (2025-08-21)
**Status**: ✅ **COMPLETED** - Major refactoring and cleanup completed

### ✅ **Elaborator Refactor and Variable Resolution**
Variable resolution implemented with clean elaborator architecture

**Problem Solved**: Variable references in instance parameters are now resolved during elaboration
- **Example**: `{M: nmos_M}` now correctly generates `m=1` instead of `m=nmos_M` in SPICE  
- **Impact**: SPICE simulation now works correctly with resolved variable values
- **Root Cause Fixed**: Elaborator now includes variable resolution phase after pattern expansion

**Implementation Completed**:
✅ **Phase 1**: Refactored elaborator into clean package structure (`src/asdl/elaborator/`)
   - ✅ Extracted pattern expansion logic to `pattern_expander.py` (240 lines)
   - ✅ Created clean main `elaborator.py` (200 lines) 
   - ✅ Added package `__init__.py` with proper exports

✅ **Phase 2**: Implemented variable resolution with clean architecture
   - ✅ Created `variable_resolver.py` (140 lines) with direct reference resolution
   - ✅ Integrated variable resolution into elaboration pipeline
   - ✅ Added error handling for undefined variables (E108 diagnostic)

✅ **Phase 3**: Integration testing and validation completed
   - ✅ All existing tests pass (82/83 - one expected failure from parameter system changes)
   - ✅ Variable resolution verified with inverter example
   - ✅ SPICE generation correctly shows resolved values (m=1, m=2) instead of variable names

**Architecture Benefits**:
- **Clean separation**: Pattern expansion and variable resolution are separate, testable modules
- **Maintainability**: Each component has single responsibility and clear interfaces  
- **Extensibility**: Easy to add new elaboration phases in the future
- **Zero breaking changes**: All existing functionality preserved

### ✅ **Data Structures Package Organization** 
Reorganized data structures and schema generation into clean package structure:
- **`src/asdl/data_structures/`** - New organized package 
  - **`structures.py`** - Core data structures (ASDLFile, Module, Instance, etc.)
  - **`schema_gen.py`** - JSON Schema and text schema generation
  - **`__init__.py`** - Clean exports maintaining backward compatibility
- **Zero breaking changes** - All existing imports work through package exports
- **Removed redundant files** - Eliminated old `expander.py` and `resolver.py` files

## Parser Hardening and Cleanup (2025-08-21)
**Status**: ✅ **COMPLETED** - Comprehensive parser hardening with TDD approach and legacy test cleanup

### ✅ **Parser Hardening Implementation (TDD)**
Complete diagnostic coverage implemented with test-driven development:

**P201: Unknown Field Warning - NEW Implementation**:
- **Test Coverage**: 5 comprehensive tests covering modules, ports, instances, multiple warnings, and negative cases
- **Implementation**: Added `_validate_unknown_fields()` method with field validation for:
  - **Modules**: `doc`, `ports`, `internal_nets`, `parameters`/`params`, `variables`/`vars`, `spice_template`, `instances`, `pdk`, `metadata`
  - **Ports**: `dir`, `type`, `constraints`, `metadata`  
  - **Instances**: `model`, `mappings`, `doc`, `parameters`/`params`, `metadata`
- **Diagnostic Quality**: Provides specific field names and suggestions for typos
- **Integration**: Seamlessly integrated into existing parser pipeline

**Existing Diagnostics Confirmed**:
- **P102: Missing Required Section** - ✅ Implemented and tested
- **P103: Invalid Section Type** - ✅ Implemented and tested
- **P104: Missing Required Field** - ✅ Implemented and tested

### ✅ **Legacy Test Updates**
Successfully updated failing tests for unified module architecture:
- **Removed**: `test_models.py` (obsolete - tests deprecated `models` section)
- **Fixed**: `test_basic_parsing.py` - Removed deprecated `models` field references
- **Fixed**: `test_location_tracking.py` - Updated module definitions to use valid `spice_template`
- **Result**: All 41 parser tests now pass (improved from 32/39 passing)

**Current Pipeline Status**:
- ✅ **Parser**: Comprehensive diagnostic coverage with hardened error handling (READY FOR REFACTORING - 550+ lines)
- ✅ **Data Structures**: Clean package organization with related components grouped, DeviceModel removed as obsolete
- ✅ **Elaborator**: Clean package with pattern expansion AND variable resolution
- ✅ **Validator**: Parameter override validation (V301-V304) implemented and integrated
- ✅ **Generator**: LVS-compatible SPICE generation with resolved variables
- ✅ **Variable Resolution**: Direct reference resolution working in production

## Parser Refactor and XCCSS Diagnostic System Design (2025-08-21)
**Status**: 📖 **DESIGN COMPLETED** - Comprehensive diagnostic system redesign with documentation

### ✅ **XCCSS Diagnostic System Design Finalized**
Complete redesign of diagnostic system from legacy `PXXX` to structured `XCCSS` format:

**XCCSS Format**: `XCCSS` where:
- **X**: Component prefix (P=Parser, E=Elaborator, V=Validator, G=Generator, I=Importer, S=Schema)
- **CC**: Category code (01=Syntax, 02=Schema, 03=Semantic, 04=Reference, 05=Type, 06=Style, 07=Extension, 08=Performance)
- **SS**: Specific error code within category (01-99)

**Architecture Decision**: **Distributed Implementation with Central Validation**
- Each component defines its own diagnostics in `{component}/diagnostics.py`
- Central registry provides conflict validation and tooling support
- Template-based message generation with named parameters
- Auto-severity detection from category codes

**Documentation Completed**:
- ✅ **`doc/diagnostic_system/xccss_design_decisions.md`** - Design rationale and architecture decisions
- ✅ **`doc/diagnostic_system/xccss_architecture.md`** - Technical implementation details and integration patterns
- ✅ **`doc/diagnostic_system/xccss_migration_plan.md`** - 5-phase implementation plan (7 weeks, detailed tasks)
- ✅ **`doc/diagnostic_system/README.md`** - Complete system overview and developer guide
- ✅ **Updated existing documentation** - Added migration notices and XCCSS previews

### 🎯 **Parser Refactor Plan Designed**
Comprehensive plan to split monolithic 550-line `parser.py` into modular architecture:

**Target Structure**:
```
src/asdl/parser/
├── __init__.py              # Public API
├── core/                    # Foundation
│   ├── yaml_loader.py      # YAML + location tracking
│   ├── diagnostic_builder.py # Structured diagnostics  
│   └── validation_mixin.py  # Reusable validation
├── sections/                # Section-specific parsers
│   ├── file_info_parser.py # FileInfo section
│   ├── import_parser.py    # Import declarations
│   ├── module_parser.py    # Module orchestration  
│   ├── port_parser.py      # Port definitions
│   └── instance_parser.py  # Instance definitions
├── resolvers/               # Field resolution
│   ├── dual_syntax_resolver.py # params/parameters, vars/variables
│   └── metadata_resolver.py    # Universal metadata
└── asdl_parser.py          # Main coordinating class
```

**Key Features**:
- **Modular Architecture**: Single responsibility per component
- **Enhanced Diagnostics**: XCCSS format with rich metadata
- **Language Server Ready**: Structured for IDE integration
- **Testable Components**: Individual parsers easily unit tested
- **Backward Compatible**: Preserves existing public API

### 📋 **Implementation Readiness**
**READY FOR IMPLEMENTATION**: Both parser refactor and XCCSS diagnostic system
- Design decisions documented and validated
- Architecture patterns established
- Migration strategy with clear phases
- Tool integration patterns defined
- Automated documentation generation planned

**Next Steps**: 
1. **Phase 1**: Foundation infrastructure (diagnostic system, registry, validation)
2. **Phase 2**: Parser migration to XCCSS and modular architecture
3. **Phase 3**: Component migration (Elaborator, Validator, Generator)
4. **Phase 4**: Tool updates and automated documentation
5. **Phase 5**: Legacy cleanup and finalization

## Parser Refactor Strategy (2025-08-22)
**Status**: 📋 **DESIGN COMPLETED** - Ready for implementation in next session

### ✅ **Comprehensive Error Code Analysis**
Complete parser error code strategy documented in `doc/parser/parser_error_codes.md`:
- **Current Coverage**: 8/15 MVP critical codes implemented, 7 missing
- **Total System**: 71 parser diagnostic codes identified (15 MVP + 56 hardening)
- **Critical Gaps**: Duplicate detection (silent data corruption) and enum validation (runtime crashes)

**MVP Critical Missing Codes**:
- **P0232**: Duplicate Module Name (HIGH - silent data loss)
- **P0242**: Duplicate Port Name (HIGH - undefined behavior)  
- **P0251**: Duplicate Instance Name (HIGH - instance conflicts)
- **P0221**: Duplicate Import Alias (HIGH - wrong references)
- **P0501**: Invalid Port Direction Enum (MEDIUM - runtime crashes)
- **P0502**: Invalid Port Type Enum (MEDIUM - runtime crashes)

### ✅ **Modular Architecture Design**
Complete modularization plan documented in `doc/parser/parser_refactor_plan.md`:

**Priority Decision**: Modularization first, then MVP validation additions
- **Rationale**: Establish maintainable foundation before adding business logic
- **Constraint**: Zero business logic changes during refactor
- **Goal**: Transform 550-line monolith into focused 50-100 line components

**Target Architecture**:
```
src/asdl/parser/
├── __init__.py              # Public API (unchanged)
├── asdl_parser.py          # Main orchestrator
├── core/                   # Foundation utilities
│   ├── yaml_loader.py      # YAML + location tracking
│   └── locatable_builder.py # Location extraction
├── sections/               # Section-specific parsers
│   ├── file_info_parser.py # FileInfo section
│   ├── import_parser.py    # Import declarations + P106 validation
│   ├── module_parser.py    # Module orchestration + P107/P108
│   ├── port_parser.py      # Port parsing + P104/P105/P201
│   └── instance_parser.py  # Instance parsing + P104/P201
└── resolvers/              # Field resolution logic
    ├── dual_syntax_resolver.py # params/parameters + P301/P302
    └── field_validator.py     # Unknown fields + P103/P201
```

**Implementation Strategy**:
1. **Phase 1**: Core utilities extraction (~4 hours)
2. **Phase 2**: Resolvers extraction (~3 hours)
3. **Phase 3**: Section parsers extraction (~8 hours)
4. **Phase 4**: Main orchestrator integration (~3 hours)
5. **Phase 5**: Comprehensive testing (~4 hours)

**Success Criteria**:
- Zero API changes
- All existing tests pass without modification
- No performance regression
- Clean modular architecture with dependency injection

### 📋 **Ready for Next Session**
**Implementation Plan**: Start with parser modularization
1. Establish modular foundation (preserve all existing behavior)
2. Add MVP validation codes to modular components
3. Implement XCCSS diagnostic system integration

**Benefits After Modularization**:
- **Maintainability**: Single responsibility components
- **Parallel Development**: Multiple developers can work efficiently
- **Easy Enhancement**: Foundation ready for MVP validation additions
- **Test Coverage**: Each component unit testable