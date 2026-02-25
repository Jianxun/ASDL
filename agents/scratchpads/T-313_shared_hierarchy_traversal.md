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
- Added dedicated hierarchy traversal unit tests first (TDD), confirmed initial
  failure because `asdl.core.hierarchy` was missing.
- Implemented shared traversal API with deterministic DFS-pre ordering,
  ancestry-based cycle stop, and centralized symbol selection fallback.
- Ran task verify command; hierarchy unit tests pass.

## Patch summary
- `src/asdl/core/hierarchy.py`
  - Added `HierarchyEntry` dataclass and `traverse_hierarchy(...)` public API.
  - Implemented deterministic DFS-pre traversal rooted at resolved top module.
  - Added centralized symbol selection with exact `(file_id, symbol)` lookup,
    unique-name fallback, and deterministic last-candidate fallback.
  - Implemented include-device policy and ancestry-based module cycle stop.
- `src/asdl/core/__init__.py`
  - Exported `HierarchyEntry` and `traverse_hierarchy` from `asdl.core`.
- `tests/unit_tests/core/test_hierarchy.py`
  - Added unit coverage for include/exclude-device policy, DFS-pre ordering,
    module-selection fallback semantics, and cycle handling.

## PR URL
- Pending.

## Verification
- `./venv/bin/pytest tests/unit_tests/core/test_hierarchy.py -v`
  - Result: 4 passed.

## Status request (Done / Blocked / In Progress)
- In Progress

## Blockers / Questions
- None.

## Next steps
- Push branch, open PR, and transition task state to `ready_for_review`.
