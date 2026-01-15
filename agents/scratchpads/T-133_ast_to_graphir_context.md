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
- [x] Inspect current AST->GraphIR conversion flow and supporting helpers.
- [x] Design session/document context objects and new symbol/ID helper modules.
- [x] Refactor conversion to use context while preserving behavior + diagnostics.
- [x] Run verification for IR unit tests.

## Progress log
- 2026-01-14: Added GraphIR session/document contexts and extracted symbol helpers.

## Patch summary
- Added AST->GraphIR session/document context module and symbol/ID allocation helpers.
- Refactored AST->GraphIR conversion flow to use new contexts without behavior changes.

## PR URL
- https://github.com/Jianxun/ASDL/pull/141

## Verification
- `venv/bin/pytest tests/unit_tests/ir -v`

## Status request
- Ready for review

## Blockers / Questions
- None.

## Next steps
- Await review feedback.
