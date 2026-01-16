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
- [ ] Inspect current netlist emission placeholders/validation + diagnostics flow for params/props.
- [ ] Implement variable merge + collision checks and placeholder exposure.
- [ ] Update template validation rules for variables.
- [ ] Add netlist tests for variable placeholders + collision diagnostics.
- [ ] Run `venv/bin/pytest tests/unit_tests/netlist -v`.

# Progress log
- 2026-01-16: Task initialized and context collected.

# Patch summary
- TBD

# PR URL
- TBD

# Verification
- TBD

# Status request (Done / Blocked / In Progress)
- In Progress

# Blockers / Questions
- None yet.

# Next steps
- Implement netlist variable placeholders + diagnostics; add tests; run verify.
