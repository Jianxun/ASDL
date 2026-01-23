# T-200: Populate PatternedGraph devices and ports in lowering

## Task summary (DoD + verify)
- DoD: Update AST -> PatternedGraph lowering to populate device definitions and module ports lists (empty list when absent). Update core PatternedGraph tests to assert ports lists and device definitions.
- Verify: `venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py tests/unit_tests/core/test_patterned_graph.py -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
- Inspect current AST->PatternedGraph lowering for ports/devices and identify missing population.
- Update PatternedGraph tests to assert ports lists and device definitions.
- Update lowering code to populate module ports lists and device definitions.
- Run required tests and record results.

## Todo
- [ ] Add test assertions for device defs and ports lists.
- [ ] Populate device definitions + ports lists in lowering.
- [ ] Run required verification tests.

## Progress log
- 2026-01-23: Scratchpad created; task status pending updates.

## Patch summary
- Pending.

## PR URL
- Pending.

## Verification
- Pending.

## Status request
- In Progress.

## Blockers / Questions
- None yet.

## Next steps
- Inspect lowering paths and existing tests.
