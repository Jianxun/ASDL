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

### ✅ **Completed Systems**
- **Import System**: Full MVP implementation with circular import detection, CLI integration, and 41 passing tests
- **Generator**: Refactored into modular components with XCCSS diagnostics and 20 passing tests
- **Parser**: XCCSS migration complete with 39 passing tests and optimized test suite organization
- **Data Structures**: PortType enum system implemented, legacy types removed, 14 passing tests
- **Test Suite**: 136/136 unit tests passing (100% success rate) across all components
- **Schema Generation**: JSON/text schema from data structures, CLI integration
- **Visualizer**: Functional with jsPlumb, zoom/pan/drag, layout export

## Key Architectural Decisions
1. **Unified Module Architecture**: Single `Module` class for both primitive and hierarchical modules
2. **Import System Design**: File-based imports with ASDL_PATH resolution and `model_alias` section (see `doc/import_system/`)
3. **Unit Device Strategy**: Unit devices implemented as primitive modules (not hierarchical) for LVS compatibility
4. **Modular Parser**: 550-line monolith split into focused components (see `doc/parser/`)
5. **XCCSS Diagnostic System**: Structured error codes replacing PXXX (see `doc/diagnostic_system/`)
6. **Two-Stage Compilation**: Import Elaboration → SPICE Generation
7. **Tool Separation**: ASDL handles imports/resolution, external tools (ams-compose) handle versioning/reproducibility
8. **Project Venv Usage**: Always use project-wide Python venv at `venv/` for commands/tests

## Known Limitations
- **YAML Pattern Parsing**: `ruamel.yaml` has issues with inline dictionary mappings containing `<p,n>` patterns. Use multi-line YAML format as workaround.
- **Diagnostic Suppression**: Several diagnostic codes temporarily suppressed for clean compile experience (see `context/archive/2025-01-27_diagnostic_suppression_implementation.md`)

## Current Focus Areas
- **CLI Enhancement**: Add missing features like `--search-path` arguments and import resolution
- **Integration Testing**: End-to-end pipeline validation with real circuit examples
- **Documentation**: Import system usage guide and best practices
- **Schema Generation**: Ensure JSON/Text schema fully reflects current data structures (`PortType`, etc.)
- **Validator Refactor Follow-ups**: Migrate integration tests to new V-codes, add missing diagnostics
- **Environment Variable Support**: Implemented in elaboration; `${VAR}` resolved in parameters
  - Diagnostics: E0501 (missing env), E0502 (invalid format)
  - Resolver: `EnvVarResolver` (separate from `VariableResolver`)
  - Wired in `Elaborator` for module and instance parameters

## Environment Variable Support Design Decisions

### Architecture Decision: Environment Variables in Parameters
**Date**: 2025-01-27  
**Status**: Implemented (Phase 1.3.1–1.3.2 complete)  
**Decision**: Support `${VAR}` syntax in parameter values for dynamic environment-based configuration

### Core Design Principles
1. **Clean Integration**: Environment variables resolved in parameters, no changes to generator logic
2. **Strict Syntax**: Only `${VAR}` format supported, anything else emits error diagnostic
3. **Fail Fast**: No defaults, missing environment variables emit E0501 diagnostic
4. **Pipeline Integration**: Resolution happens during elaboration phase with parameter resolution

### Implementation Approach
- **New Resolver**: `EnvVarResolver.resolve_in_parameters()`
- **Error Codes**: E0501 (missing env var), E0502 (invalid format)
- **Integration**: In `Elaborator._elaborate_module` before variable reference resolution
- **No Generator Changes**: Reuses `{param}` substitution as-is

### Benefits
- **Flexibility**: Dynamic PDK paths, corners, temperatures from environment
- **Simplicity**: No changes to existing template substitution logic
- **Maintainability**: Clean separation of concerns
- **LVS Compatibility**: Environment variables resolved to concrete values before generation

### Example Usage
```yaml
parameters:
  pdk_root: ${PDK_ROOT}
  corner: ${CORNER}
  temp: ${TEMP}

spice_template: |
  .include {pdk_root}/devices.asdl
  .lib {pdk_root}/devices.lib {corner}
  .temp {temp}
```

## Next Session Plan
- Add tracing/logging for import resolution and model resolution
  - Verbose option in CLI to surface search paths, resolved files, and alias mapping
  - Hook debug logs in `ImportResolver._load_file_recursive` and alias validation
  - Optional trace id per elaboration run for grouping logs
- Add integration test for env-var resolution via CLI (`asdl elaborate` and `asdl netlist`)
- Document ASDL_PATH usage and best practices in docs
- Plan refactor: migrate legacy E10x elaborator diagnostics to XCCSS helper

## Project Status: Production Ready 🎉
- **All Major Components**: Parser, Elaborator, Validator, Generator, Import System - all working correctly
- **Test Coverage**: 136/136 unit tests passing (100% success rate)
- **Core Functionality**: `test.asdl` compiles cleanly into simulation-legal netlist
- **Architecture**: Stable and well-organized with clear separation of concerns
- **Documentation**: Comprehensive design documents and implementation guides available

## Archived Sessions
- **Import System MVP Implementation**: See `context/archive/2025-01-27_import_system_mvp_complete.md`
- **Generator Refactor & XCCSS Migration**: See `context/archive/2025-01-27_generator_refactor_xccss_migration.md`
- **Parser XCCSS Migration**: See `context/archive/2025-01-27_parser_xccss_migration_complete.md`
- **Data Structures and Parser Updates**: See `context/archive/2025-01-27_data_structures_parser_updates.md`
- **Test Suite Fixes**: See `context/archive/2025-01-27_test_suite_fixes_complete.md`
- **Diagnostic Suppression Implementation**: See `context/archive/2025-01-27_diagnostic_suppression_implementation.md`
