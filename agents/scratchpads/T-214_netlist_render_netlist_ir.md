# T-214: Refactor netlist renderer to consume NetlistIR

## Task summary (DoD + verify)
- Update netlist rendering to accept NetlistIR dataclasses instead of xDSL IFIR ops.
- Use NetlistIR index helper for module/device lookup and `(ref_file_id, ref)` resolution.
- Preserve template rendering semantics, deterministic ordering, parameter/variable merge, and placeholder validation behavior.
- Add render tests that exercise NetlistIR inputs and parity with existing outputs.
- Verify: `venv/bin/pytest tests/unit_tests/netlist/test_netlist_render_netlist_ir.py -v`

## Read (paths)
- `agents/roles/executor.md`
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `agents/scratchpads/T-214_netlist_render_netlist_ir.md`

## Plan
- [x] Inspect existing netlist rendering + ir_utils helpers to identify xDSL IFIR dependencies.
- [x] Add/adjust NetlistIR render tests to lock expected output behavior.
- [x] Refactor renderer to use NetlistIR dataclasses and NetlistIRIndex lookups.
- [x] Update related helpers (templates/params) only if needed to keep parity.
- [x] Run targeted tests and capture results.

## Progress log
- 2026-01-24 09:55 — Task intake; read executor role + context files; confirmed T-214 ready and depends on T-213 (done); next step update task state to in_progress.
- 2026-01-24 10:00 — Set `T-214` status to in_progress and ran `scripts/lint_tasks_state.py` (OK); next step create feature branch.
- 2026-01-24 10:02 — Created branch `feature/T-214-netlist-render-netlist-ir`; next step inspect netlist renderer + tests.
- 2026-01-24 10:15 — Added NetlistIR render tests for device params/pattern ports and ref_file_id module resolution; ran pytest (2 failing as expected); next step refactor renderer to accept NetlistIR.
- 2026-01-24 10:17 — Committed test additions (cf7a8e8: “Add NetlistIR netlist render tests”); next step implement NetlistIR rendering.
- 2026-01-24 10:45 — Implemented NetlistIR rendering path in netlist renderer (dispatcher, NetlistIR symbol resolution, pattern rendering, conns ordering) and updated params dict helper; tests now passing; next step commit changes.
- 2026-01-24 10:47 — Ran `venv/bin/pytest tests/unit_tests/netlist/test_netlist_render_netlist_ir.py -v` (pass); next step commit implementation.
- 2026-01-24 10:49 — Committed NetlistIR rendering changes (66606e1: “Render NetlistIR netlists”); next step update scratchpad summary and prep closeout.
- 2026-01-24 10:55 — Opened PR https://github.com/Jianxun/ASDL/pull/224; next step update task state to ready_for_review.
- 2026-01-24 10:57 — Set T-214 status to ready_for_review (PR 224) and ran `scripts/lint_tasks_state.py` (OK); next step push metadata updates.

## Patch summary
- Added NetlistIR render tests covering pattern-aware ports, param/variable merges, and ref_file_id module selection.
- Added NetlistIR rendering path in netlist renderer with NetlistIRIndex lookups, pattern rendering, and ordered connection validation.
- Extended params dict stringification helper to accept mapping inputs from NetlistIR.

## PR URL
- https://github.com/Jianxun/ASDL/pull/224

## Verification
- `venv/bin/pytest tests/unit_tests/netlist/test_netlist_render_netlist_ir.py -v`

## Status request
- Ready for review.

## Blockers / Questions
- None.

## Next steps
- Await review feedback.
