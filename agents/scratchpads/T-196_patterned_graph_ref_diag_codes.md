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
- 2026-01-22: Added reference diagnostic coverage for qualified/unqualified cases and updated lowering codes.

## Patch summary
- Updated instance reference diagnostics to emit IR-010/IR-011 per qualified/unqualified failures.
- Added tests for missing and ambiguous references across qualified and unqualified cases.

## PR URL
- https://github.com/Jianxun/ASDL/pull/197

## Verification
- `venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py -v`
  - Result: PASS

## Status request
- Ready for review.

## Blockers / Questions
- None yet.

## Next steps
- Await review feedback.
