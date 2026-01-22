# Task summary (DoD + verify)
- DoD: Treat spliced net names as errors in PatternedGraph lowering and add binding tests that allow spliced endpoints only for index or scalar bindings while rejecting spliced broadcast. Ensure diagnostics align with the refactor spec updates.
- Verify: venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py tests/unit_tests/patterns_refactor/test_binding.py -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- docs/specs_refactor/spec_refactor_pattern_service.md
- agents/adr/ADR-0022-no-net-splices.md

# Plan
- Review current lowering and binding rules for splices.
- Add diagnostics for spliced net names in lowering.
- Update binding rules/tests for splice allowances and errors.
- Run targeted tests and record results.

# Progress log
- 2026-01-21: Scratchpad created.
- 2026-01-21: Added splice validation for net names and expanded binding tests.

# Patch summary
- Added splice validation for net name expressions during lowering.
- Added binding tests for spliced endpoint index/scalar cases and broadcast rejection.
- Added lowering diagnostic test for spliced net names.

# PR URL
- (pending)

# Verification
- `venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py tests/unit_tests/patterns_refactor/test_binding.py -v`

# Status request
- In Progress

# Blockers / Questions
- None.

# Next steps
- Inspect current splice handling in lowering and binding modules.
