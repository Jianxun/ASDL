# T-122: Relocate GraphIR rebundling helpers to AST projection

## Task summary (DoD + verify)
- DoD: Move `rebundle_bundle`/`rebundle_pattern_expr` out of `src/asdl/ir/graphir/patterns.py` into the GraphIR->AST projection path (converter or pass) so rebundling is treated as projection logic, not GraphIR core. Remove wrapper exports from pattern passes, keep any GraphIR-side metadata decode helpers as needed, and update call sites/tests without changing behavior.
- Verify: `venv/bin/pytest tests/unit_tests/ir/test_pattern_atomization.py -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
- [ ] Inspect current GraphIR rebundling helpers and call sites.
- [ ] Move rebundling helpers into GraphIR->AST projection path and update imports.
- [ ] Update pattern pass exports and call sites/tests to use the new location.
- [ ] Run verification tests.

## Progress log
- 2026-02-06: Initialized scratchpad and started task.

## Patch summary
- TBD.

## PR URL
- TBD.

## Verification
- TBD.

## Status request
- In Progress.

## Blockers / Questions
- None yet.

## Next steps
- Inspect current GraphIR rebundling helper usage and decide new home in projection path.
