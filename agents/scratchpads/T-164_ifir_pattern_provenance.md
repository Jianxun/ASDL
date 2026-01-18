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
- [x] Inspect IFIR dialect + GraphIR->IFIR converter pattern metadata handling.
- [x] Update IFIR ops/attrs to carry pattern provenance metadata + expression table.
- [x] Update GraphIR->IFIR conversion to propagate pattern origin attrs + table.
- [x] Refresh IFIR dialect/converter tests for structured metadata.
- [x] Run targeted IFIR tests.
- [x] Open PR and finalize task status.

# Progress log
- 2026-01-19: Initialized scratchpad and set task to in progress.
- 2026-01-19: Added structured pattern provenance attributes to IFIR ops and module metadata.
- 2026-01-19: Updated GraphIR->IFIR conversion to pass through pattern provenance metadata.
- 2026-01-19: Refreshed IFIR/netlist tests for structured pattern metadata.
- 2026-01-19: Ran IFIR unit tests.
- 2026-01-19: Opened PR #166.
- 2026-01-19: Fixed e2e pipeline test expectations for structured pattern origins.
- 2026-01-19: Updated IFIR dialect context loading to avoid duplicate pattern attr registration.
- 2026-01-19: Ran targeted e2e pipeline test.

# Patch summary
- Added IFIR pattern provenance attributes and module expression table metadata.
- Updated GraphIR->IFIR conversion to preserve structured pattern origins.
- Refreshed IFIR dialect/converter and netlist tests for new metadata.
- Fixed pipeline e2e pattern origin assertions to resolve expressions via the table.
- Loaded GraphIR dialect where needed to register shared pattern origin attrs.

# PR URL
- https://github.com/Jianxun/ASDL/pull/166

# Verification
- `venv/bin/pytest tests/unit_tests/ir/test_ifir_dialect.py tests/unit_tests/ir/test_ifir_converter.py -v`
- `venv/bin/pytest tests/unit_tests/e2e/test_pipeline_mvp.py::test_pipeline_atomizes_patterns_before_emission -v`

# Status request (Done / Blocked / In Progress)
- Done

# Blockers / Questions
- None.

# Next steps
- Await review feedback.
