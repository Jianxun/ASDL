# Task summary (DoD + verify)
- DoD: Add a dataclass-based NetlistIR model representing design/module/net/instance/device/backend nodes with literal names and optional pattern provenance metadata. Use `ports` for module port ordering (consistent with other refactor IRs) and include docstrings. Add a unit test covering construction and ordering invariants.
- Verify: `venv/bin/pytest tests/unit_tests/emit/test_netlist_ir_model.py -v`

# Read (paths)
- agents/roles/executor.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/project_status.md
- docs/specs/spec_netlist_ir.md
- src/asdl/core/graph.py
- src/asdl/core/atomized_graph.py
- src/asdl/ir/patterns/expr_table.py
- src/asdl/ir/patterns/origin.py

# Plan
- [x] Write NetlistIR dataclasses per spec (design/module/net/instance/conn/device/backend + pattern types).
- [x] Add unit test covering construction + ordering invariants.
- [x] Run focused pytest for new test.
- [x] Update scratchpad, tasks_state, and prepare PR.

# Progress log
- 2026-01-23 22:37 — Task intake, read executor workflow/specs/core graph models; created scratchpad and set T-210 in_progress; next step define test/model.
- 2026-01-23 22:39 — Added NetlistIR model test coverage draft; created `tests/unit_tests/emit/test_netlist_ir_model.py`; next step implement NetlistIR dataclasses.
- 2026-01-23 22:39 — Implemented NetlistIR dataclasses per spec in `src/asdl/emit/netlist_ir.py`; next step run pytest and update scratchpad/checklist.
- 2026-01-23 22:39 — Ran `./venv/bin/pytest tests/unit_tests/emit/test_netlist_ir_model.py -v`; 1 passed; next step commit changes.
- 2026-01-23 22:40 — Committed NetlistIR model + tests (db1bee9); next step finalize scratchpad and PR.
- 2026-01-23 22:40 — Normalized optional defaults in NetlistIR dataclasses; reran pytest `tests/unit_tests/emit/test_netlist_ir_model.py`; passed; next step commit updates.
- 2026-01-23 22:41 — Committed NetlistIR default refinements (f3a0c63); next step finalize scratchpad + PR.

# Patch summary
- Added NetlistIR dataclass model and pattern provenance types.
- Added unit test covering construction and ordering invariants.

# PR URL
- https://github.com/Jianxun/ASDL/pull/217

# Verification
- `./venv/bin/pytest tests/unit_tests/emit/test_netlist_ir_model.py -v`

# Status request (Done / Blocked / In Progress)
- Ready for review

# Blockers / Questions
- None.

# Next steps
- Await review feedback.
- 2026-01-23 22:42 — Opened PR https://github.com/Jianxun/ASDL/pull/217; next step update tasks_state to ready_for_review.
- 2026-01-23 22:42 — Set T-210 to ready_for_review in tasks_state and ran lint_tasks_state.py; next step commit/push updates.
- 2026-01-23 22:43 — Committed scratchpad/status updates (ad4c9f7); next step push branch updates.
