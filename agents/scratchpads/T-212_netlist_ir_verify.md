# Task summary (DoD + verify)
- DoD: Port IFIR verification rules to NetlistIR as stateless validators (literal names, unique nets/instances, conn targets, ports list, and pattern-origin table consistency). Add diagnostics entries for NetlistIR validation and unit tests for at least one failure per rule group.
- Verify: `venv/bin/pytest tests/unit_tests/emit/test_netlist_ir_verify.py -v`

# Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

# Plan
- Review IFIR verification rules and NetlistIR model.
- Implement NetlistIR stateless validators with diagnostic codes.
- Add diagnostics catalog entries.
- Add unit tests for each rule group.
- Run verify command.

# Progress log
- 2026-01-24 00:00 — Task intake, read context files, created scratchpad, set T-212 to in_progress, ran lint_tasks_state, created feature branch feature/T-212-netlist-ir-verify; next step review IFIR verification rules and NetlistIR model.
- 2026-01-24 00:10 — Added NetlistIR verification unit tests covering literal names, duplicate nets/instances, conn targets, port list, and pattern origin mismatch; committed 3f49154 (Add NetlistIR verification tests); next step implement NetlistIR verifier and diagnostic catalog updates.
- 2026-01-24 00:20 — Implemented NetlistIR stateless verifier with diagnostics + updated diagnostic codes spec; committed 0c84384 (Add NetlistIR verification helpers); next step run unit tests.
- 2026-01-24 00:25 — Ran `venv/bin/pytest tests/unit_tests/emit/test_netlist_ir_verify.py -v` (pass); next step update scratchpad summary and prep PR.
- 2026-01-24 00:35 — Opened PR https://github.com/Jianxun/ASDL/pull/219, set T-212 to ready_for_review, ran lint_tasks_state; next step commit scratchpad/state updates.
- 2026-01-24 00:40 — Committed scratchpad/status updates (5c723a5) and pushed branch; next step final response.

# Patch summary
- Added NetlistIR stateless verification helpers with diagnostic codes.
- Documented new NetlistIR diagnostic codes in the catalog.
- Added unit tests for each NetlistIR verification rule group.

# PR URL
- https://github.com/Jianxun/ASDL/pull/219

# Verification
- `venv/bin/pytest tests/unit_tests/emit/test_netlist_ir_verify.py -v`

# Status request
- Ready for review.

# Blockers / Questions
- None.

# Next steps
- Await review feedback.
