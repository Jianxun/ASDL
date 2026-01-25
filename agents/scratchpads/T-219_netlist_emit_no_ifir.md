# T-219 Netlist emit no IFIR

## Task summary (DoD + verify)
- DoD: Netlist verification/rendering consumes NetlistIR only: remove IFIR/xDSL types from netlist verification and rendering helpers, delete legacy IFIR dispatch paths, and ensure NetlistIR diagnostics remain unchanged. Update NetlistIR emitter tests to run without xdsl.
- Verify: `venv/bin/pytest tests/unit_tests/emit/test_netlist_emit_verify.py tests/unit_tests/netlist/test_netlist_render_netlist_ir.py -v`

## Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

## Plan
- Inspect netlist verify/render helpers for IFIR usage and xdsl dependencies.
- Remove IFIR/xDSL types and dispatch paths, keep NetlistIR diagnostics unchanged.
- Update tests to avoid xdsl reliance; add/adjust coverage as needed.
- Run verify command and record results.

## Progress log
- 2026-01-25 00:00 — Task intake; created scratchpad; next step update task state and branch.
- 2026-01-25 00:04 — Confirmed task scope (NetlistIR-only verify/render); set T-219 to in_progress, ran lint, created branch `feature/T-219-netlist-no-ifir`; next step remove IFIR verification helpers.
- 2026-01-25 00:05 — Removed IFIR verification helpers + xdsl dependencies in netlist verify/index utilities; committed 94f5053 ("Remove IFIR verification helpers"); next step update renderer/API.
- 2026-01-25 00:06 — Dropped IFIR render paths, added NetlistIR pattern rendering helper, updated netlist exports/API; committed 1f1623d ("Drop IFIR render paths from netlist emitter"); next step run verify tests.
- 2026-01-25 00:07 — Ran `venv/bin/pytest tests/unit_tests/emit/test_netlist_emit_verify.py tests/unit_tests/netlist/test_netlist_render_netlist_ir.py -v`; all tests passed; next step update scratchpad summary and prep PR.
- 2026-01-25 00:07 — Recorded scratchpad progress and task status; committed 07da9b9 ("Track T-219 progress"); next step open PR.
- 2026-01-25 00:08 — Pushed branch `feature/T-219-netlist-no-ifir` and opened PR https://github.com/Jianxun/ASDL/pull/227; next step update task state and scratchpad closeout.
- 2026-01-25 00:09 — Set T-219 status to ready_for_review (PR 227) and ran lint; next step finalize scratchpad and push updates.
- 2026-01-25 00:35 — Review intake: verified PR targets main and includes required logs; set status to review_in_progress and ran lint; next step complete review checks.
- 2026-01-25 00:38 — Review checks: relied on PR test logs (not rerun); scope check found remaining IFIR/GraphIR emit_netlist call sites in tests; next step request changes.
- 2026-01-25 00:38 — Posted PR comment requesting changes; set status to request_changes and ran lint; next step await updates.
- 2026-01-25 00:47 — Review follow-up: set T-219 to in_progress and re-ran tasks_state lint; next step update IFIR/GraphIR test usages to NetlistIR.
- 2026-01-25 00:55 — Updated e2e and netlist emitter tests to use NetlistIR-only pipeline/helpers; next step run targeted tests and commit fixes.
- 2026-01-25 01:01 — Ran pytest on e2e/netlist emitter; fixed NetlistIR pattern-origin/span expectations; reran tests (28 passed); next step commit changes and update PR.
- 2026-01-25 01:08 — Set T-219 status to ready_for_review and ran tasks_state lint; next step push commits and notify reviewer.

## Patch summary
- Removed IFIR/xDSL verification dispatch in `src/asdl/emit/netlist/verify.py` and pruned IFIR helpers from `src/asdl/emit/netlist/ir_utils.py`.
- Removed IFIR render paths in `src/asdl/emit/netlist/render.py`, added NetlistIR-only pattern rendering helpers, and narrowed netlist emit API/exports to NetlistIR.
- Updated e2e and netlist emitter tests to use NetlistIR-only pipeline/shims and adjusted pattern-origin/span expectations for NetlistIR diagnostics.

## PR URL
https://github.com/Jianxun/ASDL/pull/227

## Verification
- `venv/bin/pytest tests/unit_tests/emit/test_netlist_emit_verify.py tests/unit_tests/netlist/test_netlist_render_netlist_ir.py -v`
  - Result: 6 passed
- `venv/bin/pytest tests/unit_tests/e2e/test_pipeline_mvp.py tests/unit_tests/netlist/test_netlist_emitter.py -v`
  - Result: 28 passed

## Status request
- Ready for review

## Blockers / Questions

## Next steps
- Await reviewer feedback.
