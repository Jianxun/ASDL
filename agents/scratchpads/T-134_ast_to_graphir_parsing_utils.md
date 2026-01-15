# T-134 Ast to GraphIR parsing and utils split

## Task summary (DoD + verify)
- Extract instance/net/endpoint parsing helpers and diagnostic/attr utilities into dedicated modules.
- Update AST->GraphIR conversion to use shared helpers without changing behavior or error messaging.
- Verify with `venv/bin/pytest tests/unit_tests/ir -v`.

## Read
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
- Inspect current AST->GraphIR parsing/diagnostic helpers.
- Move parsing helpers into `ast_to_graphir_parsing.py` and utility helpers into `ast_to_graphir_utils.py`.
- Update `ast_to_graphir.py` to use shared helpers and keep diagnostics identical.
- Add/adjust docstrings and any needed tests.

## Todo
- [x] Extract parsing helpers into `ast_to_graphir_parsing.py` and update usage.
- [ ] Extract diagnostic/attr helpers into `ast_to_graphir_utils.py` and update usage.
- [ ] Run `venv/bin/pytest tests/unit_tests/ir -v`.

## Progress log
- 2026-01-xx: Initialized task, set status to in_progress, created feature branch.
- 2026-01-xx: Moved parsing helpers into `ast_to_graphir_parsing.py`.

## Patch summary
- TBD

## PR URL
- TBD

## Verification
- TBD

## Status request
- In Progress

## Blockers / Questions
- None yet.

## Next steps
- Review current parsing/diagnostic utilities in GraphIR converter and plan extraction.
