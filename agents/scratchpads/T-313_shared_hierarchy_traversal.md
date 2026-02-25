# T-313 Add shared hierarchy traversal utility (v0)

## Task summary (DoD + verify)
- DoD: Implement shared traversal infrastructure in `src/asdl/core/hierarchy.py`
  with a single public API
  `traverse_hierarchy(design, *, include_devices, order="dfs-pre")`.
  The traversal must be deterministic DFS-pre, include centralized module
  selection by `(file_id, symbol)`, and enforce ancestry-based cycle stop
  behavior. Add dedicated unit tests for include/exclude-device policy,
  stable ordering, module-selection fallback, and cycle handling.
- Verify:
  - `./venv/bin/pytest tests/unit_tests/core/test_hierarchy.py -v`

## Read (paths)
- agents/roles/executor.md
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- docs/specs/spec_hierarchy_traversal.md
- src/asdl/views/instance_index.py
- src/asdl/cli/query_runtime.py

## Plan
- Set task state to `in_progress` and lint task-state policy.
- Add hierarchy traversal unit tests first (TDD) for DoD behavior.
- Implement `src/asdl/core/hierarchy.py` and export API from core package.
- Run verify command and capture results.
- Close out task state and PR metadata.

## Milestone notes
- Intake complete; implementation pending.

## Patch summary
- Pending.

## PR URL
- Pending.

## Verification
- Pending.

## Status request (Done / Blocked / In Progress)
- In Progress

## Blockers / Questions
- None.

## Next steps
- Implement and validate T-313 scope.
