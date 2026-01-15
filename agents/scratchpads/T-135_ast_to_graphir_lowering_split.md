# T-135 Ast to GraphIR lowering split

## Task summary (DoD + verify)
- DoD: Move module/device lowering helpers into a dedicated lowering module and slim the AST->GraphIR facade to orchestration only, preserving the public API and behavior.
- Verify: `venv/bin/pytest tests/unit_tests/ir -v`

## Read
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
- [x] Inspect current AST->GraphIR lowering helpers and callers.
- [x] Extract module/device lowering into `ast_to_graphir_lowering.py` with docstrings.
- [x] Update facade to orchestrate via the new module; keep behavior unchanged.
- [x] Run verify command.

## Progress log
- 2026-01-20: Initialized task, set status to in_progress, created branch.
- 2026-01-20: Extracted lowering helpers into `ast_to_graphir_lowering.py`.
- 2026-01-20: Updated `ast_to_graphir.py` to call the lowering helpers.
- 2026-01-20: Verified `tests/unit_tests/ir`.

## Patch summary
- Added `ast_to_graphir_lowering.py` for module/device lowering helpers.
- Slimmed `ast_to_graphir.py` to orchestration + entry diagnostics.
- Updated scratchpad/task status for T-135.

## PR URL
- https://github.com/Jianxun/ASDL/pull/143

## Verification
- `venv/bin/pytest tests/unit_tests/ir -v`

## Status request
- Ready for Review

## Blockers / Questions
- None.

## Next steps
- Await review feedback.
