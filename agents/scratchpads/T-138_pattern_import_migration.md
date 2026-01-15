# T-138 Pattern import migration

## Task summary (DoD + verify)
- DoD: Update remaining imports to use asdl.ir.patterns, including NFIR
  dialect and parser tests, and delete src/asdl/patterns. Ensure tests
  referencing pattern helpers pass without the legacy module.
- Verify:
  - venv/bin/pytest tests/unit_tests/parser -v
  - venv/bin/pytest tests/unit_tests/ir -v

## Read
- agents/roles/executor.md
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- agents/scratchpads/T-138_pattern_import_migration.md

## Plan
- [x] Audit remaining imports of legacy pattern helpers.
- [x] Update imports to asdl.ir.patterns in code and tests.
- [x] Remove the legacy src/asdl/patterns package.
- [x] Run parser/ir tests and capture results.

## Progress log
- 2026-01-17: Prepared task context; set status to in_progress.
- 2026-01-17: Updated imports and removed legacy patterns package.
- 2026-01-17: Aligned parser tests and NFIR verification with new atomize API.

## Patch summary
- Updated NFIR dialect + parser tests to import from asdl.ir.patterns.
- Removed src/asdl/patterns legacy module package.
- Updated parser atomization expectations and NFIR endpoint checks for new
  AtomizedEndpoint fields.

## PR URL
- TBD

## Verification
- venv/bin/pytest tests/unit_tests/parser -v
- venv/bin/pytest tests/unit_tests/ir -v

## Status request
- In Progress

## Blockers / Questions
- None.

## Next steps
- Run parser and IR unit tests.
