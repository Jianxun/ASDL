# Task summary (DoD + verify)
- DoD: Remove origin reconstruction in `src/asdl/lowering/atomized_graph_to_netlist_ir.py` and instead copy Atomized* `pattern_origin` into NetlistIR nets/instances. Delete/retire `_PatternOriginResolver` or reduce it to building the pattern_expression_table from `expression_id` values found in atomized origins. Keep NetlistIR `pattern_expression_table` wiring intact for verifier/rendering. Update/extend emit tests to assert numeric pattern rendering now applies to all atoms (e.g., BUS[25], BUS[24], pin[130], pin[129], sw_row[130], sw_row[129]).
- Verify: `venv/bin/pytest tests/unit_tests/emit -v`

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect atomized->netlist IR lowering and current pattern origin resolver logic.
- Update NetlistIR construction to consume Atomized* pattern_origin and rebuild pattern_expression_table from atomized origins.
- Update/extend emit tests for numeric pattern rendering across atoms.
- Run verify command.

Todo:
- [x] Update lowering tests for atomized-origin data paths.
- [x] Update atomized_graph_to_netlist_ir to copy origins + build pattern table from atomized origins.
- [x] Add emit test for numeric pattern rendering across all atoms.
- [x] Run `venv/bin/pytest tests/unit_tests/emit -v`.

# Progress log

- 2026-01-25 21:06 — Task intake; created scratchpad and set T-227 in_progress; next step review atomized->netlist lowering code.
- 2026-01-25 21:14 — Updated NetlistIR lowering to use atomized pattern origins and adjusted lowering tests; files: src/asdl/lowering/atomized_graph_to_netlist_ir.py, tests/unit_tests/lowering/test_atomized_graph_to_netlist_ir.py; next step add emit test coverage.
- 2026-01-25 21:15 — Committed NetlistIR lowering updates and atomized-origin test updates (3d11199); next step add emit test.
- 2026-01-25 21:15 — Added emit test for numeric pattern rendering across all atoms; file: tests/unit_tests/emit/test_netlist_ir_atomized_origins.py; next step run emit test suite.
- 2026-01-25 21:15 — Committed emit test coverage for numeric pattern rendering (1cebb1b); next step run emit test suite.
- 2026-01-25 21:15 — Ran `venv/bin/pytest tests/unit_tests/emit -v`; result: 25 passed; next step finalize summary and PR.
- 2026-01-25 21:15 — Committed scratchpad progress update (3b384cc); next step prepare PR.
- 2026-01-25 21:15 — Committed scratchpad commit log entry (e57766f); next step open PR.
- 2026-01-25 21:18 — Opened PR https://github.com/Jianxun/ASDL/pull/237; next step update task state to ready_for_review.
- 2026-01-25 21:22 — Review intake; confirmed PR targets main and scratchpad/verify logs present; next step set review_in_progress and inspect diffs.
- 2026-01-25 21:22 — Set T-227 status to review_in_progress; ran lint_tasks_state.py; next step review code/tests against DoD.
- 2026-01-25 21:22 — Completed scope/DoD check and diff review; no blockers found; next step post PR comment and set review_clean.

# Patch summary
- Removed pattern origin reconstruction in AtomizedGraph -> NetlistIR lowering; origins now flow from atomized entities and the pattern table is built from referenced expression ids.
- Updated lowering tests to use AtomizedPatternOrigin instead of patterned ids.
- Added emit test coverage for numeric pattern rendering across all atoms.

# PR URL
- https://github.com/Jianxun/ASDL/pull/237

# Verification
- `venv/bin/pytest tests/unit_tests/emit -v`

# Status request (Done / Blocked / In Progress)
- Done

# Blockers / Questions
- None.

# Next steps
- Await reviewer feedback.
- 2026-01-25 21:19 — Updated tasks_state to ready_for_review (PR 237), ran lint_tasks_state.py, and committed state change (9c7de07); next step push branch.
