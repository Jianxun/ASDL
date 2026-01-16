# Task summary (DoD + verify)
- Merge device/backend variables for emission, expose them as template placeholders, and emit diagnostics when instance params attempt to override variable keys or when variables collide with parameter keys or backend props. Update template validation to allow variables and add netlist tests covering variable placeholders and collision errors.
- Verify: `venv/bin/pytest tests/unit_tests/netlist -v`

# Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

# Plan
- [x] Inspect current netlist emission placeholders/validation + diagnostics flow for params/props.
- [x] Implement variable merge + collision checks and placeholder exposure.
- [x] Update template validation rules for variables.
- [x] Add netlist tests for variable placeholders + collision diagnostics.
- [x] Run `venv/bin/pytest tests/unit_tests/netlist -v`.

# Progress log
- 2026-01-16: Task initialized and context collected.
- 2026-01-16: Added netlist tests and GraphIR helper coverage for device/backend variables.
- 2026-01-16: Implemented variable merge/collision diagnostics and template placeholder support; netlist tests passing.

# Patch summary
- Added netlist tests for variable placeholders plus collision diagnostics.
- Added variable merge/validation in emission + verification and allowed variable placeholders in templates.

# PR URL
- https://github.com/Jianxun/ASDL/pull/151

# Verification
- `venv/bin/pytest tests/unit_tests/netlist -v`
  - PASS

# Status request (Done / Blocked / In Progress)
- Done

# Blockers / Questions
- None yet.

# Next steps
- Await review feedback.
