# Task summary (DoD + verify)
- DoD: Hard-deprecate AST->NFIR and NFIR->IFIR converters by removing them from public exports, relocating the modules under `legacy/` (or deleting them if no longer needed), and updating any call sites to use AST->GraphIR and GraphIR->IFIR instead. Update/trim tests to match the new export surface, and document NFIR as projection-only.
- Verify: `venv/bin/pytest tests/unit_tests/ir -v`

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Explain task understanding and confirm scope (exports, relocations, call sites, tests, doc note).
- Update call sites/tests to the GraphIR pipeline and adjust public exports.
- Relocate or remove NFIR converters under legacy and update docs.
- Verify and record results.

# Todo
- [x] Review current NFIR converter exports/usages and decide deletions vs legacy moves.
- [x] Update tests/imports to use AST->GraphIR + GraphIR->IFIR only.
- [x] Remove NFIR converters from public exports.
- [x] Relocate NFIR converter modules under legacy/ (or delete).
- [x] Document NFIR as projection-only in spec.

# Progress log
- 2026-01-14: Understanding: remove AST->NFIR and NFIR->IFIR from public exports, move converter modules to legacy (or delete), update tests/call sites to GraphIR path, and document NFIR as projection-only.
- 2026-01-14: Trimmed NFIR converter tests and exports; moved converters under legacy.
- 2026-01-14: Updated NFIR spec to call out projection-only status.
- 2026-01-14: Ran IR unit tests and opened PR #130.
- 2026-01-14: Updated pipeline spec to reflect AST->GraphIR flow and added GraphIR converter error coverage.
- 2026-01-14: Re-ran IR unit tests after review fixes.

# Patch summary
- Removed NFIR converter tests and retained GraphIR->IFIR coverage.
- Re-exported GraphIR converters from `src/asdl/ir` and `src/asdl/ir/converters`.
- Relocated deprecated NFIR converters under `legacy/src/asdl/ir/converters`.
- Updated NFIR spec to mark it as projection-only.
- Updated pipeline spec to remove NFIR stages and document GraphIR->IFIR projection.
- Added GraphIR conversion tests for invalid instance/endpoint expressions.

# PR URL
- https://github.com/Jianxun/ASDL/pull/130

# Verification
- `venv/bin/pytest tests/unit_tests/ir -v`
- `venv/bin/pytest tests/unit_tests/ir -v`

# Status request (Done / Blocked / In Progress)
- Ready for Review

# Blockers / Questions

# Next steps
- Await review feedback.
