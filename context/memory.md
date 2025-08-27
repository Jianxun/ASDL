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
8. **Project Venv Usage**: Always use project-wide Python venv at `venv/` for commands/tests

## Known Limitations
- **YAML Pattern Parsing**: `ruamel.yaml` has issues with inline dictionary mappings containing `<p,n>` patterns. Use multi-line YAML format as workaround.

## Current Focus Areas
- **Import System Phase 1.2.5**: Enhanced elaborator integration (3-phase processing: Import → Pattern → Variable)
- **CLI Integration**: Add --search-path arguments and import resolution support
- **Integration Testing**: End-to-end pipeline validation with real circuit examples
- **Documentation**: Import system usage guide and best practices
  - See also: context/import_implementations.md for a distilled implementation snapshot

### ✅ Generator Refactor Decisions (2025-08-27)
- Remove XMAIN from netlist output entirely.
- Remove automatic PDK `.include` emission from the generator; PDK handling is injected by a higher-level simulation orchestrator (or future CLI header-prepend facility).
- Introduce top-level rendering modes:
  - `subckt`: emit `.subckt {top} … .ends` with `top` last.
  - `flat`: comment only the top `.subckt`/`.ends` wrapper lines with `*`; preserve body unchanged.
- Emit hierarchical subcircuits in dependency order (children-before-parents), with `top` last.
- Refactor `spice_generator.py` into components: options, ordering, subckt builder, instance rendering (templates/calls), formatting, guards, and postprocess.
- Validation vs generation: keep minimal defensive generator diagnostics (unknown model, missing mappings, unresolved placeholders, variable-shadowing), while CLI runs validator first and skips generation on prior ERRORs.
- Breaking changes policy: accept test breakage during MVP refactor; update tests after implementation.

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

### **Phase 1.2.6 (2025-08-25)**
- Implemented post-load validation for qualified instance references:
  - **E0444** Unknown import alias
  - **E0443** Module not found in imported file
- Added quality warnings:
  - **I0601** Unused import alias
  - **I0602** Unused model alias
- Enhanced **E0441** details to include explicit probe paths.
- Updated CLI `netlist` to skip generation when any ERROR diagnostics exist (prevents runtime exceptions and surfaces diagnostics).
- Added unit tests for E0443/E0444 and probe paths; scaffolded CLI integration test for toy example.

### **Generator Refactor & XCCSS Migration (2025-08-25)**
- Refactored monolithic `src/asdl/generator.py` into package `src/asdl/generator/` with `spice_generator.py` and `diagnostics.py`.
- Adopted XCCSS diagnostics for generator; implemented per-code tests under `tests/unit_tests/generator/`.
- Diagnostics implemented: `G0102` (top not found), `G0201` (unconnected port), `G0301` (invalid module), `G0305` (unresolved placeholders), `G0401` (unknown model), `G0601` (variable shadows parameter - WARNING), `G0701` (no top specified - INFO).
- Consolidated pipeline structure tests under `tests/integration/generator/`; split verbose unified tests into focused suites: primitives, hierarchical, variables, empty design.
- Added `doc/test/unit_test_strategy.md` documenting the project-wide unit test strategy from this refactor.
- Added `context/todo_generator.md` to track PDK include path redesign.

### **Generator Diagnostics Roadmap (Unit Test Focus)**
- Diagnostics-first policy in generator unit tests; no raw exceptions in unit layer.
- Planned diagnostics:
  - G0102 Top module not found (ERROR): top specified but missing in `modules`; no XMAIN emitted; emit header comment.
  - G0301 Invalid module definition (ERROR): module lacks both `spice_template` and `instances`; skip generation for that module.
  - G0201 Unconnected port in subcircuit call (ERROR): missing port mappings; annotate and skip instance emission.
  - I0701 Missing top module (INFO): no top specified; document skipped XMAIN.
- Tests will be added per-code in `tests/unit_tests/generator/`; unified tests de-duplicated.

### **Parser Phase 0 Complete (2025-08-25)**
- Introduced parser XCCSS diagnostics module `src/asdl/parser/diagnostics.py` with `create_parser_diagnostic`.
- Imports simplified to file-path strings; consolidated import diagnostics under parser P-codes:
  - P0501 Invalid Import Path Type (non-string)
  - P0502 Invalid Import File Extension (not .asdl)
- Began XCCSS migration for parser codes:
  - P100→P0101, P101→P0102, P102→P0201, P103→P0202
  - P200→P0701 (unknown top-level), P201→P0702 (unknown field)
- Updated unit tests to match (refactored imports tests, dropped rich import objects).

