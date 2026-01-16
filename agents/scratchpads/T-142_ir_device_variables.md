# Task summary (DoD + verify)
- Add `variables` attributes to GraphIR/IFIR device and backend ops and propagate AST device/backend variables through GraphIR and IFIR projections. Ensure GraphIR->IFIR projection preserves variables and add IR unit tests that assert variables are present and stringified.
- Verify: `venv/bin/pytest tests/unit_tests/ir -v`

# Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

# Plan
- [x] Add IR unit tests for device/backend variables (GraphIR + IFIR projection).
- [x] Add variables attributes to GraphIR/IFIR device/backend ops and wire AST->GraphIR + GraphIR->IFIR propagation.
- [x] Run `venv/bin/pytest tests/unit_tests/ir -v`.

# Progress log
- 2026-01-16: Collected task context and added IR variable coverage tests.
- 2026-01-16: Wired device/backend variables through GraphIR/IFIR ops + converters; tests pass.

# Patch summary
- Added GraphIR/IFIR device + backend variable attrs and propagated through lowering/projection.
- Added IR tests for stringified variables in GraphIR and preserved variables in IFIR.

# PR URL
- TODO

# Verification
- `venv/bin/pytest tests/unit_tests/ir -v`

# Status request (Done / Blocked / In Progress)
- In Progress

# Blockers / Questions
- None yet.

# Next steps
- Open PR and request review.
