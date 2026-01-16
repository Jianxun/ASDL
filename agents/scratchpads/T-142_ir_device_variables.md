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
- [ ] Add IR unit tests for device/backend variables (GraphIR + IFIR projection).
- [ ] Add variables attributes to GraphIR/IFIR device/backend ops and wire AST->GraphIR + GraphIR->IFIR propagation.
- [ ] Run `venv/bin/pytest tests/unit_tests/ir -v`.

# Progress log
- 2026-01-16: Collected task context and added initial IR variable coverage tests.

# Patch summary
- TODO

# PR URL
- TODO

# Verification
- TODO

# Status request (Done / Blocked / In Progress)
- In Progress

# Blockers / Questions
- None yet.

# Next steps
- TODO
