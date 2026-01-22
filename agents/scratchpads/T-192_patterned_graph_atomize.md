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
- [ ] Review PatternedGraph and AtomizedGraph specs and current core models.
- [ ] Implement PatternedGraph -> AtomizedGraph lowering under `src/asdl/lowering/`.
- [ ] Add deterministic ordering and diagnostics for expansion/binding failures.
- [ ] Add/extend tests for expansion, broadcast, and error cases.
- [ ] Run verify command and record results.

## Progress log
- 2026-01-XX: Initialized scratchpad.

## Patch summary
- TBD.

## PR URL
- TBD.

## Verification
- Not run.

## Status request
- Not started.

## Blockers / Questions
- None yet.

## Next steps
- Confirm conversion API shape and diagnostic expectations.
