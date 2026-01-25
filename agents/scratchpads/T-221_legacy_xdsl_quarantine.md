# Task summary (DoD + verify)
- **DoD**: Move the xDSL IR implementation and tests out of the active tree (`src/asdl/ir`, `tests/unit_tests/ir`, and any xdsl-only netlist tests) into `legacy/`, and update the codebase map to point to their legacy location. Active imports must not reference the moved modules.
- **Verify**: `venv/bin/pytest tests/unit_tests/emit/test_netlist_emit_verify.py tests/unit_tests/netlist/test_netlist_render_netlist_ir.py tests/unit_tests/cli -v`

# Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

# Plan
- [x] Inspect xDSL IR code/tests and identify active imports to address.
- [x] Relocate xDSL IR code/tests into `legacy/` and prune active imports.
- [x] Update codebase map for new legacy locations.
- [x] Verify required tests.

# Progress log
- 2026-01-25 01:37 — Task intake: reviewed contract/tasks/state; created scratchpad; set T-221 in_progress and linted tasks_state; next step inspect xDSL IR/tests for relocation.
- 2026-01-25 01:46 — Moved xDSL IR tree into legacy and relocated IR/lowering/pattern tests to legacy; created legacy test/lowering dirs; next step remove remaining asdl.ir imports in active emit/lowering modules and update codebase map.
- 2026-01-25 01:46 — Removed asdl.ir imports from emit/lowering (inline helpers), updated package docstring and codebase map to point to legacy IR; next step review tree for lingering refs and commit.
- 2026-01-25 01:47 — Committed move of xDSL IR/tests into legacy (13caf5f); next step commit active import cleanups and doc updates.
- 2026-01-25 01:48 — Committed active import cleanups + codebase map update (906cff5); next step stage scratchpad/state updates and run verification.
- 2026-01-25 01:48 — Verified required pytest targets (emit/netlist/cli) succeeded; next step update scratchpad verification section and prep PR.
- 2026-01-25 01:50 — Opened PR https://github.com/Jianxun/ASDL/pull/232; next step update tasks_state to ready_for_review and push scratchpad/state updates.
- 2026-01-25 01:50 — Set T-221 ready_for_review with PR 232 and linted tasks_state; next step commit scratchpad/state updates and push.
- 2026-01-25 01:50 — Committed scratchpad/status updates (1d041b5); next step push branch updates.

# Patch summary
- Moved xDSL IR implementation and related lowering + tests into `legacy/src/asdl/ir`, `legacy/src/asdl/lowering`, and `legacy/tests/unit_tests`.
- Removed active-tree dependencies on `asdl.ir` (netlist diagnostics/verify/templates, lowering exports) and updated package docstring/codebase map to reflect legacy location.

# PR URL
- https://github.com/Jianxun/ASDL/pull/232

# Verification
- `venv/bin/pytest tests/unit_tests/emit/test_netlist_emit_verify.py tests/unit_tests/netlist/test_netlist_render_netlist_ir.py tests/unit_tests/cli -v`

# Status request
- Ready for review.

# Blockers / Questions

# Next steps
- Await reviewer feedback.
