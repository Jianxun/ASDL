# Task summary (DoD + verify)
- DoD: Enforce backend-name uniqueness per device in NetlistIR verification. Add a new diagnostic code (IR-056) to the catalog and expose a verifier constant. Add a unit test that reports duplicate backend names.
- Verify: venv/bin/pytest tests/unit_tests/emit/test_netlist_ir_verify.py -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect NetlistIR verification and existing diagnostics/constants.
- Add IR-056 diagnostic entry and verifier constant.
- Implement backend-name uniqueness per device rule and unit test.
- Run verify command.

# Progress log
- 2026-01-24 09:10 — Task intake: reviewed DoD and context; understanding: add NetlistIR verifier rule for per-device backend name uniqueness with IR-056 constant + catalog entry + test; next step set task in_progress and create branch.
- 2026-01-24 09:12 — Set T-216 status to in_progress, ran tasks_state lint, created feature branch; next step add failing unit test for duplicate backend names.

# Patch summary

# PR URL

# Verification

# Status request (Done / Blocked / In Progress)

# Blockers / Questions

# Next steps
