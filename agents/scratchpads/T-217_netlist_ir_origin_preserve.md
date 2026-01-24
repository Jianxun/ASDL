# Task summary (DoD + verify)
- DoD: Update AtomizedGraph -> NetlistIR lowering to preserve pattern_origin metadata even when pattern expression kinds are missing or mismatched, so NetlistIR verification can surface invalid origins. Add a lowering unit test that demonstrates pattern_origin survives a kind mismatch.
- Verify: venv/bin/pytest tests/unit_tests/lowering/test_atomized_graph_to_netlist_ir.py -v

# Read (paths)
- agents/roles/executor.md
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
1. Inspect AtomizedGraph -> NetlistIR lowering for pattern_origin handling and current mismatch behavior.
2. Add/adjust unit test that exercises kind mismatch and asserts pattern_origin preservation.
3. Implement lowering change to preserve pattern_origin on mismatched/missing kinds.
4. Run targeted unit test and record results.

# Todo
- [x] Add lowering test for kind mismatch preserving pattern_origin.
- [x] Update pattern origin resolver to ignore kind mismatches/missing kinds.
- [x] Run lowering unit tests.

# Progress log
- 2026-01-24 00:00 — Task intake and context review; created scratchpad; set T-217 to in_progress; next step inspect lowering implementation.
- 2026-01-24 00:12 — Added lowering test for pattern_origin kind mismatch preservation; updated `tests/unit_tests/lowering/test_atomized_graph_to_netlist_ir.py`; next step adjust lowering to keep origins.
- 2026-01-24 00:22 — Updated NetlistIR lowering pattern origin resolver to keep origins on kind mismatches/missing kinds; updated `src/asdl/lowering/atomized_graph_to_netlist_ir.py`; next step run tests.
- 2026-01-24 00:30 — Ran lowering unit tests (2 passed) for NetlistIR lowering; updated scratchpad verification; next step prep closeout.

# Patch summary

- Preserved pattern_origin resolution regardless of pattern expr kind mismatches in `src/asdl/lowering/atomized_graph_to_netlist_ir.py`.
- Added lowering test coverage for kind mismatch origin preservation in `tests/unit_tests/lowering/test_atomized_graph_to_netlist_ir.py`.

# PR URL

# Verification
 - venv/bin/pytest tests/unit_tests/lowering/test_atomized_graph_to_netlist_ir.py -v
   - Result: PASS

# Status request (Done / Blocked / In Progress)

# Blockers / Questions

# Next steps
