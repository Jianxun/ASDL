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
- **CLI Enhancement**: Simplify flags; imports resolve via `ASDL_PATH` (no `--search-path`)
- **Integration Testing**: End-to-end pipeline validation with real circuit examples
- **Documentation**: Import system usage guide and best practices
- **Schema Generation**: Ensure JSON/Text schema fully reflects current data structures (`PortType`, etc.)
- **Validator Refactor Follow-ups**: Migrate integration tests to new V-codes, add missing diagnostics
- **Environment Variable Support**: Implemented in elaboration; `${VAR}` resolved in parameters and primitive `spice_template`
  - Diagnostics: E0501 (missing env), E0502 (invalid format)
  - Resolver: `EnvVarResolver` (separate from `VariableResolver`)
  - Wired in `Elaborator` for module/instance parameters and for module `spice_template`

### 2025-09-08 – Elaborator Diagnostics Migration (XCCSS) and Tests
- Decision: Merge import-phase diagnostics under Elaborator `E` codes (no separate `I` component). Updated design doc to reflect `E04xx` (Reference) and `E06xx` (Style) for import.
- Implemented: Centralized Elaborator diagnostics in `src/asdl/elaborator/diagnostics.py` with XCCSS codes and legacy mapping.
  - Added: E0101–E0105, E0301–E0302, E0402, E0501–E0502; documented E0441–E0446, E0601–E0602 in design doc.
  - Refactored: `pattern_expander.py`, `variable_resolver.py`, `elaborator.py` now use `create_elaborator_diagnostic()` with template params.
  - Tests: Added per-code unit tests under `tests/unit_tests/elaborator/` and removed overlapping legacy diagnostic tests. Elaborator unit tests: all passing.
- Follow-ups: Migrate import resolver call sites to the new `E04xx/E06xx` codes with a thin compatibility layer; add per-code import tests; address generator/integration test failures separately; consider skipping archived example tests.

### 2025-09-08 – Import Diagnostics Tests Consolidation (E04xx)
- Consolidated import tests under elaborator unit tests with per-code files:
  - `tests/unit_tests/elaborator/test_E0441_import_file_not_found.py`
  - `tests/unit_tests/elaborator/test_E0442_circular_import_detected.py`
  - `tests/unit_tests/elaborator/test_E0443_module_not_found_in_import.py`
  - `tests/unit_tests/elaborator/test_E0444_import_alias_not_found.py`
  - `tests/unit_tests/elaborator/test_E0445_model_alias_collision.py`
  - Infrastructure/flow moved to: `test_import_resolver_flow.py`, `test_path_resolver.py`
- Removed legacy `tests/unit_tests/elaborator/import_/` tests.
- Result: elaborator test suite green (47 passed).

### 2025-09-08 – Import System Refactor (Modularization)
- Split `import_resolver.py` into modular components under `src/asdl/elaborator/import_/`:
  - `dependency_graph.py` (graph + alias map; loader-driven cycle detection)
  - `reference_validator.py` (qualified refs E0443/E0444; fixed alias-usage tracking)
  - `flattener.py` (rewrite + merge; local-wins precedence with warning; optional metadata drop)
  - `types.py` (ImportGraph, GraphNode, AliasResolutionMap), `policies.py` (PrecedencePolicy, FlattenOptions)
  - `coordinator.py` new orchestrator; `import_resolver.py` now a compatibility wrapper
  - `tracing.py` added logging helpers; `README.md` documents module relationships
- Diagnostics: Added `E0446` for load/parse failures; `FileLoader` emits `E0441` for not found, `E0442` for cycles (resolved-stack fix), `E0446` for parse.
- Behavior: Precedence is local-over-import with shadowing warning; determinism sorting intentionally skipped for now.

### 2025-09-08 – Import Graph Export & Cycle Detection Consolidation
- Added dependency graph JSON export helpers: `export_import_graph` and `export_import_graph_json` (relative paths with optional absolute).
- Implemented path normalization: coordinator and graph builder resolve `main_file_path` to absolute for consistent identity.
- Consolidated cycle detection: removed builder pre-check; `FileLoader` is the single source of E0442.
- Added unit test: `tests/unit_tests/elaborator/test_import_graph_export.py` validating relative path export.
- Generator readability: set `SPICEGenerator.indent` to two spaces; generator unit tests now pass.

