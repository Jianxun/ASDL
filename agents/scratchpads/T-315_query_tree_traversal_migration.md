# T-315 — Migrate query tree traversal to shared utility

## Task summary (DoD + verify)
- DoD:
  - Refactor query-tree payload construction to consume shared traversal with
    `include_devices=True`, preserving current compact/verbose JSON payloads
    and default ASCII tree text output exactly.
  - Remove duplicate traversal helpers from query runtime once migrated.
  - Retain stage-aware behavior and deterministic ordering with no output
    contract changes.
- Verify:
  - `./venv/bin/pytest tests/unit_tests/cli/test_query_tree.py tests/unit_tests/cli/test_query_cli_runtime.py -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `agents/roles/executor.md`

## Plan
- Set `T-315` status to `in_progress` and lint task state.
- Add/adjust query tree regression tests for shared traversal migration behavior.
- Refactor `src/asdl/cli/query_runtime.py` to use shared hierarchy traversal with
  `include_devices=True` while preserving output contracts.
- Remove duplicate local traversal/module-selection helpers from query runtime.
- Run task verify command and record outcomes.
- Close out task state + PR metadata once PR is opened.

## Milestone notes
- Intake complete; implementation not started.
- Migrated query tree traversal to shared hierarchy utility with
  `include_devices=True`.
- Removed duplicate local traversal and module-selection helpers from
  query runtime.

## Patch summary
- `src/asdl/cli/query_runtime.py`
  - Replaced local query-tree DFS traversal with
    `asdl.core.hierarchy.traverse_hierarchy(..., include_devices=True)`.
  - Removed duplicate `_TreeInstanceEntry`, `_collect_tree_instances`, and
    `_select_module` helpers after migration.
  - Preserved stage-aware resolved/emitted ref mapping and output assembly.

## PR URL
- Pending.

## Verification
- `./venv/bin/pytest tests/unit_tests/cli/test_query_tree.py tests/unit_tests/cli/test_query_cli_runtime.py -v`
  - Result: 10 passed

## Status request (Done / Blocked / In Progress)
- In Progress

## Blockers / Questions
- None.

## Next steps
- Implement migration with no payload/output behavior drift.
