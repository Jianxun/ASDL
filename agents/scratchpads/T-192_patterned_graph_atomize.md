# T-192 Convert PatternedGraph to AtomizedGraph

## Task summary (DoD + verify)
- DoD: Implement a lowering pass in `src/asdl/lowering/patterned_graph_to_atomized.py` that expands PatternedGraph nets/instances/endpoints into a fully atomized core graph using the refactor pattern service and binding rules. Ensure deterministic ordering for atoms and endpoints. Add unit tests covering basic expansion, broadcast binding, and error cases.
- Verify: `venv/bin/pytest tests/unit_tests/core/test_patterned_graph_atomize.py -v`

## Read
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
- [x] Review PatternedGraph and AtomizedGraph specs and current core models.
- [x] Draft atomization tests (basic expansion, broadcast binding, error case).
- [x] Implement PatternedGraph -> AtomizedGraph lowering under `src/asdl/lowering/`.
- [x] Add deterministic ordering + diagnostics for expansion/binding failures.
- [x] Run verify command and record results.

## Progress log
- 2026-01-22: Reviewed specs + core models; implemented atomization lowering + tests.
- 2026-01-23: Added duplicate-atom diagnostics, tightened param expansion handling, and extended tests.

## Patch summary
- Added `build_atomized_graph` lowering with pattern expansion/binding diagnostics.
- Added unit tests for atomization expansion, broadcast binding, and binding errors.
- Added duplicate atom diagnostics for nets/instances and skipped duplicate emissions.
- Stopped applying instance params when expansion errors occur; added tests for duplicates/mismatch.

## PR URL
- https://github.com/Jianxun/ASDL/pull/202

## Verification
- `venv/bin/pytest tests/unit_tests/core/test_patterned_graph_atomize.py -v`

## Status request
- Ready for review.

## Blockers / Questions
- None yet.

## Next steps
- Await review.
