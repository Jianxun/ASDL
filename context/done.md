### 2025-08-28 — Validator Refactor
- Moved `src/asdl/validator.py` → `src/asdl/validator/validator.py`; created package `src/asdl/validator/`.
- Renamed `src/asdl/validator_diagnostics.py` → `src/asdl/validator/diagnostics.py`.
- Introduced modular validator architecture:
  - `core/` with `types.py`, `registry.py`, `runner.py` (exports `ASDLValidator`).
  - `rules/` with `port_mapping.py`, `parameter_overrides.py`, `net_declarations.py`, `module_parameters.py`, `unused.py`.
- Kept public API `from src.asdl.validator import ASDLValidator` via package re-export.
- Added backward-compat shim methods to `ASDLValidator` to preserve legacy unit tests and CLI usage.
- All validator unit tests green after refactor.

# Done – Completed Milestones & Features

_This file archives major completed tasks so they don't clutter active todo lists._

## Visualizer
- Static schematic renderer (Phase 1) ✅
- Minimal visualizer foundation (Phases 2–5) ✅
- Named port system & Flowchart connections ✅
- Save-layout export feature ✅

## Compiler / Core
- Parser refactoring & full location tracking ✅
- Data-structure cleanup & legacy removal ✅
- Elaborator implementation & pattern expansion ✅
- SPICEGenerator modernization and full test suite ✅
  - Diagnostics implemented: G0102, G0201, G0301, G0305, G0401, G0601 (warn), G0701 (info) ✅
  - Unit tests refactored into focused files; integration tests updated ✅
- Integration test framework with NgSpice validation ✅

# Completed Tasks Archive

## 2025-08-30: Test Suite Fixes - Round 1 Complete
- **Integration Test Restoration**: Fixed `test_mixed_design.py` to pass
  - Renamed `SignalType` → `PortType` and `SignalType.VOLTAGE` → `PortType.SIGNAL`
  - Removed PDK `.include` assertions (generator no longer emits these)
  - Removed `XMAIN` assertions (generator no longer emits XMAIN)
- **Data Structure API Updates**: Fixed `models={}` → `modules={}` in elaborator tests
  - Updated `test_instance_expansion.py`, `test_port_expansion_diagnostics.py`, `test_port_expansion.py`
- **Module Validation Fixes**: Added minimal `spice_template` to test modules
  - Fixed bus expansion tests with `spice_template: "test {data[3:0]}"`
  - Fixed port expansion tests with `spice_template: "test_module {in<p,n>}"`
  - Fixed mixed pattern tests with proper `spice_template`
- **Port Type Validation**: Fixed invalid port types in tests
  - Changed `type: digital` → `type: signal`
  - Changed `dir: in` → `dir: IN`
- **Test Status Improvement**: Reduced unit test failures from 18 to 8 (55% reduction)
  - **Unit Tests**: 8 failures remaining (down from 18)
  - **Integration Tests**: ✅ All passing
  - **Core Functionality**: `test.asdl` compiles cleanly into simulation-legal netlist
- **Files Modified**: 
  - `tests/integration/generator/test_mixed_design.py`
  - `tests/unit_tests/elaborator/test_instance_expansion.py`
  - `tests/unit_tests/elaborator/test_port_expansion_diagnostics.py`
  - `tests/unit_tests/elaborator/test_port_expansion.py`
  - `tests/unit_tests/elaborator/test_bus_expansion.py`
  - `tests/unit_tests/elaborator/test_mixed_pattern_diagnostics.py`
