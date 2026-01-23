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
- [x] Add test assertions for device defs and ports lists.
- [x] Populate device definitions + ports lists in lowering.
- [x] Run required verification tests.

## Progress log
- 2026-01-23: Scratchpad created; task status set to in progress.
- 2026-01-23: Updated PatternedGraph tests to assert device defs and ports lists.
- 2026-01-23: Lowering now registers device definitions and fills device ID maps from builder.
- 2026-01-23: Fixed port_order aliasing to avoid InitVar/property conflicts in core graphs.
- 2026-01-23: Verified PatternedGraph tests.

## Patch summary
- Added device definition lowering with ports/params/vars capture.
- Added device/ports assertions in PatternedGraph tests.
- Adjusted ModuleGraph/AtomizedModuleGraph port_order aliasing to avoid InitVar default conflicts.

## PR URL
- https://github.com/Jianxun/ASDL/pull/205

## Verification
- `venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py tests/unit_tests/core/test_patterned_graph.py -v`

## Status request
- Ready for review.

## Blockers / Questions
- None yet.

## Next steps
- Run required verification tests.
