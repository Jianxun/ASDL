# Generator Refactor & XCCSS Migration - COMPLETED (2025-01-27)

## Generator Refactor Decisions (2025-08-27)
- Remove XMAIN from netlist output entirely.
- Remove automatic PDK `.include` emission from the generator; PDK handling is injected by a higher-level simulation orchestrator (or future CLI header-prepend facility).
- Introduce top-level rendering modes:
  - `subckt`: emit `.subckt {top} … .ends` with `top` last.
  - `flat`: comment only the top `.subckt`/`.ends` wrapper lines with `*`; preserve body unchanged.
- Emit hierarchical subcircuits in dependency order (children-before-parents), with `top` last.
- Refactor `spice_generator.py` into components: options, ordering, subckt builder, instance rendering (templates/calls), formatting, guards, and postprocess.
- Validation vs generation: keep minimal defensive generator diagnostics (unknown model, missing mappings, unresolved placeholders, variable-shadowing), while CLI runs validator first and skips generation on prior ERRORs.
- Breaking changes policy: accept test breakage during MVP refactor; update tests after implementation.

## Generator Refactor & XCCSS Migration (2025-08-25)
- Refactored monolithic `src/asdl/generator.py` into package `src/asdl/generator/` with `spice_generator.py` and `diagnostics.py`.
- Adopted XCCSS diagnostics for generator; implemented per-code tests under `tests/unit_tests/generator/`.
- Diagnostics implemented: `G0102` (top not found), `G0201` (unconnected port), `G0301` (invalid module), `G0305` (unresolved placeholders), `G0401` (unknown model), `G0601` (variable shadows parameter - WARNING), `G0701` (no top specified - INFO).
- Consolidated pipeline structure tests under `tests/integration/generator/`; split verbose unified tests into focused suites: primitives, hierarchical, variables, empty design.
- Added `doc/test/unit_test_strategy.md` documenting the project-wide unit test strategy from this refactor.
- Added `context/todo_generator.md` to track PDK include path redesign.

## Generator Diagnostics Roadmap (Unit Test Focus)
- Diagnostics-first policy in generator unit tests; no raw exceptions in unit layer.
- Planned diagnostics:
  - G0102 Top module not found (ERROR): top specified but missing in `modules`; no XMAIN emitted; emit header comment.
  - G0301 Invalid module definition (ERROR): module lacks both `spice_template` and `instances`; skip generation for that module.
  - G0201 Unconnected port in subcircuit call (ERROR): missing port mappings; annotate and skip instance emission.
  - I0701 Missing top module (INFO): no top specified; document skipped XMAIN.
- Tests will be added per-code in `tests/unit_tests/generator/`; unified tests de-duplicated.

## Generator Refactor Progress (2025-08-27)
- Modularization complete for generator: `options`, `ordering`, `subckt`, `instances`, `templates`, `calls`, `formatting`, `guards`, `postprocess`.
- Removed automatic PDK `.include` emission and `XMAIN` emission; preserved diagnostics behavior (G0102, G0701).
- `SPICEGenerator.generate()` split into helper methods for readability and testability.
- Implemented hierarchical dependency ordering (children-first; `top` last) and `TopStyle.FLAT` (comment-only wrappers for top).
- CLI supports `--top-style {subckt,flat}`; options threaded to generator.
- All generator unit tests passing (20/20).

## Status: ✅ COMPLETE - Production Ready
- Generator refactored into modular components
- XCCSS diagnostics fully implemented
- All 20 generator unit tests passing
- CLI integration complete with top-style options
- Hierarchical dependency ordering working
- PDK include and XMAIN emission removed as planned
