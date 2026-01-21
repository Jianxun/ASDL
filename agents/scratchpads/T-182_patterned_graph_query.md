# Task summary (DoD + verify)
- Implement GraphIndex and DesignQuery helpers (net/instance lookup + adjacency lists) derived from PatternedGraph.
- Add tests for deterministic lookup and adjacency construction.
- Verify: `venv/bin/pytest tests/unit_tests/core/test_query.py -v`

# Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `docs/specs_refactor/spec_refactor_patterned_graph.md`

# Plan
- Write tests for index/query construction and determinism.
- Implement GraphIndex + DesignQuery helpers with docstrings.
- Export new helpers in core __init__.
- Run verify command and record results.

# Todo list
- [x] Draft query/index tests for deterministic lookup + adjacency.
- [ ] Implement GraphIndex + DesignQuery helpers.
- [ ] Update core exports.
- [ ] Run verification.

# Progress log
- 2026-01-20: Created scratchpad and gathered requirements.
- 2026-01-20: Added failing query/index tests (TDD baseline).

# Patch summary

# PR URL

# Verification

# Status request (Done / Blocked / In Progress)

# Blockers / Questions

# Next steps
