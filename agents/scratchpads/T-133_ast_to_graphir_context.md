# T-133 Ast to GraphIR conversion context refactor

## Task summary (DoD + verify)
- Introduce conversion context objects for AST->GraphIR (session + document),
  extract symbol/ID allocation helpers into new modules, and update the
  top-level conversion flow to use the new context without changing
  behavior or diagnostics.
- Verify: `venv/bin/pytest tests/unit_tests/ir -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
- Inspect current AST->GraphIR conversion flow and supporting helpers.
- Design session/document context objects and new symbol/ID helper modules.
- Refactor conversion to use context while preserving behavior + diagnostics.
- Add/adjust tests if needed and run verification.

## Progress log
- 2026-01-XX: Task started.

## Patch summary
- TBD

## PR URL
- TBD

## Verification
- TBD

## Status request
- In progress

## Blockers / Questions
- None.

## Next steps
- Review current conversion helpers and define context boundaries.