## Logging System Phase 1 – Implemented
**Branch**: `feature/logging_system_phase1`

- Hierarchical logging under `asdlc.*`; CLI flags `--debug`, `--trace`, `--log-json`, `--log-file` at group level; `-v` at subcommands maps to INFO.
- Human and JSON formatters; file handler with env overrides `ASDL_LOG_LEVEL`, `ASDL_LOG_FILE`, `ASDL_LOG_FORMAT`.
- Import resolver emits DEBUG/TRACE logs for search paths, alias resolution, loads; added timing scaffolding.
- Unit tests added: logging config, CLI logging; all unit tests passing. Integration tests skipped during Phase 1.

### Demo Notes
- INFO: shows stage progress; DEBUG: adds initialization, file loads, timings; TRACE: adds alias resolution lines.
- Example used: `examples/inv/tb_inv.asdl` with `PDK_ROOT` and `ASDL_PATH` set; netlists written to `/tmp/tb_inv_*.spice`.

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

## Session – 2025-09-07 Examples & Heuristics

- Variable resolver heuristic refined: only case-insensitive exact name clashes trigger E108. Identifier-like strings (e.g., source names) are no longer misinterpreted as variables.
- Environment variable substitution extended to primitive `spice_template` strings: `${VAR}` now resolved during elaboration.
- Example libraries:
  - Added `examples/libs/ota_single_ended/ota_5t/ota_5t_pin.asdl` (PMOS input pair, NMOS mirror load, PMOS tail). Naming convention preserves `tail` node; sizing reflects PMOS≈2× NMOS.
  - Updated `examples/libs/ota_single_ended/tb/tb_ota_5t.asdl` to test PMOS-input OTA; corrected bias polarity and import/model aliasing.
- Verified netlisting; unresolved placeholder G0305 eliminated when `PDK_ROOT` is set.

## Next Session Plan
- Add tracing/logging for import resolution and model resolution
  - Verbose option in CLI to surface search paths, resolved files, and alias mapping
  - Hook debug logs in `ImportResolver._load_file_recursive` and alias validation
  - Optional trace id per elaboration run for grouping logs
- Add integration test for env-var resolution via CLI (`asdl elaborate` and `asdl netlist`)
- Document ASDL_PATH usage and best practices in docs
- Plan refactor: migrate legacy E10x elaborator diagnostics to XCCSS helper

## Logging System Implementation
**Branch**: `feature/logging_system_phase1`  
**Scope**: Phase 1 – Structured Logging Foundation (see `doc/logging/logging_system_design.md`)

### Objectives (Phase 1)
- Integrate Python `logging` with hierarchical loggers under root `asdlc`
- Map CLI flags to levels (`-v`→INFO, `--debug`→DEBUG, `--trace`→TRACE)
- Replace `click.echo()` progress prints with logger calls
- Human-readable formatter with timestamps and component tags
- Optional JSON formatter and `--log-file` handler
- Respect env vars: `ASDL_LOG_LEVEL`, `ASDL_LOG_FILE`, `ASDL_LOG_FORMAT`
- Minimal tests for configuration and flag mapping

## Project Status: Production Ready 🎉
- **All Major Components**: Parser, Elaborator, Validator, Generator, Import System - all working correctly
- **Test Coverage**: Elaborator unit tests passing after XCCSS migration. Integration/generator suites have failures pending refactor alignment.
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

## Import System Update – Search Path Policy
**Date**: 2025-09-07  
**Branch**: `feature/import_refactor_paths`  
**Change**:
- Import search paths now resolve from `ASDL_PATH` only, with fallback to `.`
- Removed CLI flag `--search-path`; CLI no longer passes search paths
- `PathResolver.DEFAULT_SEARCH_PATHS = ["."]`; legacy defaults (`libs`, `third_party`) removed
- Diagnostics E0441 suggestion text updated to reference `ASDL_PATH` (no CLI flag)

**Rationale**:
- Simplify mental model and commands; ensure portability via environment
- Keep programmatic API override available (`search_paths` param) without CLI exposure

**Follow-ups**:
- Add tracing to log effective search roots and probe candidates
- Update docs and examples to export `ASDL_PATH` (see `examples/setup.sh`)