### **Parser Test Suite Refactor — Phase 1 Progress (2025-08-26)**
- Consolidated YAML/root diagnostics into canonical `tests/unit_tests/parser/test_yaml_and_root.py` covering P0101/P0102 and empty content behavior.
- Parameterized unknown top-level section diagnostics into `tests/unit_tests/parser/test_toplevel_sections.py` covering P0701 for `models` and `future_feature`.
- Removed redundant `tests/unit_tests/parser/test_error_handling.py` and deduplicated P0701 case from `test_unified_parsing.py`.
- All parser unit tests green: 45 passed.

### **Parser XCCSS Migration Completed (2025-08-26)**
- Migrated legacy parser codes to XCCSS and updated registry:
  - P107→P0230, P108→P0231, P104→P0240 (port), P104→P0250 (instance), P105→P0205,
    P301→P0601, P302→P0602. Kept existing P0101, P0102, P0201, P0202, P0501, P0502, P0503, P0701, P0702.
- Created one-per-code unit tests named after codes (e.g., `test_p0240_missing_port_dir.py`).
- Pruned overlapping consolidated tests in favor of per-code tests.
- Current parser unit tests: 38 passed.

### **Parser Phase 4 — Enum Validation (2025-08-26)**
- Implemented enum-specific diagnostics:
  - P0511 Invalid Port Direction Enum
  - P0512 Invalid Port Type Enum
- Updated `PortParser` to emit enum-specific errors instead of generic P0205.
- Added unit tests `test_p0511_invalid_port_direction_enum.py` and `test_p0512_invalid_port_type_enum.py`.
- Adjusted `test_p0205_port_parsing_error.py` to expect P0511 for invalid direction value.

### **Parser Test Suite Refactor — Naming Cleanup (2025-08-26)**
- Removed redundant `tests/unit_tests/parser/test_unified_parsing.py`; negative cases are covered by per-code tests:
  - P0230 in `test_p0230_module_type_conflict.py`
  - P0231 in `test_p0231_incomplete_module_definition.py`
  - P0501 in `test_p0501_invalid_import_path_type.py`
  - P0502 in `test_p0502_invalid_import_file_extension.py`
- Kept and relocated positive-path coverage into focused suites:
  - `tests/unit_tests/parser/test_parser_positive_paths.py` (happy-path parsing and imports)
  - `tests/unit_tests/parser/test_parser_basics.py` (root/yaml basics where applicable)
  - `tests/unit_tests/parser/test_parser_modules.py` (module-focused behaviors)
  - `tests/unit_tests/parser/test_parser_location_tracking.py` (centralized location tracking)
- Suite structure now: per-code diagnostics files + focused positive-path/module/location suites.

### Generator Refactor Progress (2025-08-27)
- Modularization complete for generator: `options`, `ordering`, `subckt`, `instances`, `templates`, `calls`, `formatting`, `guards`, `postprocess`.
- Removed automatic PDK `.include` emission and `XMAIN` emission; preserved diagnostics behavior (G0102, G0701).
- `SPICEGenerator.generate()` split into helper methods for readability and testability.
- Implemented hierarchical dependency ordering (children-first; `top` last) and `TopStyle.FLAT` (comment-only wrappers for top).
- CLI supports `--top-style {subckt,flat}`; options threaded to generator.
- All generator unit tests passing (20/20).

### Data Structures and Parser Updates (2025-08-27)
- Removed deprecated `PortConstraints` class and the `constraints` field from `Port`.
- Renamed `SignalType` → `PortType` with enum values: `signal`, `power`, `ground`, `bias`, `control`.
- `Port.type` is now optional with default `PortType.SIGNAL`.
- Updated `parser/sections/port_parser.py` to validate `PortType` and removed constraints parsing; updated P0512 messages.
- Updated exports in `src/asdl/data_structures/__init__.py` and `src/asdl/__init__.py`.
- Updated unit tests under `tests/unit_tests/` to use `PortType.SIGNAL`; removed all `PortConstraints` references.

### Data Structures Test Suite Simplification (2025-08-27)
- Archived legacy data structure tests referencing removed types (`PrimitiveType`, `DeviceModel`).
- Added lean, invariants-oriented tests covering: module invariants, port defaults/enums, instance helpers, locatable formatting, and `ASDLFile` basics.
- `tests/unit_tests/data_structures`: 14 passed.

### Current Unit Test Status (2025-08-27)
- Data structures unit tests: green (14/14).
- Generator unit tests: green.
- Validator unit tests: one suite still references legacy `DeviceModel` (to refactor next session).
- Integration tests intentionally skipped (under refactor).

### Next Session Plan
- Refactor validator test suite to align with unified data structures (remove `DeviceModel` usage).
- Focus on schema generation improvements now that data structures are stable:
  - Ensure JSON Schema and text schema fully reflect `PortType` and field metadata.
  - Remove any remaining duplication and align CLI `asdlc schema` behavior.
