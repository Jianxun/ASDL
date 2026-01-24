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
- 2026-01-24 09:14 — Committed task setup (19901be); files: agents/context/tasks_state.yaml, agents/scratchpads/T-216_netlist_ir_backend_uniqueness.md; next step add failing unit test.
- 2026-01-24 09:18 — Added unit test covering duplicate NetlistIR backend names; files: tests/unit_tests/emit/test_netlist_ir_verify.py; next step commit test.
- 2026-01-24 09:19 — Committed unit test (7c725ac); next step implement verifier rule, add IR-056 diagnostic entry + constant.
- 2026-01-24 09:26 — Implemented backend-name uniqueness verification and IR-056 catalog entry; files: src/asdl/emit/verify_netlist_ir.py, docs/specs/spec_diagnostic_codes.md; next step commit changes.
- 2026-01-24 09:27 — Committed verifier + diagnostics update (04c26c6); next step update scratchpad and run tests.
- 2026-01-24 09:30 — Ran verify command: venv/bin/pytest tests/unit_tests/emit/test_netlist_ir_verify.py -v (pass); next step update scratchpad summary and open PR.
- 2026-01-24 09:35 — Opened PR https://github.com/Jianxun/ASDL/pull/220; updated task status to ready_for_review; next step finalize scratchpad and push updates.

# Patch summary
- Added NetlistIR verifier rule for duplicate backend names with IR-056 constant.
- Documented IR-056 in diagnostic codes catalog.
- Added unit test covering duplicate backend names.

# PR URL
- https://github.com/Jianxun/ASDL/pull/220
# Verification
- venv/bin/pytest tests/unit_tests/emit/test_netlist_ir_verify.py -v

# Status request (Done / Blocked / In Progress)
- Done
# Blockers / Questions
- None
# Next steps
- Await review feedback.
