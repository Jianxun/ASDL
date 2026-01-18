# Task summary (DoD + verify)
- DoD: Extend IFIR module and net/instance ops to carry structured pattern provenance (pattern origin + expression table), and update GraphIR->IFIR conversion to pass through pattern origin attributes and the pattern expression table. Update IFIR dialect and converter tests to assert the structured metadata is preserved.
- Verify: `venv/bin/pytest tests/unit_tests/ir/test_ifir_dialect.py tests/unit_tests/ir/test_ifir_converter.py -v`

# Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

# Plan
- [ ] Inspect IFIR dialect + GraphIR->IFIR converter pattern metadata handling.
- [ ] Update IFIR ops/attrs to carry pattern provenance metadata + expression table.
- [ ] Update GraphIR->IFIR conversion to propagate pattern origin attrs + table.
- [ ] Refresh IFIR dialect/converter tests for structured metadata.
- [ ] Run targeted IFIR tests.
- [ ] Open PR and finalize task status.

# Progress log
- 2026-01-19: Initialized scratchpad and set task to in progress.

# Patch summary
- TBD.

# PR URL
- TBD.

# Verification
- TBD.

# Status request (Done / Blocked / In Progress)
- In Progress.

# Blockers / Questions
- None.

# Next steps
- Inspect IFIR dialect + converter metadata flows.
