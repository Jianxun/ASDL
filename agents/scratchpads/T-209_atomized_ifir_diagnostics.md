# Task summary (DoD + verify)
- DoD: Emit diagnostics for missing/invalid registry data (missing pattern table entries, missing expr kind, missing backend template) and unresolved refs in AtomizedGraph -> IFIR lowering. Add unit tests covering at least one missing-registry and one unresolved reference failure.
- Verify: venv/bin/pytest tests/unit_tests/lowering/test_atomized_graph_to_ifir.py -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Review AtomizedGraph -> IFIR lowering and existing diagnostics codes/helpers.
- Add diagnostics for missing registry data (pattern table, expr kind, backend template) and unresolved refs.
- Extend unit tests for missing registry + unresolved ref failures.
- Run targeted pytest and update task status/PR metadata.

# Progress log
- 2026-01-23 21:23 — Task intake: need diagnostics for missing registry data + unresolved refs in AtomizedGraph -> IFIR lowering, with new unit tests; next step review lowering code and diagnostics patterns.
- 2026-01-23 21:23 — Added unit tests for missing pattern registry data and unresolved reference, plus adjusted missing endpoint test to include backend templates; files: tests/unit_tests/lowering/test_atomized_graph_to_ifir.py; next step implement diagnostics in lowering.
- 2026-01-23 21:23 — Implemented diagnostics for missing pattern registry data, expr kinds, backend templates; updated IFIR lowering to propagate errors; files: src/asdl/lowering/atomized_graph_to_ifir.py; next step run unit tests.
- 2026-01-23 21:24 — Ran venv/bin/pytest tests/unit_tests/lowering/test_atomized_graph_to_ifir.py -v; all tests passed.
- 2026-01-23 21:24 — Commit 47e24cf: add missing registry/back-end template diagnostics and new unit tests; files: src/asdl/lowering/atomized_graph_to_ifir.py, tests/unit_tests/lowering/test_atomized_graph_to_ifir.py, agents/scratchpads/T-209_atomized_ifir_diagnostics.md, agents/context/tasks_state.yaml.
- 2026-01-23 21:25 — Opened PR https://github.com/Jianxun/ASDL/pull/216 for T-209 changes.
- 2026-01-23 21:25 — Updated tasks_state.yaml to ready_for_review with PR 216.

# Patch summary
- Add missing-registry diagnostics (pattern expression, expr kind, backend template) in AtomizedGraph -> IFIR lowering.
- Record invalid pattern origin data as lowering errors instead of silent drops.
- Add unit tests for missing pattern registry data and unresolved references; update missing-endpoint test to include backend templates.

# PR URL
- https://github.com/Jianxun/ASDL/pull/216

# Verification
- venv/bin/pytest tests/unit_tests/lowering/test_atomized_graph_to_ifir.py -v (pass)

# Status request (Done / Blocked / In Progress)
- Ready for review

# Blockers / Questions
- None.

# Next steps
- Await review feedback.
- 2026-01-23 21:25 — Commit 40f4235: record PR URL and set task status ready_for_review; files: agents/scratchpads/T-209_atomized_ifir_diagnostics.md, agents/context/tasks_state.yaml.
