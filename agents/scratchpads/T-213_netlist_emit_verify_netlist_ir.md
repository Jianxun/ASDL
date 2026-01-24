# T-213: Netlist verification consumes NetlistIR

## Task summary (DoD + verify)
- Update netlist verification to accept NetlistIR dataclasses as the primary
  input, reusing `verify_netlist_ir(...)` for structural checks before
  backend/template validation.
- Introduce a NetlistIR index helper (module/device lookup by `(file_id, name)`)
  in emit utils and keep diagnostics parity with the existing emit verification
  (missing backend, placeholders, variable merge errors).
- Add tests that exercise NetlistIR verification in the emit path without xDSL
  dependencies.
- Verify: `venv/bin/pytest tests/unit_tests/emit/test_netlist_emit_verify.py -v`

## Read (paths)
- `agents/roles/executor.md`
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `src/asdl/emit/netlist/verify.py`
- `src/asdl/emit/netlist/ir_utils.py`
- `tests/unit_tests/emit/test_netlist_emit_verify.py`

## Plan
- Inspect current emit/netlist verify helpers and NetlistIR verifier usage.
- Add NetlistIR index helper in `ir_utils.py` (module/device lookups, top name).
- Refactor emit verifier to accept NetlistIR, call `verify_netlist_ir(...)`, then
  run backend/template checks with parity diagnostics.
- Add/adjust tests that exercise NetlistIR verification without xDSL.
- Run verify command.

## Todo
- Add NetlistIR emit verification tests (TDD).
- Implement NetlistIR index + emit verifier refactor.
- Run emit verifier tests.

## Progress log
- 2026-01-24 00:00 — Task intake complete; read task context + executor role; set T-213 to in_progress; created feature branch `feature/T-213-netlist-emit-verify-netlist-ir`; next step inspect current netlist emit verifier.
- 2026-01-24 00:27 — Added NetlistIR emit verification tests; new file `tests/unit_tests/emit/test_netlist_emit_verify.py`; ran pytest (failed due to IFIR-only verifier); commit 0f59653; next step refactor verifier to accept NetlistIR.
- 2026-01-24 00:50 — Implemented NetlistIR index + emit verification path in `src/asdl/emit/netlist/ir_utils.py` and `src/asdl/emit/netlist/verify.py`; commit a08c227; next step rerun tests.
- 2026-01-24 00:52 — Verified `venv/bin/pytest tests/unit_tests/emit/test_netlist_emit_verify.py -v` passes; next step finish closeout updates.
- 2026-01-24 00:58 — Opened PR https://github.com/Jianxun/ASDL/pull/223; next step update task status to ready_for_review.
- 2026-01-24 00:59 — Set T-213 status to ready_for_review with PR 223; next step run tasks_state lint and push updates.
- 2026-01-24 01:42 — Review intake: confirmed PR 223, scratchpad + verification logs present; set T-213 to review_in_progress; next step review scope and code changes.
- 2026-01-24 01:43 — Scope review complete; changes align with DoD and listed files; next step confirm verification logs and review code behavior.
- 2026-01-24 01:43 — Verified required pytest command logged in scratchpad (not rerun locally); next step finalize review decision.
- 2026-01-24 01:44 — Posted PR review comment marking review clean; set T-213 status to review_clean; next step merge and close out.
- 2026-01-24 01:46 — Set T-213 status to done (merged=true) and prepared closeout commit; next step push and merge PR.
- 2026-01-24 01:46 — Merged PR 223, deleted remote/local branch, and pruned refs; next step checkout main and pull.

## Patch summary
- Added NetlistIR emit verifier tests covering structural checks, missing backend, placeholder validation, and variable merge errors.
- Added NetlistIR symbol index helpers and NetlistIR verification path that reuses `verify_netlist_ir` before backend/template checks.

## PR URL
- https://github.com/Jianxun/ASDL/pull/223

## Verification
- `venv/bin/pytest tests/unit_tests/emit/test_netlist_emit_verify.py -v`

## Status request
- Ready for review.

## Blockers / Questions
- None yet.

## Next steps
- Inspect current emit verifier + NetlistIR helpers.
