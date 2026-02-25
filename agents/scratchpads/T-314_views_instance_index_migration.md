# T-314 — Migrate views instance index to shared traversal

## Task summary (DoD + verify)
- DoD:
  - Refactor `asdl.views.instance_index.build_instance_index` to consume
    shared traversal with `include_devices=False` and preserve current
    module-only index behavior.
  - Remove duplicated traversal and module selection helpers from views index
    code once migrated.
  - Keep existing view-binding matching semantics/output unchanged and update
    regressions to prove no behavior drift.
- Verify:
  - `./venv/bin/pytest tests/unit_tests/views/test_instance_index.py tests/unit_tests/views/test_view_resolver.py -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `agents/roles/executor.md`

## Plan
- Set `T-314` status to `in_progress` and lint task state.
- Add/adjust tests first for traversal migration invariants.
- Refactor `src/asdl/views/instance_index.py` to use shared traversal.
- Remove duplicate local traversal/module-selection helpers if now unused.
- Run task verify command and record outcomes.
- Close out task state and PR metadata once PR is opened.

## Milestone notes
- Intake complete; implementation not started.
- Migrated `build_instance_index` to `traverse_hierarchy(..., include_devices=False)`.
- Removed local `_select_module` traversal-selection duplication.
- Added regression coverage for module-only behavior when device targets exist.

## Patch summary
- `src/asdl/views/instance_index.py`
  - Replaced local DFS traversal with shared `asdl.core.hierarchy.traverse_hierarchy`.
  - Preserved index entry shape, logical module-name normalization, and root path behavior.
  - Removed duplicate local module-selection helper.
- `tests/unit_tests/views/test_instance_index.py`
  - Added `test_build_instance_index_excludes_device_targets` to lock module-only indexing behavior.

## PR URL
- Pending.

## Verification
- `./venv/bin/pytest tests/unit_tests/views/test_instance_index.py tests/unit_tests/views/test_view_resolver.py -v`
  - Result: 14 passed

## Status request (Done / Blocked / In Progress)
- In Progress

## Blockers / Questions
- None.

## Next steps
- Implement migration with test coverage and no behavior drift.
