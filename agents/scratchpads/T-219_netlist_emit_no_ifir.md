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

## Patch summary

## PR URL

## Verification
- `venv/bin/pytest tests/unit_tests/emit/test_netlist_emit_verify.py tests/unit_tests/netlist/test_netlist_render_netlist_ir.py -v`
  - Result: 6 passed

## Status request
- In Progress

## Blockers / Questions

## Next steps
- Run verify tests for NetlistIR emit/verify.
- Update scratchpad with verification results and patch summary.
- Push branch and open PR when ready.
