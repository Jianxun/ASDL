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
- [x] Inspect current GraphIR rebundling helpers and call sites.
- [x] Move rebundling helpers into GraphIR->AST projection path and update imports.
- [x] Update pattern pass exports and call sites/tests to use the new location.
- [x] Run verification tests.

## Progress log
- 2026-02-06: Initialized scratchpad and started task.
- 2026-02-06: Moved rebundling helpers into GraphIR->AST projection module and removed pass wrappers.
- 2026-02-06: Opened PR #133.

## Patch summary
- Added GraphIR->AST projection helper module for rebundling GraphIR pattern bundles.
- Trimmed GraphIR pattern metadata helpers to remove rebundling logic.
- Removed rebundling wrapper exports from pattern passes and updated tests to import from projection helpers.

## PR URL
- https://github.com/Jianxun/ASDL/pull/133

## Verification
- `venv/bin/pytest tests/unit_tests/ir/test_pattern_atomization.py -v`

## Status request
- Done.

## Blockers / Questions
- None yet.

## Next steps
- Inspect current GraphIR rebundling helper usage and decide new home in projection path.
