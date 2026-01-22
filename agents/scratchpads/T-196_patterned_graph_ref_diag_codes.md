# T-196 Use IR-010/IR-011 for PatternedGraph reference diagnostics

## Task summary (DoD + verify)
- DoD: Update PatternedGraph instance reference diagnostics to emit IR-010 for qualified `ns.symbol` failures and IR-011 for unqualified/ambiguous references while keeping IR-001 for malformed instance expressions. Add tests covering unresolved qualified namespaces/symbols and ambiguous or missing unqualified references.
- Verify: `venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py -v`

## Read
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
- [ ] Inspect current reference resolution paths and diagnostic helpers.
- [ ] Update diagnostic codes and messages per spec.
- [ ] Add tests for qualified/unqualified failure cases.
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
- Review lowering diagnostics and reference resolution behavior.
