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
- Audit remaining imports of legacy pattern helpers.
- Update imports to asdl.ir.patterns and remove legacy module.
- Run parser/ir tests and capture results.

## Progress log
- 2026-01-17: Prepared task context; set status to in_progress.

## Patch summary
- TBD

## PR URL
- TBD

## Verification
- TBD

## Status request
- In Progress

## Blockers / Questions
- None.

## Next steps
- Update imports and delete legacy patterns module.
