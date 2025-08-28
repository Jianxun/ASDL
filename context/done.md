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
