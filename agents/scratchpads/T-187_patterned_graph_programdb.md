# Task summary (DoD + verify)
- DoD: Add ProgramDB-backed reference resolution for modules/devices during PatternedGraph lowering so cross-file instance refs are resolved. Include tests for multi-file resolution via import roots.
- Verify: venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect current PatternedGraph lowering + imports resolver integration points.
- Add ProgramDB-backed resolution for module/device refs during lowering.
- Extend tests for multi-file import root resolution in lowering/import pipeline.
- Verify targeted tests.

# Progress log
- 2026-01-xx: Created scratchpad and started task.
- 2026-01-xx: Added import-graph resolution test coverage.
- 2026-01-xx: Implemented import-graph PatternedGraph lowering and qualified ref resolution.

# Patch summary
- Added import-graph PatternedGraph builder and qualified reference resolution in lowering.
- Added multi-file import-root test for PatternedGraph lowering.

# PR URL
- https://github.com/Jianxun/ASDL/pull/195

# Verification
- venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py -v

# Status request (Done / Blocked / In Progress)
- Done

# Blockers / Questions
- None yet.

# Next steps
- Review lowering + import resolver APIs.
- Implement ProgramDB resolution + tests.
