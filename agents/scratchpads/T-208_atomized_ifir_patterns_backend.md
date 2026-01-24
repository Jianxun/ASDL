# Task summary (DoD + verify)
- DoD: Use registry-backed pattern expression tables and expr-kind mappings to reconstruct IFIR pattern_origin attrs for nets, instances, and devices. Attach backend template metadata for devices and extend happy-path tests to assert pattern origins and backend templates round-trip.
- Verify: venv/bin/pytest tests/unit_tests/lowering/test_atomized_graph_to_ifir.py -v

# Read (paths)
- agents/roles/executor.md
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect AtomizedGraph -> IFIR lowering + tests to understand current pattern/back-end data flow.
- Add pattern_origin reconstruction using registries (expr table + kind mapping) for nets/instances/devices.
- Thread backend template metadata into IFIR devices and assert round-trip in tests.
- Run targeted tests and record results.

# Progress log
- 2026-01-24 00:00 — Task intake: reviewed contract/tasks and created scratchpad; set T-208 in_progress; next step inspect atomized_graph_to_ifir lowering and tests.
- 2026-01-24 00:10 — Added registries field to AtomizedProgramGraph and propagated PatternedGraph registries into atomized build; files: src/asdl/core/atomized_graph.py, src/asdl/lowering/patterned_graph_to_atomized.py; commit 8fb58b1; next step update AtomizedGraph->IFIR lowering + tests for pattern origins/backend templates.
- 2026-01-24 00:24 — Added pattern origin reconstruction, pattern expression table generation, and backend template emission in AtomizedGraph->IFIR; updated happy-path test to assert pattern origins and backend backend templates; files: src/asdl/lowering/atomized_graph_to_ifir.py, tests/unit_tests/lowering/test_atomized_graph_to_ifir.py; commit 8d65177; next step run targeted tests.
- 2026-01-24 00:26 — Ran ./venv/bin/pytest tests/unit_tests/lowering/test_atomized_graph_to_ifir.py -v; all tests passed.

# Patch summary
- Added registry propagation to AtomizedProgramGraph for downstream metadata access.
- Rebuilt IFIR lowering to attach pattern origins, pattern expression tables, and device backend templates.
- Expanded AtomizedGraph->IFIR happy-path test coverage for pattern origins and backend templates.

# PR URL
https://github.com/Jianxun/ASDL/pull/215

# Verification
- ./venv/bin/pytest tests/unit_tests/lowering/test_atomized_graph_to_ifir.py -v

# Status request
Ready for review.

# Blockers / Questions
None.

# Next steps
None.
